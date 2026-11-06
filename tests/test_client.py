"""wavu.client against a real worker subprocess (tests/scripts as the script folder)."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

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
    (tmp_path / ".pixi" / "envs").mkdir(parents=True)  # already installed
    cmd = worker_command(tmp_path, pixi="pixi", frozen=True)
    assert cmd[:4] == ["pixi", "run", "--manifest-path", str(tmp_path / "pixi.toml")]
    assert "--frozen" in cmd and cmd[-2:] == ["--script-dir", str(tmp_path)]
    with pytest.raises(WorkerError, match="no pixi.toml"):
        worker_command(tmp_path / "elsewhere", pixi="pixi")


def test_first_start_asks_pixi_for_progress_lines(tmp_path):
    (tmp_path / "pixi.toml").write_text("")
    assert worker_command(tmp_path, pixi="pixi")[:3] == ["pixi", "run", "-v"]   # no environment yet
    (tmp_path / ".pixi" / "envs").mkdir(parents=True)
    assert "-v" not in worker_command(tmp_path, pixi="pixi")                  # installed: stay quiet


def test_child_env_drops_the_host_pixi_environment(monkeypatch):
    monkeypatch.setenv("PIXI_PROJECT_MANIFEST", "/host/pixi.toml")
    monkeypatch.setenv("CONDA_PREFIX", "/host/.pixi/envs/default")
    env = child_env()
    assert "PIXI_PROJECT_MANIFEST" not in env and "CONDA_PREFIX" not in env
    assert env["PYTHONUNBUFFERED"] == "1"
    json.dumps(env)


# -- container / remote path mapping ------------------------------------------


def test_paths_are_translated_between_host_and_container():
    w = Worker("127.0.0.1", 1, "t", host_prefix=r"D:\data", worker_prefix="/data")
    assert w.to_worker(r"D:\data\cells\a.tif") == "/data/cells/a.tif"
    assert w.to_worker("d:/DATA/b.tif") == "/data/b.tif"            # Windows paths ignore case
    assert w.to_worker("E:/elsewhere/c.tif") == "E:/elsewhere/c.tif"  # outside the shared folder: unchanged
    assert w.from_worker("/data/.wavu-tmp/job/out.tif").replace("\\", "/") == "D:/data/.wavu-tmp/job/out.tif"
    assert w.from_worker("/tmp/x.tif") == "/tmp/x.tif"
    assert w._tmp == Path(r"D:\data") / ".wavu-tmp"                    # large inputs go where the container sees them


def test_large_inputs_are_sent_as_container_paths(tmp_path):
    w = Worker("127.0.0.1", 1, "t", host_prefix=str(tmp_path), worker_prefix="/data")
    enc = w.encode_inputs({"image": np.zeros((2, 3, 8, 8), np.float32)})
    assert enc["image"]["path"].startswith("/data/.wavu-tmp/")
    assert (tmp_path / ".wavu-tmp" / enc["image"]["path"].rsplit("/", 1)[1]).is_file()


def test_connect_with_a_shared_folder_runs_end_to_end(tmp_path):
    hs = tmp_path / "worker.json"
    shared = tmp_path / "shared"
    shared.mkdir()
    proc = WorkerProc(SCRIPTS, "--handshake-file", str(hs), "--tmp-dir", str(shared / ".wavu-tmp"))
    try:
        # Same folder under the same name on both sides (a local stand-in for a container mount).
        w = Worker.connect(hs, host_prefix=shared, worker_prefix=str(shared))
        img = np.ones((2, 3, 10, 10), np.float32)                    # 4-D: travels as a file in the shared folder
        res = w.run("echo", {}, {"image": img})
        assert res.outputs["image"].value.shape == img.shape
    finally:
        proc.stop()


# -- table / file inputs (scripted pipelines) -----------------------------------


def test_a_dataframe_input_travels_as_a_temporary_csv(w):
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"label": [1, 2, 3], "area": [10.0, 20.5, 7.0]})
    enc = w.encode_inputs({"table": df})
    path = Path(enc["table"]["path"])
    assert path.suffix == ".csv" and path.parent == w._tmp and path.is_file()
    assert "data" not in enc["table"]
    w._made.remove(path)
    path.unlink()

    res = w.run("table_stats", {}, {"table": df})
    assert res.outputs["n_rows"].value == 3
    assert res.outputs["kind"].value == "DataFrame"
    back = res.outputs["doubled"].value
    assert list(back.columns) == ["label", "area", "double"]
    assert back["double"].tolist() == [20.0, 41.0, 14.0]
    assert not list(w._tmp.glob("*-table.csv"))  # temporary CSV removed after run()


def test_a_list_of_dicts_input_travels_as_a_csv(w):
    pytest.importorskip("pandas")
    rows = [{"label": 1, "area": 4}, {"label": 2, "area": 5}]
    res = w.run("table_stats", {}, {"table": rows})
    assert res.outputs["n_rows"].value == 2
    assert res.outputs["doubled"].value["double"].tolist() == [8, 10]
    assert not list(w._tmp.glob("*-table.csv"))


def test_a_csv_path_input_passes_through(w, tmp_path):
    pytest.importorskip("pandas")
    csv_path = tmp_path / "t.csv"
    csv_path.write_text("label,area\n1,3\n", encoding="utf-8")
    enc = w.encode_inputs({"table": csv_path})
    assert enc["table"]["path"] == str(csv_path)
    res = w.run("table_stats", {}, {"table": str(csv_path)})
    assert res.outputs["n_rows"].value == 1
    assert csv_path.is_file()  # the caller's own file is never removed


def test_table_inputs_are_written_to_the_shared_folder(tmp_path):
    pd = pytest.importorskip("pandas")
    w = Worker("127.0.0.1", 1, "t", host_prefix=str(tmp_path), worker_prefix="/data")
    enc = w.encode_inputs({"det": pd.DataFrame({"a": [1]}), "rows": [{"a": 1}]})
    for name in ("det", "rows"):
        p = enc[name]["path"]
        assert p.startswith("/data/.wavu-tmp/") and p.endswith(f"-{name}.csv")
        assert (tmp_path / ".wavu-tmp" / p.rsplit("/", 1)[1]).is_file()
