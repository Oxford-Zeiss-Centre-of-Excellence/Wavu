"""A real microscopy frame (CTC Fluo-N2DH-GOWT1) through the worker by file path.

Skips unless `pixi run fetch-test-data` has been run (data is never committed).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest
import tifffile

from conftest import REPO, WorkerProc

DATA = REPO / "tests" / "data" / "Fluo-N2DH-GOWT1"
pytestmark = [
    pytest.mark.test_data,
    pytest.mark.skipif(not (DATA / "t021.tif").exists(), reason="run `pixi run fetch-test-data`"),
]


def test_template_blur_on_a_real_frame_by_path(tmp_path):
    script_dir = tmp_path / "s"
    shutil.copytree(REPO / "templates" / "wavu-script", script_dir, ignore=shutil.ignore_patterns(".pixi", "pixi.lock"))
    w = WorkerProc(script_dir)
    try:
        job = w.client.run("script", params={"sigma": 3}, inputs={"image": {"path": str(DATA / "t021.tif"), "meta": {"pixel_um": 0.24}}},
                           inline_limit=0)
        events = w.client.events(job)
        assert events[-1][0] == "done", events
        out = w.client.get(f"/jobs/{job}/result")[1]["outputs"]["blurred"]
        assert "data" not in out  # inline_limit=0: TIFF path
        blurred = tifffile.imread(out["path"])
        src = tifffile.imread(DATA / "t021.tif")
        assert blurred.shape == src.shape == (1024, 1024) and blurred.dtype == np.uint8
        assert blurred.astype(float).std() < src.astype(float).std()
    finally:
        w.stop()


def test_ground_truth_labels_are_a_sane_label_image():
    gt = tifffile.imread(DATA / "man_seg021.tif")
    assert gt.dtype == np.uint16 and len(np.unique(gt)) - 1 == 24
