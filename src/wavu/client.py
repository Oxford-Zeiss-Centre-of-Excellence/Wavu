"""A Python client for ``wavu-worker``: what the Fiji Groovy client does, for Python hosts.

napari-wavu, notebooks and other Python front ends use this to start a worker
in a script folder's own pixi environment, or to attach to one that is already
running, and to run jobs on it. Standard library plus numpy/tifffile (already
wavu dependencies); the HTTP protocol is in docs/protocol.md.

    from wavu.client import Worker

    with Worker.start("path/to/script-folder", on_log=print) as w:
        print(w.scripts())
        result = w.run("script", params={"sigma": 2.0}, inputs={"image": arr}, on_log=print)
        blurred = result.outputs["blurred"].value

The worker is started with a pipe on its stdin and exits when that pipe
closes, so it never outlives the host process, as in Fiji.
"""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

import numpy as np

from wavu.codec import INLINE_LIMIT, decode_array, encode_array, read_table
from wavu.types import RoiSet

DEFAULT_HANDSHAKE = Path.home() / ".wavu" / "worker.json"
Log = Callable[[str], None]
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# Variables that describe the *host's* environment. A child `pixi run` for a
# different manifest must not inherit them, or it may activate the wrong env.
_HOST_ENV_PREFIXES = ("PIXI_", "CONDA_", "VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH", "INIT_CWD")


class WorkerError(RuntimeError):
    """The worker could not start, refused a request, or a job failed."""


class JobCancelled(WorkerError):
    """The job was cancelled before it finished."""


# --------------------------------------------------------------------- pixi --


def find_pixi() -> str | None:
    """pixi from $WAVU_PIXI, $PIXI_EXE (set inside `pixi run`), ~/.wavu/bin, PATH, ~/.pixi/bin."""
    name = "pixi.exe" if os.name == "nt" else "pixi"
    candidates = [os.environ.get("WAVU_PIXI"), os.environ.get("PIXI_EXE"), str(Path.home() / ".wavu" / "bin" / name)]
    candidates.append(shutil.which("pixi"))
    candidates.append(str(Path.home() / ".pixi" / "bin" / name))
    for c in candidates:
        if c and Path(c).is_file():
            return c
    return None


def worker_command(script_dir: Path, pixi: str | None = None, frozen: bool = False, debugpy: int | None = None) -> list[str]:
    """The `pixi run ... wavu-worker` command that serves ``script_dir`` in its own environment."""
    manifest = script_dir / "pixi.toml"
    if not manifest.is_file():
        raise WorkerError(f"{script_dir} has no pixi.toml, so it is not a Wavu script folder (see templates/wavu-script)")
    pixi = pixi or find_pixi()
    if pixi is None:
        raise WorkerError("pixi was not found. Install it from https://pixi.sh, or set WAVU_PIXI to its path.")
    cmd = [pixi, "run", "--manifest-path", str(manifest)]
    if frozen:
        cmd.append("--frozen")
    cmd += ["wavu-worker", "--script-dir", str(script_dir)]
    if debugpy:
        cmd += ["--debugpy", str(debugpy), "--debugpy-wait"]
    return cmd


def child_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(_HOST_ENV_PREFIXES)}
    env.update(NO_COLOR="1", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    return env


# ------------------------------------------------------------------ results --


@dataclass
class Output:
    """One output of a finished job. ``value`` is loaded for you: an array, a table, a RoiSet, a Path or a plain value."""

    name: str
    kind: str  # image | table | rois | file | value
    value: Any
    meta: dict[str, Any] = field(default_factory=dict)
    spec: dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    outputs: dict[str, Output]
    logs: list[str] = field(default_factory=list)


def load_output(name: str, spec: dict[str, Any]) -> Output:
    kind = spec.get("kind", "value")
    meta = dict(spec.get("meta") or {})
    if kind == "image":
        if "data" in spec:
            value: Any = decode_array(spec)
        else:
            import tifffile

            value = tifffile.imread(spec["path"])
    elif kind == "table":
        value = read_table(Path(spec["path"]))
    elif kind == "rois":
        value = RoiSet(spec["path"])
    elif kind == "file":
        value = Path(spec["path"])
    else:
        value = spec.get("value")
    return Output(name, kind, value, meta, spec)


# ------------------------------------------------------------------- worker --


class Worker:
    """A connection to one ``wavu-worker``; owns the process if it started it."""

    def __init__(self, host: str, port: int, token: str, *, version: str | None = None,
                 script_dir: str | None = None, process: subprocess.Popen | None = None,
                 tmp_dir: Path | None = None):
        self.host, self.port, self.token = host, int(port), token
        self.version, self.script_dir, self.process = version, script_dir, process
        self.base = f"http://{host}:{self.port}"
        self._tmp = Path(tmp_dir) if tmp_dir else Path(tempfile.gettempdir()) / "wavu-inputs"
        self._made: list[Path] = []  # temporary input files, removed after each run()

    # -- lifecycle ---------------------------------------------------------
    @classmethod
    def start(cls, script_dir: str | os.PathLike, *, command: Sequence[str] | None = None,
              pixi: str | None = None, frozen: bool = False, debugpy: int | None = None,
              on_log: Log | None = None, timeout: float | None = None,
              cancel: threading.Event | None = None) -> "Worker":
        """Start a worker for ``script_dir`` and wait for its handshake.

        By default this is ``pixi run --manifest-path <dir>/pixi.toml wavu-worker``,
        so the script runs in that folder's own environment; the first start
        installs it, which can take minutes (pixi's progress goes to ``on_log``).
        Pass ``command`` to start the worker some other way (e.g. in tests).
        """
        script_dir = Path(script_dir).resolve()
        log = on_log or (lambda _m: None)
        cmd = list(command) if command is not None else worker_command(script_dir, pixi, frozen, debugpy)
        log("Starting worker: " + " ".join(cmd))
        if command is None:
            log("(the first start installs the script's environment; this can take a few minutes)")
        proc = subprocess.Popen(cmd, cwd=script_dir, env=child_env(), stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lines: queue.Queue[str | None] = queue.Queue()
        tail: list[str] = []

        def pump_stdout() -> None:
            for raw in proc.stdout:  # type: ignore[union-attr]
                lines.put(raw.decode("utf-8", "replace"))
            lines.put(None)

        def pump_stderr() -> None:
            for raw in proc.stderr:  # type: ignore[union-attr]
                text = _ANSI.sub("", raw.decode("utf-8", "replace")).strip()
                if text:
                    tail[:] = (tail + [text])[-40:]
                    log(text)

        threading.Thread(target=pump_stdout, name="wavu-stdout", daemon=True).start()
        threading.Thread(target=pump_stderr, name="wavu-stderr", daemon=True).start()
        t0 = time.monotonic()
        hello = None
        while hello is None:
            if cancel is not None and cancel.is_set():
                proc.kill()
                raise JobCancelled("cancelled while starting the worker")
            if timeout is not None and time.monotonic() - t0 > timeout:
                proc.kill()
                raise WorkerError(f"the worker did not start within {timeout:.0f} s")
            try:
                line = lines.get(timeout=0.25)
            except queue.Empty:
                continue
            if line is None:
                proc.wait(5)
                raise WorkerError(f"the worker exited (code {proc.returncode}) before starting:\n" + "\n".join(tail))
            try:
                obj = json.loads(line)
            except ValueError:
                obj = None
            if isinstance(obj, dict) and obj.get("port") and obj.get("token"):
                hello = obj
            elif line.strip():
                log(line.strip())
        # Keep draining stdout so a chatty process can never block on a full pipe.
        threading.Thread(target=lambda: [None for _ in iter(lambda: lines.get(), None)], daemon=True).start()
        w = cls("127.0.0.1", hello["port"], hello["token"], version=hello.get("wavu"),
                script_dir=str(script_dir), process=proc)
        log(f"Worker ready (wavu {w.version}, port {w.port})")
        return w

    @classmethod
    def connect(cls, handshake: str | os.PathLike = DEFAULT_HANDSHAKE, host: str | None = None) -> "Worker":
        """Attach to a worker started elsewhere (``pixi run worker``) through its handshake file."""
        path = Path(handshake).expanduser()
        if not path.is_file():
            raise WorkerError(f"no handshake file at {path}; start the worker with `pixi run worker` first")
        info = json.loads(path.read_text(encoding="utf-8"))
        h = host or info.get("host") or "127.0.0.1"
        if h == "0.0.0.0":
            h = "127.0.0.1"
        w = cls(h, info["port"], info["token"], version=info.get("wavu"), script_dir=info.get("script_dir"))
        if not w.alive():
            raise WorkerError(f"the worker at {h}:{info['port']} is not answering (stale {path}?)")
        return w

    def alive(self) -> bool:
        if self.process is not None and self.process.poll() is not None:
            return False
        try:
            return bool(self._call("GET", "/health", timeout=3).get("ok"))
        except (WorkerError, OSError):
            return False

    def stop(self) -> None:
        """Shut the worker down. A worker this client started is also waited for (and killed if stuck)."""
        try:
            self._call("POST", "/shutdown", {}, timeout=5)
        except (WorkerError, OSError):
            pass
        p = self.process
        if p is not None:
            try:
                p.stdin.close()  # type: ignore[union-attr]
            except OSError:
                pass
            try:
                p.wait(5)
            except subprocess.TimeoutExpired:
                p.kill()

    def __enter__(self) -> "Worker":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.stop()

    # -- HTTP --------------------------------------------------------------
    def _request(self, method: str, path: str, body: Any = None) -> urllib.request.Request:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        return req

    def _call(self, method: str, path: str, body: Any = None, timeout: float = 60) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(self._request(method, path, body), timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode("utf-8")).get("error", e.reason)
            except ValueError:
                msg = e.reason
            raise WorkerError(f"{method} {path}: {msg}") from None

    def health(self) -> dict[str, Any]:
        return self._call("GET", "/health")

    def scripts(self) -> dict[str, Any]:
        """``{"scripts": {name: {"name", "doc", "params"}}, "errors": {name: message}}``."""
        return self._call("GET", "/scripts")

    # -- jobs --------------------------------------------------------------
    def encode_inputs(self, inputs: dict[str, Any], meta: dict[str, dict] | None = None,
                      inline_limit: int = INLINE_LIMIT) -> dict[str, Any]:
        """Arrays travel inline when small (<= 3-D), otherwise through a temporary TIFF; paths pass through."""
        out: dict[str, Any] = {}
        meta = meta or {}
        for name, value in inputs.items():
            m = dict(meta.get(name) or {})
            if isinstance(value, (str, os.PathLike)):
                out[name] = {"path": str(value), "meta": m}
                continue
            a = np.ascontiguousarray(value)
            if a.nbytes <= inline_limit and a.ndim <= 3:
                out[name] = encode_array(a, m)
            else:
                import tifffile

                self._tmp.mkdir(parents=True, exist_ok=True)
                path = self._tmp / f"{uuid.uuid4().hex}-{name}.tif"
                tifffile.imwrite(path, a, photometric="minisblack")
                self._made.append(path)
                out[name] = {"path": str(path), "meta": m}
        return out

    def submit(self, script: str, params: dict[str, Any] | None = None, inputs: dict[str, Any] | None = None,
               meta: dict[str, dict] | None = None) -> str:
        body = {"script": script, "params": params or {}, "inputs": self.encode_inputs(inputs or {}, meta)}
        return self._call("POST", "/run", body)["job"]

    def events(self, job: str, since: int = 0) -> Iterator[tuple[str, dict[str, Any]]]:
        """Yield ``(kind, data)`` from the job's event stream until its terminal event."""
        with urllib.request.urlopen(self._request("GET", f"/jobs/{job}/events?since={since}"), timeout=None) as r:
            kind = None
            for raw in r:
                line = raw.decode("utf-8").rstrip("\r\n")
                if line.startswith("event: "):
                    kind = line[7:]
                elif line.startswith("data: ") and kind:
                    yield kind, json.loads(line[6:])

    def cancel(self, job: str) -> None:
        self._call("POST", f"/jobs/{job}/cancel", {})

    def result(self, job: str) -> dict[str, Any]:
        return self._call("GET", f"/jobs/{job}/result")

    def run(self, script: str, params: dict[str, Any] | None = None, inputs: dict[str, Any] | None = None, *,
            meta: dict[str, dict] | None = None, on_log: Log | None = None,
            on_progress: Callable[[float], None] | None = None,
            cancel: threading.Event | None = None) -> Result:
        """Run one job to completion and return its loaded outputs.

        ``cancel`` is checked while the job runs; setting it asks the script to
        stop (cancelling is cooperative: the script must check ``ctx.cancelled()``).
        Raises ``JobCancelled`` or ``WorkerError`` (with the script's traceback).
        """
        job = self.submit(script, params, inputs, meta)
        logs: list[str] = []
        if cancel is not None:
            def watch() -> None:
                while not cancel.wait(0.2):
                    if done.is_set():
                        return
                try:
                    self.cancel(job)
                except (WorkerError, OSError):
                    pass

            done = threading.Event()
            threading.Thread(target=watch, daemon=True).start()
        try:
            for kind, data in self.events(job):
                if kind == "log":
                    logs.append(data.get("message", ""))
                    if on_log:
                        on_log(data.get("message", ""))
                elif kind == "progress" and on_progress:
                    on_progress(float(data.get("value", 0.0)))
                elif kind in ("done", "error", "cancelled"):
                    break
        finally:
            if cancel is not None:
                done.set()
            while self._made:
                self._made.pop().unlink(missing_ok=True)
        res = self.result(job)
        status = res.get("status")
        if status == "cancelled":
            raise JobCancelled(f"{script}: cancelled")
        if status == "error":
            err = res.get("error") or {}
            raise WorkerError(f"{script} failed: {err.get('message', err)}\n{err.get('traceback', '')}".rstrip())
        outputs = {n: load_output(n, s) for n, s in (res.get("outputs") or {}).items()}
        return Result(outputs, logs)
