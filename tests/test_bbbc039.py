"""A real microscopy image (BBBC039, CC0, committed in tests/data) through the worker by file path."""

from __future__ import annotations

import shutil

import numpy as np
import tifffile

from conftest import REPO, WorkerProc

DATA = REPO / "tests" / "data" / "BBBC039"


def bbbc039_labels(path) -> np.ndarray:
    """BBBC039 masks are a 4-colouring in channel 0; each nucleus is one connected component of one colour."""
    import imagecodecs
    from scipy import ndimage

    colours = imagecodecs.png_decode(path.read_bytes())[..., 0]
    labels = np.zeros(colours.shape, np.uint16)
    n = 0
    for c in np.unique(colours[colours > 0]):
        lab, k = ndimage.label(colours == c)
        labels[lab > 0] = lab[lab > 0] + n
        n += k
    return labels


def test_ground_truth_mask_decodes_to_110_nuclei():
    gt = bbbc039_labels(DATA / "A02_s1_mask.png")
    assert gt.shape == (520, 696) and gt.max() == 110
    assert len(np.unique(gt)) == 111


def test_template_blur_on_a_real_image_by_path(tmp_path):
    script_dir = tmp_path / "s"
    shutil.copytree(REPO / "templates" / "wavu-script", script_dir,
                    ignore=shutil.ignore_patterns(".pixi", "pixi.lock", ".github"))
    w = WorkerProc(script_dir)
    try:
        job = w.client.run("script", params={"sigma": 3},
                           inputs={"image": {"path": str(DATA / "A02_s1.tif")}}, inline_limit=0)
        events = w.client.events(job)
        assert events[-1][0] == "done", events
        out = w.client.get(f"/jobs/{job}/result")[1]["outputs"]["blurred"]
        assert "data" not in out  # inline_limit=0: TIFF path
        blurred = tifffile.imread(out["path"])
        src = tifffile.imread(DATA / "A02_s1.tif")
        assert blurred.shape == src.shape == (520, 696) and blurred.dtype == np.uint16
        assert blurred.astype(float).std() < src.astype(float).std()
    finally:
        w.stop()
