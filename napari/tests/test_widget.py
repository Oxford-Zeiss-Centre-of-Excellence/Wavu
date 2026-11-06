"""The dock widget on a napari viewer model, against a real wavu-worker.

The worker runs in this test environment with plain Python (no pixi), serving
tests/scripts; test_pixi.py covers the real `pixi run` path.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from napari_wavu._widget import WavuWidget, param_widget

SCRIPTS = Path(__file__).parent / "scripts"
pytestmark = pytest.mark.timeout(180)


@pytest.fixture
def widget(viewer, qtbot, monkeypatch):
    from wavu import client

    real_start = client.Worker.start.__func__

    def start(cls, script_dir, **kw):  # same Worker.start, but the worker is plain `python -m wavu.worker`
        kw["command"] = [sys.executable, "-m", "wavu.worker", "--script-dir", str(script_dir)]
        return real_start(cls, script_dir, **kw)

    monkeypatch.setattr(client.Worker, "start", classmethod(start))
    w = WavuWidget(viewer)
    qtbot.addWidget(w.native)
    yield viewer, w
    w.stop_all()


def start_worker(w, qtbot):
    w._folder.value = SCRIPTS
    w._start.changed.emit(True)
    qtbot.waitUntil(lambda: bool(w._script.choices), timeout=60000)


def test_param_widgets_follow_the_contract():
    assert param_widget("sigma", {"type": "float", "default": 2.0}, []).value == 2.0
    assert param_widget("n", {"type": "int", "default": 3}, []).value == 3
    assert param_widget("fast", {"type": "bool", "default": True}, []).value is True
    w = param_widget("m", {"type": "choice", "choices": ["a", "b"], "default": "b"}, [])
    assert w.value == "b"
    assert param_widget("note", {"type": "str", "default": "x", "label": "A note"}, []).label == "A note"


def test_start_lists_scripts_and_builds_the_form(widget, qtbot):
    viewer, w = widget
    viewer.add_image(np.zeros((8, 8), np.float32), name="cells")
    start_worker(w, qtbot)
    assert "blur" in w._script.choices
    w._script.value = "blur"
    names = [p.name for p in w._params]
    assert names == ["image", "sigma", "label_it"]
    assert w._params["image"].value is viewer.layers["cells"]
    assert "Worker ready" in w._log.value


def test_run_adds_result_layers(widget, qtbot):
    viewer, w = widget
    img = np.zeros((32, 32), np.float32)
    img[16, 16] = 100
    viewer.add_image(img, name="cells", scale=(0.5, 0.5))
    start_worker(w, qtbot)
    w._script.value = "blur"
    w._params["sigma"].value = 2.0
    w._params["label_it"].value = True
    w._run.changed.emit(True)
    qtbot.waitUntil(lambda: "Done." in w._log.value or "Error" in w._log.value, timeout=60000)
    assert "Error" not in w._log.value, w._log.value
    blurred = viewer.layers["blurred"]
    assert 0 < blurred.data[16, 16] < 100
    assert tuple(blurred.scale) == (0.5, 0.5)
    assert type(viewer.layers["labels"]).__name__ == "Labels"
    assert "pixel size 0.5" in w._log.value


def test_script_errors_are_shown_not_raised(widget, qtbot):
    viewer, w = widget
    start_worker(w, qtbot)
    w._script.value = "boom"
    w._run.changed.emit(True)
    qtbot.waitUntil(lambda: "Error" in w._log.value and w._run.enabled, timeout=60000)
    assert "kaboom" in w._log.value


def test_cancel_is_reported_as_cancelled_not_as_an_error(widget, qtbot):
    viewer, w = widget
    start_worker(w, qtbot)
    w._script.value = "slow"
    w._run.changed.emit(True)
    qtbot.waitUntil(lambda: "started" in w._log.value, timeout=60000)
    w._stop_job.changed.emit(True)
    qtbot.waitUntil(lambda: "Cancelled." in w._log.value and w._run.enabled, timeout=60000)
    assert "Error" not in w._log.value


def test_remote_container_settings_connect_with_a_shared_folder(viewer, qtbot, tmp_path):
    import subprocess

    shared = tmp_path / "shared"
    shared.mkdir()
    hs = tmp_path / "worker.json"
    proc = subprocess.Popen([sys.executable, "-m", "wavu.worker", "--script-dir", str(SCRIPTS),
                             "--handshake-file", str(hs), "--tmp-dir", str(shared / ".wavu-tmp")],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc.stdout.readline()  # handshake line: the worker is up
    w = WavuWidget(viewer)
    qtbot.addWidget(w.native)
    try:
        assert w._remote_box.native.isHidden()
        w._remote.value = True
        assert not w._remote_box.native.isHidden()
        w._handshake.value = hs
        w._host_dir.value = shared
        w._worker_dir.value = str(shared)  # same folder, same name: a local stand-in for a container mount
        w._connect.changed.emit(True)
        qtbot.waitUntil(lambda: bool(w._script.choices) or "Error" in w._log.value, timeout=30000)
        assert "host folder" in w._log.value and w.worker.worker_prefix == str(shared)
        viewer.add_image(np.ones((2, 3, 12, 12), np.float32), name="stack")  # 4-D: travels through the shared folder
        w._script.value = "blur"
        w._run.changed.emit(True)
        qtbot.waitUntil(lambda: "Done." in w._log.value or "Error" in w._log.value, timeout=60000)
        assert "Error" not in w._log.value, w._log.value
        assert viewer.layers["blurred"].data.shape == (2, 3, 12, 12)
    finally:
        proc.stdin.close()
        proc.wait(10)


def test_remote_settings_need_both_folders_or_neither(viewer, qtbot, tmp_path):
    w = WavuWidget(viewer)
    qtbot.addWidget(w.native)
    w._remote.value = True
    w._worker_dir.value = "/data"
    w._connect.changed.emit(True)
    assert "give both the host folder and the container folder" in w._log.value
