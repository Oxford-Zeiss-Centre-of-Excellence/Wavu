"""``wavu-worker``: serve one script folder over a tiny authenticated HTTP/JSON API.

Standard library only (http.server + json + threading) -- see docs/decisions.md.

Protocol (all requests need ``Authorization: Bearer <token>``):

    GET  /health                 -> {"ok": true, "wavu": version, "scripts": n}
    GET  /scripts                -> {"scripts": {name: schema}, "errors": {name: msg}}
    POST /run                    {script, params, inputs, inline_limit?} -> {"job": id}
    GET  /jobs/<id>/events       text/event-stream: log, progress, then done|error|cancelled
    POST /jobs/<id>/cancel       -> {"ok": true}
    GET  /jobs/<id>/result       -> {"status", "outputs"?, "error"?}  (409 while running)
    POST /shutdown               -> {"ok": true}, then the worker exits

On start it prints one JSON line to stdout: {"wavu": version, "port": N, "token": "..."}.
It exits when stdin closes (the parent died) unless --detached.
"""

from __future__ import annotations

import argparse
import hmac
import io
import json
import os
import secrets
import shutil
import sys
import tempfile
import threading
import time
import traceback
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from wavu import __version__
from wavu.codec import INLINE_LIMIT, decode_input, encode_output
from wavu.scripts import ScriptError, coerce_params, discover
from wavu.types import Cancelled

TERMINAL = ("done", "error", "cancelled")
DEFAULT_HANDSHAKE = Path.home() / ".wavu" / "worker.json"
KEEPALIVE_S = 15.0

_job_local = threading.local()


class _StdoutRouter(io.TextIOBase):
    """print() inside a job goes to that job's log; elsewhere to stderr.

    stdout carries the one-line handshake; after that nobody reads it, so a
    chatty script must not fill the pipe (and its prints belong in Fiji's Log).
    """

    def writable(self) -> bool:
        return True

    def write(self, s: str) -> int:
        job = getattr(_job_local, "job", None)
        if job is None:
            sys.__stderr__.write(s)
            return len(s)
        job._print_buf += s
        while "\n" in job._print_buf:
            line, job._print_buf = job._print_buf.split("\n", 1)
            job.emit("log", {"message": line})
        return len(s)

    def flush(self) -> None:
        sys.__stderr__.flush()


class Ctx:
    """What a script's ``run`` receives as ``ctx``."""

    def __init__(self, job: Job) -> None:
        self._job = job
        self.tmpdir: Path = job.tmpdir
        self.meta: dict[str, dict[str, Any]] = job.input_meta

    def log(self, msg: Any) -> None:
        self._job.emit("log", {"message": str(msg)})

    def progress(self, frac: float) -> None:
        self._job.emit("progress", {"value": max(0.0, min(1.0, float(frac)))})

    def cancelled(self) -> bool:
        return self._job.cancel_event.is_set()

    def check_cancelled(self) -> None:
        if self.cancelled():
            raise Cancelled()


class Job:
    def __init__(self, script: Any, params: dict, inputs: dict, input_meta: dict, tmpdir: Path, inline_limit: int):
        self.id = uuid.uuid4().hex[:12]
        self.script = script
        self.params = params
        self.inputs = inputs
        self.input_meta = input_meta
        self.tmpdir = tmpdir
        self.inline_limit = inline_limit
        self.status = "running"
        self.events: list[tuple[str, dict]] = []
        self.cond = threading.Condition()
        self.cancel_event = threading.Event()
        self.outputs: dict[str, Any] | None = None
        self.error: dict[str, str] | None = None
        self._print_buf = ""

    def emit(self, kind: str, data: dict) -> None:
        with self.cond:
            if self.status in TERMINAL:
                return
            self.events.append((kind, data))
            if kind in TERMINAL:
                self.status = kind
            self.cond.notify_all()

    def run(self) -> None:
        _job_local.job = self
        try:
            ctx = Ctx(self)
            result = self.script.module.run(ctx, self.inputs, self.params)
            if self._print_buf:
                self.emit("log", {"message": self._print_buf})
            if self.cancel_event.is_set():
                self.emit("cancelled", {})
                return
            if result is None:
                result = {}
            if not isinstance(result, dict):
                raise TypeError(f"run() must return a dict, got {type(result).__name__}")
            self.outputs = {str(k): encode_output(str(k), v, self.tmpdir, self.inline_limit) for k, v in result.items()}
            self.emit("done", {"outputs": sorted(self.outputs)})
        except Cancelled:
            self.emit("cancelled", {})
        except BaseException as e:  # noqa: BLE001 - every failure must reach the client
            if self.cancel_event.is_set():
                self.emit("cancelled", {})
            else:
                self.error = {"message": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()}
                sys.__stderr__.write(self.error["traceback"])
                self.emit("error", self.error)
        finally:
            _job_local.job = None


class Worker:
    def __init__(self, script_dir: Path, token: str, tmp_root: Path):
        self.script_dir = Path(script_dir).resolve()
        self.token = token
        self.tmp_root = tmp_root
        self.scripts, self.errors = discover(self.script_dir)
        self.jobs: dict[str, Job] = {}
        self.server: ThreadingHTTPServer | None = None
        self._stopping = threading.Event()

    def start_job(self, body: dict) -> Job:
        name = body.get("script")
        if name not in self.scripts:
            known = ", ".join(sorted(self.scripts)) or "none"
            hint = f" ({self.errors[name]})" if name in self.errors else ""
            raise ScriptError(f"unknown script {name!r}{hint}; available: {known}")
        script = self.scripts[name]
        params = coerce_params(script.params, body.get("params"))
        raw_inputs = body.get("inputs") or {}
        if not isinstance(raw_inputs, dict):
            raise ScriptError("'inputs' must be an object")
        inputs: dict[str, Any] = {}
        meta: dict[str, dict] = {}
        for k, spec in raw_inputs.items():
            try:
                inputs[k], meta[k] = decode_input(spec)
            except ValueError as e:
                raise ScriptError(f"input {k!r}: {e}") from None
        tmpdir = Path(tempfile.mkdtemp(prefix="job-", dir=self.tmp_root))
        job = Job(script, params, inputs, meta, tmpdir, int(body.get("inline_limit", INLINE_LIMIT)))
        self.jobs[job.id] = job
        threading.Thread(target=job.run, name=f"wavu-job-{job.id}", daemon=True).start()
        return job

    def stop(self) -> None:
        if self._stopping.is_set():
            return
        self._stopping.set()
        for job in self.jobs.values():
            job.cancel_event.set()
        if self.server is not None:
            threading.Thread(target=self.server.shutdown, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    server_version = f"wavu/{__version__}"
    worker: Worker  # set on the subclass made in serve()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        if os.environ.get("WAVU_ACCESS_LOG"):
            sys.__stderr__.write("wavu: " + (format % args) + "\n")

    # -- helpers -----------------------------------------------------------
    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def _authorized(self) -> bool:
        got = self.headers.get("Authorization", "")
        ok = hmac.compare_digest(got.encode(), f"Bearer {self.worker.token}".encode())
        if not ok:
            self._error(HTTPStatus.UNAUTHORIZED, "missing or wrong token")
        return ok

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n == 0:
            return {}
        data = json.loads(self.rfile.read(n).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("request body must be a JSON object")
        return data

    def _job(self, job_id: str) -> Job | None:
        job = self.worker.jobs.get(job_id)
        if job is None:
            self._error(HTTPStatus.NOT_FOUND, f"no job {job_id!r}")
        return job

    # -- routes ------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        if not self._authorized():
            return
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        w = self.worker
        if parts == ["health"]:
            self._json(200, {"ok": True, "wavu": __version__, "scripts": len(w.scripts), "script_dir": str(w.script_dir)})
        elif parts == ["scripts"]:
            self._json(200, {"scripts": {n: s.schema() for n, s in w.scripts.items()}, "errors": w.errors})
        elif len(parts) == 3 and parts[0] == "jobs" and parts[2] == "events":
            job = self._job(parts[1])
            if job is not None:
                since = int(parse_qs(url.query).get("since", ["0"])[0])
                self._stream(job, since)
        elif len(parts) == 3 and parts[0] == "jobs" and parts[2] == "result":
            job = self._job(parts[1])
            if job is None:
                return
            if job.status not in TERMINAL:
                self._json(HTTPStatus.CONFLICT, {"status": job.status})
            else:
                payload: dict[str, Any] = {"status": job.status}
                if job.outputs is not None:
                    payload["outputs"] = job.outputs
                if job.error is not None:
                    payload["error"] = job.error
                self._json(200, payload)
        else:
            self._error(HTTPStatus.NOT_FOUND, f"no route GET {url.path}")

    def do_POST(self) -> None:  # noqa: N802
        if not self._authorized():
            return
        parts = [p for p in urlparse(self.path).path.split("/") if p]
        try:
            body = self._body()
        except ValueError as e:
            self._error(HTTPStatus.BAD_REQUEST, f"bad JSON: {e}")
            return
        if parts == ["run"]:
            try:
                job = self.worker.start_job(body)
            except ScriptError as e:
                self._error(HTTPStatus.BAD_REQUEST, str(e))
                return
            self._json(200, {"job": job.id})
        elif len(parts) == 3 and parts[0] == "jobs" and parts[2] == "cancel":
            job = self._job(parts[1])
            if job is not None:
                job.cancel_event.set()
                self._json(200, {"ok": True, "status": job.status})
        elif parts == ["shutdown"]:
            self._json(200, {"ok": True})
            self.worker.stop()
        else:
            self._error(HTTPStatus.NOT_FOUND, f"no route POST /{'/'.join(parts)}")

    def _stream(self, job: Job, since: int) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        i = max(0, since)
        while True:
            with job.cond:
                while i >= len(job.events) and job.status not in TERMINAL:
                    if not job.cond.wait(KEEPALIVE_S):
                        break
                batch = job.events[i:]
                finished = job.status in TERMINAL
            try:
                if not batch and not finished:
                    self.wfile.write(b": keepalive\n\n")
                for kind, data in batch:
                    i += 1
                    self.wfile.write(f"id: {i}\nevent: {kind}\ndata: {json.dumps(data)}\n\n".encode())
                self.wfile.flush()
            except OSError:
                return  # client went away; the job carries on
            if finished and i >= len(job.events):
                return


def _watch_stdin(worker: Worker) -> None:
    try:
        while sys.stdin.buffer.read(4096):
            pass
    except (OSError, ValueError):
        pass
    worker.stop()


def serve(
    script_dir: Path,
    host: str = "127.0.0.1",
    port: int = 0,
    token: str | None = None,
    handshake_file: Path | None = None,
    watch_stdin: bool = True,
    tmp_dir: Path | None = None,
    keep_tmp: bool = False,
) -> int:
    token = token or os.environ.get("WAVU_TOKEN") or secrets.token_urlsafe(24)
    if tmp_dir is not None:
        Path(tmp_dir).mkdir(parents=True, exist_ok=True)
    tmp_root = Path(tempfile.mkdtemp(prefix="wavu-", dir=tmp_dir))
    worker = Worker(script_dir, token, tmp_root)
    for name, err in worker.errors.items():
        sys.__stderr__.write(f"wavu: could not load script {name!r}: {err}\n")
    handler = type("BoundHandler", (Handler,), {"worker": worker})
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    worker.server = server
    real_port = server.server_address[1]
    hello = {"wavu": __version__, "port": real_port, "token": token}
    if handshake_file is not None:
        handshake_file = Path(handshake_file).expanduser()
        handshake_file.parent.mkdir(parents=True, exist_ok=True)
        info = {**hello, "pid": os.getpid(), "host": host, "script_dir": str(worker.script_dir), "tmp_dir": str(tmp_root)}
        handshake_file.write_text(json.dumps(info, indent=2), encoding="utf-8")
    sys.stdout.write(json.dumps(hello) + "\n")
    sys.stdout.flush()
    sys.stdout = _StdoutRouter()
    sys.__stderr__.write(
        f"wavu {__version__}: serving {len(worker.scripts)} script(s) from {worker.script_dir} on {host}:{real_port}\n"
    )
    if watch_stdin:
        threading.Thread(target=_watch_stdin, args=(worker,), daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if handshake_file is not None:
            try:
                handshake_file.unlink()
            except OSError:
                pass
        if not keep_tmp:
            time.sleep(0.05)
            shutil.rmtree(tmp_root, ignore_errors=True)
    return 0


def start_debugpy(port: int, host: str = "127.0.0.1", wait: bool = False) -> None:
    try:
        import debugpy
    except ImportError:
        sys.__stderr__.write("wavu: --debugpy needs the 'debugpy' package in this script's environment\n")
        raise SystemExit(2) from None
    debugpy.listen((host, port))
    sys.__stderr__.write(f"wavu: debugpy listening on {host}:{port} (VS Code: 'Attach to Wavu worker')\n")
    if wait:
        sys.__stderr__.write("wavu: waiting for the debugger to attach...\n")
        debugpy.wait_for_client()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wavu-worker", description=__doc__.split("\n\n")[0])
    p.add_argument("--script-dir", required=True, type=Path, help="folder holding the script(s) and their pixi.toml")
    p.add_argument("--host", default="127.0.0.1", help="interface to bind (default 127.0.0.1; 0.0.0.0 only inside a container)")
    p.add_argument("--port", type=int, default=0, help="port (default: a random free one)")
    p.add_argument("--token", help="auth token (default: $WAVU_TOKEN or a random one)")
    p.add_argument(
        "--handshake-file",
        nargs="?",
        const=DEFAULT_HANDSHAKE,
        type=Path,
        help=f"also write port/token to this JSON file (default when given without a value: {DEFAULT_HANDSHAKE})",
    )
    p.add_argument("--detached", action="store_true", help="do not exit when stdin closes (terminal / container use)")
    p.add_argument("--tmp-dir", type=Path, help="where per-job temp folders go (must be visible to Fiji)")
    p.add_argument("--keep-tmp", action="store_true", help="keep job temp folders after exit")
    p.add_argument("--debugpy", type=int, metavar="PORT", help="start debugpy on this port so VS Code can attach")
    p.add_argument("--debugpy-wait", action="store_true", help="with --debugpy: wait for the debugger before serving")
    p.add_argument("--version", action="version", version=f"wavu {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.script_dir.is_dir():
        sys.__stderr__.write(f"wavu: script folder not found: {args.script_dir}\n")
        return 2
    if args.debugpy:
        start_debugpy(args.debugpy, "0.0.0.0" if args.host == "0.0.0.0" else "127.0.0.1", args.debugpy_wait)
    return serve(
        args.script_dir,
        host=args.host,
        port=args.port,
        token=args.token,
        handshake_file=args.handshake_file,
        watch_stdin=not args.detached,
        tmp_dir=args.tmp_dir,
        keep_tmp=args.keep_tmp,
    )


if __name__ == "__main__":
    raise SystemExit(main())
