"""wavu.client against a real worker subprocess (tests/scripts as the script folder)."""

from __future__ import annotations

import json
import sys
import threading

import numpy as np
import pytest

from wavu import RoiSet
from wavu.client import JobCancelled, Worker, WorkerError, child_env, worker_command

from conftest import SCRIPTS, WorkerProc

pytestmark = pytest.mark.timeout(120)


@pytest.fixture(scope="module")
def w():
    logs: list[str] = []
    worker = Worker.start(SCRIPTS, command=[sys.executable, "-m", "wavu.worker", "--script-dir", str(SCRIPTS)],
                          on_log=logs.append)
    worker.start_logs = logs
    yield worker
    worker.stop()


def test_start_reads_the_handshake_and_logs_progress(w):
    assert w.alive()
    assert any("Worker ready" in m for m in w.start_logs)
    assert w.health()["ok"] is True


def test_scripts_lists_schemas_and_errors(w):
    s = w.scripts()
    assert "echo" in s["scripts"] and "broken" in s["errors"]
    assert s["scripts"]["echo"]["params"]["which"]["choices"] == ["a", "b"]


def test_run_round_trips_an_inline_image_and_params(w):
    img = np.arange(12, dtype=np.uint16).reshape(3, 4)
    res = w.run("echo", {"factor": 2, "flag": True, "which": "a"}, {"image": img}, meta={"image": {"pixel_um": 0.25}})
    np.testing.assert_array_equal(res.outputs["image"].value, img * 2)
    assert res.outputs["params"].value == "hi|True|a|0.5"
    assert res.outputs["meta"].value == "0.25"


def test_large_inputs_travel_as_tiff(w):
    img = np.ones((2, 3, 30, 30), dtype=np.float32)  # 4-D never travels inline
    enc = w.encode_inputs({"image": img})
    assert "path" in enc["image"] and "data" not in enc["image"]
    res = w.run("echo", {}, {"image": img})
    assert res.outputs["image"].value.shape == (2, 3, 30, 30)


def test_every_output_kind_is_loaded(w):
    pytest.importorskip("pandas")
    pytest.importorskip("roifile")
    out = w.run("outputs").outputs
    assert out["labels"].kind == "image" and out["labels"].value.dtype == np.uint16
    assert out["big"].kind == "image" and out["big"].value.shape == (4, 40, 50)
    assert out["big"].meta["pixel_um"] == 0.5
    assert list(out["table"].value.columns) == ["label", "area"]
    assert out["rows"].kind == "table"
    assert isinstance(out["rois"].value, RoiSet) and out["rois"].value.path.is_file()
    assert out["count"].value == 1


def test_logs_are_streamed(w):
    seen: list[str] = []
    with pytest.raises(WorkerError, match="kaboom from script") as e:
        w.run("boom", on_log=seen.append)
    assert seen == ["about to fail"]
    assert "Traceback" in str(e.value)


def test_cancel_stops_a_running_job(w):
    cancel = threading.Event()
    seen: list[str] = []

    def on_log(m: str) -> None:
        seen.append(m)
        if m == "started":
            cancel.set()

    with pytest.raises(JobCancelled):
        w.run("slow", on_log=on_log, cancel=cancel)
    assert "saw cancel" in seen


def test_bad_params_are_reported(w):
    with pytest.raises(WorkerError, match="unknown script"):
        w.run("nope")


def test_connect_through_a_handshake_file(tmp_path):
    hs = tmp_path / "worker.json"
    proc = WorkerProc(SCRIPTS, "--handshake-file", str(hs))
    try:
        w = Worker.connect(hs)
        assert w.script_dir == str(SCRIPTS.resolve())
        assert w.alive()
    finally:
        proc.stop()


def test_connect_without_a_handshake_file_explains(tmp_path):
    with pytest.raises(WorkerError, match="pixi run worker"):
        Worker.connect(tmp_path / "missing.json")


def test_start_reports_an_early_exit(tmp_path):
    with pytest.raises(WorkerError, match="exited"):
        Worker.start(tmp_path, command=[sys.executable, "-c", "import sys; sys.exit(3)"])


def test_worker_command_uses_the_folder_manifest(tmp_path):
    (tmp_path / "pixi.toml").write_text("")
    cmd = worker_command(tmp_path, pixi="pixi", frozen=True)
    assert cmd[:4] == ["pixi", "run", "--manifest-path", str(tmp_path / "pixi.toml")]
    assert "--frozen" in cmd and cmd[-2:] == ["--script-dir", str(tmp_path)]
    with pytest.raises(WorkerError, match="no pixi.toml"):
        worker_command(tmp_path / "elsewhere", pixi="pixi")


def test_child_env_drops_the_host_pixi_environment(monkeypatch):
    monkeypatch.setenv("PIXI_PROJECT_MANIFEST", "/host/pixi.toml")
    monkeypatch.setenv("CONDA_PREFIX", "/host/.pixi/envs/default")
    env = child_env()
    assert "PIXI_PROJECT_MANIFEST" not in env and "CONDA_PREFIX" not in env
    assert env["PYTHONUNBUFFERED"] == "1"
    json.dumps(env)
