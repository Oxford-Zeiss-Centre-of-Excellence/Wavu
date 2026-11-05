"""The worker's HTTP protocol, against a real subprocess (tests/scripts as the script folder)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest
import tifffile

import wavu
from wavu.codec import decode_array, encode_array

from conftest import SCRIPTS, WorkerProc

pytestmark = pytest.mark.timeout(120)


# -- handshake & auth ---------------------------------------------------------


def test_handshake_is_exactly_one_json_line(worker):
    hello = json.loads(worker.hello_line)
    assert set(hello) == {"wavu", "port", "token"}
    assert hello["wavu"] == wavu.__version__
    assert isinstance(hello["port"], int) and hello["port"] > 0
    assert len(hello["token"]) >= 20


@pytest.mark.parametrize("token", [None, "wrong-token"])
@pytest.mark.parametrize("method,path", [("GET", "/health"), ("GET", "/scripts"), ("POST", "/run"), ("POST", "/shutdown")])
def test_requests_without_the_right_token_are_rejected(client, token, method, path):
    status, body = client.request(method, path, body={} if method == "POST" else None, token=token)
    assert status == 401
    assert "token" in body["error"]


def test_health(client):
    status, body = client.get("/health")
    assert status == 200
    assert body["ok"] is True and body["wavu"] == wavu.__version__


def test_unknown_route_is_404(client):
    assert client.get("/nope")[0] == 404


# -- /scripts -----------------------------------------------------------------


def test_scripts_lists_runnable_scripts_with_their_schema(client):
    status, body = client.get("/scripts")
    assert status == 200
    scripts = body["scripts"]
    assert {"echo", "chatty", "slow", "boom", "outputs"} <= set(scripts)
    assert "helper_mod" not in scripts  # no run(): a helper, not a script
    echo = scripts["echo"]
    assert echo["doc"].startswith("Returns its input")
    p = echo["params"]
    assert p["image"] == {"type": "image", "label": "Image"}
    assert p["factor"] == {"type": "int", "default": 1, "label": "Factor"}
    assert p["note"]["label"] == "A note"
    assert p["which"]["choices"] == ["a", "b"] and p["which"]["default"] == "b"
    assert p["flag"] == {"type": "bool", "default": False, "label": "Flag"}


def test_scripts_reports_import_errors_without_crashing(client):
    _, body = client.get("/scripts")
    assert "broken" not in body["scripts"]
    assert "ModuleNotFoundError" in body["errors"]["broken"]


# -- /run + SSE ---------------------------------------------------------------


def test_run_streams_log_and_progress_then_done(client):
    job = client.run("chatty", params={"steps": 3})
    events = client.events(job)
    kinds = [k for k, _ in events]
    assert kinds == ["log", "progress", "log", "progress", "log", "progress", "log", "done"]
    assert [d["message"] for k, d in events if k == "log"] == ["step 0", "step 1", "step 2", "printed line"]
    assert [d["value"] for k, d in events if k == "progress"] == pytest.approx([1 / 3, 2 / 3, 1.0])
    status, result = client.get(f"/jobs/{job}/result")
    assert status == 200 and result["status"] == "done"
    assert result["outputs"]["answer"] == {"kind": "value", "value": 42}


def test_events_can_resume_from_an_index(client):
    job = client.run("chatty", params={"steps": 2})
    full = client.events(job)
    assert client.events(job, since=2) == full[2:]


def test_inline_image_round_trip_with_params_and_meta(client):
    img = np.arange(12, dtype=np.uint16).reshape(3, 4)
    spec = encode_array(img, {"pixel_um": 0.25, "channel_names": ["DAPI"]})
    job = client.run("echo", params={"factor": "3", "note": "x", "flag": "true", "which": "a"}, inputs={"image": spec})
    assert client.events(job)[-1][0] == "done"
    out = client.get(f"/jobs/{job}/result")[1]["outputs"]
    assert out["image"]["kind"] == "image"
    np.testing.assert_array_equal(decode_array(out["image"]), img * 3)
    assert out["params"]["value"] == "x|True|a|0.5"
    assert out["meta"]["value"] == "0.25"


def test_image_input_by_file_path(client, tmp_path):
    img = np.ones((5, 6), dtype=np.uint8)
    path = tmp_path / "in.tif"
    tifffile.imwrite(path, img)
    job = client.run("echo", inputs={"image": {"path": str(path)}})
    client.events(job)
    out = client.get(f"/jobs/{job}/result")[1]["outputs"]
    np.testing.assert_array_equal(decode_array(out["image"]), img)


def test_every_output_kind(client):
    job = client.run("outputs")
    events = client.events(job)
    assert events[-1][0] == "done", events
    out = client.get(f"/jobs/{job}/result")[1]["outputs"]
    labels = out["labels"]
    assert labels["kind"] == "image" and labels["dtype"] == "uint16"  # int64 labels -> ImageJ 16-bit
    assert decode_array(labels).max() == 1
    big = out["big"]
    assert big["kind"] == "image" and "data" in big  # 3-D and small: inline
    assert big["dtype"] == "float32" and big["shape"] == [4, 40, 50]
    assert big["meta"] == {"pixel_um": 0.5, "axes": "ZYX"}
    assert out["table"]["kind"] == "table" and out["table"]["columns"] == ["label", "area"]
    assert Path(out["table"]["path"]).read_text().splitlines()[0] == "label,area"
    assert out["rows"]["columns"] == ["a", "b"]
    assert out["rois"]["kind"] == "rois" and Path(out["rois"]["path"]).is_file()
    assert out["count"] == {"kind": "value", "value": 1}


def test_inline_limit_sends_big_images_as_tiff_files(client):
    job = client.run("outputs", inline_limit=100)
    client.events(job)
    out = client.get(f"/jobs/{job}/result")[1]["outputs"]
    big = out["big"]
    assert "data" not in big
    arr = tifffile.imread(big["path"])
    assert arr.shape == (4, 40, 50) and arr.dtype == np.float32
    with tifffile.TiffFile(big["path"]) as tf:
        assert tf.imagej_metadata["unit"] == "um"
    assert big["meta"] == {"pixel_um": 0.5, "axes": "ZYX"}


# -- errors -------------------------------------------------------------------


def test_script_exception_becomes_error_event_with_traceback(client):
    job = client.run("boom")
    events = client.events(job)
    assert [k for k, _ in events] == ["log", "error"]
    err = events[-1][1]
    assert err["message"] == "RuntimeError: kaboom from script"
    assert "boom.py" in err["traceback"]
    status, result = client.get(f"/jobs/{job}/result")
    assert result["status"] == "error" and result["error"]["message"] == err["message"]


def test_non_dict_return_is_an_error(client):
    job = client.run("bad_return")
    assert client.events(job)[-1] == ("error", client.get(f"/jobs/{job}/result")[1]["error"])


@pytest.mark.parametrize(
    "body,fragment",
    [
        ({"script": "nope"}, "unknown script 'nope'"),
        ({"script": "broken"}, "ModuleNotFoundError"),
        ({"script": "echo", "params": {"factor": "abc"}}, "factor"),
        ({"script": "echo", "params": {"which": "z"}}, "not one of"),
        ({"script": "echo", "params": {"bogus": 1}}, "unknown parameter"),
        ({"script": "echo", "inputs": {"image": {"path": "/no/such/file.tif"}}}, "not found"),
        ({"script": "echo", "inputs": {"image": {"dtype": "uint8", "shape": [2, 2], "data": "AA=="}}}, "bytes"),
    ],
)
def test_bad_run_requests_are_400_with_a_message(client, body, fragment):
    status, resp = client.post("/run", body)
    assert status == 400
    assert fragment in resp["error"]


def test_unknown_job_is_404(client):
    assert client.get("/jobs/doesnotexist/result")[0] == 404
    assert client.post("/jobs/doesnotexist/cancel")[0] == 404


# -- cancel -------------------------------------------------------------------


def test_cancel_a_running_job(client):
    job = client.run("slow")
    assert client.get(f"/jobs/{job}/result")[0] == 409  # still running
    time.sleep(0.2)
    status, body = client.post(f"/jobs/{job}/cancel")
    assert status == 200 and body["ok"]
    events = client.events(job)
    assert events[0] == ("log", {"message": "started"})
    assert events[-1][0] == "cancelled"
    assert client.get(f"/jobs/{job}/result")[1] == {"status": "cancelled"}


# -- lifetime -----------------------------------------------------------------


def test_worker_exits_when_stdin_closes():
    w = WorkerProc(SCRIPTS)
    assert w.client.get("/health")[0] == 200
    w.proc.stdin.close()
    assert w.proc.wait(15) == 0
    w.stop()


def test_post_shutdown_stops_the_worker_and_removes_the_handshake_file(tmp_path):
    hs = tmp_path / "worker.json"
    w = WorkerProc(SCRIPTS, "--handshake-file", str(hs), "--detached")
    info = json.loads(hs.read_text())
    assert info["port"] == w.hello["port"] and info["token"] == w.hello["token"]
    assert Path(info["script_dir"]) == SCRIPTS.resolve()
    assert w.client.post("/shutdown")[0] == 200
    assert w.proc.wait(15) == 0
    assert not hs.exists()
    w.stop()


def test_detached_worker_ignores_closed_stdin():
    w = WorkerProc(SCRIPTS, "--detached")
    w.proc.stdin.close()
    time.sleep(1.0)
    assert w.proc.poll() is None
    assert w.client.post("/shutdown")[0] == 200
    assert w.proc.wait(15) == 0
    w.stop()


def test_fixed_token_from_environment(monkeypatch):
    monkeypatch.setenv("WAVU_TOKEN", "my-fixed-token-123456789")
    w = WorkerProc(SCRIPTS)
    try:
        assert w.hello["token"] == "my-fixed-token-123456789"
    finally:
        w.stop()


def test_missing_script_dir_exits_2(tmp_path):
    r = subprocess.run([sys.executable, "-m", "wavu.worker", "--script-dir", str(tmp_path / "x")], capture_output=True)
    assert r.returncode == 2 and b"not found" in r.stderr
