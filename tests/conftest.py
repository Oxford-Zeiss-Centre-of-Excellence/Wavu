"""Shared fixtures: a real wavu-worker subprocess and a tiny HTTP client for it."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SCRIPTS = HERE / "scripts"
REPO = HERE.parent


class Client:
    def __init__(self, port: int, token: str):
        self.base = f"http://127.0.0.1:{port}"
        self.token = token

    def request(self, method: str, path: str, body: dict | None = None, token: str | None = "default"):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if token == "default":
            token = self.token
        if token is not None:
            req.add_header("Authorization", f"Bearer {token}")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "{}")

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.request("POST", path, body if body is not None else {}, **kw)

    def events(self, job: str, since: int = 0) -> list[tuple[str, dict]]:
        """Read the SSE stream to its end; returns [(event, data), ...]."""
        req = urllib.request.Request(f"{self.base}/jobs/{job}/events?since={since}")
        req.add_header("Authorization", f"Bearer {self.token}")
        out, kind = [], None
        with urllib.request.urlopen(req, timeout=60) as r:
            assert r.headers["Content-Type"].startswith("text/event-stream")
            for raw in r:
                line = raw.decode().rstrip("\r\n")
                if line.startswith("event: "):
                    kind = line[7:]
                elif line.startswith("data: "):
                    out.append((kind, json.loads(line[6:])))
        return out

    def run(self, script: str, params=None, inputs=None, **extra):
        status, body = self.post("/run", {"script": script, "params": params or {}, "inputs": inputs or {}, **extra})
        assert status == 200, body
        return body["job"]


class WorkerProc:
    def __init__(self, script_dir: Path, *extra: str):
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "wavu.worker", "--script-dir", str(script_dir), *extra],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        line = self.proc.stdout.readline().decode()
        assert line, self.proc.stderr.read().decode()
        self.hello_line = line
        self.hello = json.loads(line)
        self.client = Client(self.hello["port"], self.hello["token"])

    def stop(self):
        if self.proc.poll() is None:
            try:
                self.proc.stdin.close()
            except OSError:
                pass
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        for s in (self.proc.stdout, self.proc.stderr):
            s.close()


@pytest.fixture(scope="module")
def worker():
    w = WorkerProc(SCRIPTS)
    yield w
    w.stop()


@pytest.fixture
def client(worker) -> Client:
    return worker.client
