"""Tests for script.py -- run with `pixi run test` in this folder. No Fiji needed."""

from pathlib import Path

import numpy as np
import pytest

from wavu.testing import FakeCtx, run_script

SCRIPT = Path(__file__).with_name("script.py")
DEMO = Path(__file__).resolve().parents[1] / "data" / "demo_timelapse.tif"


def blobs(shape, centres, r=5, value=1000):
    yy, xx = np.mgrid[: shape[0], : shape[1]]
    img = np.full(shape, 100, np.uint16)
    for y, x in centres:
        img[(yy - y) ** 2 + (xx - x) ** 2 <= r * r] = value
    return img


def test_counts_blobs_per_frame():
    stack = np.stack([blobs((64, 64), [(15, 15), (45, 45)]),
                      blobs((64, 64), [(15, 15), (45, 45), (15, 48)])])
    ctx = FakeCtx(meta={"image": {"pixel_um": 0.5}})
    out = run_script(SCRIPT, {"image": stack}, {"sigma": 1.0, "min_area": 10}, ctx=ctx)

    labels = out["labels"]
    assert labels.data.shape == (2, 64, 64) and labels.data.dtype == np.uint16 and labels.axes == "TYX"
    assert labels.pixel_um == 0.5
    assert out["count_per_frame"]["count"].tolist() == [2, 3]
    assert labels.data[0].max() == 2 and labels.data[1].max() == 3          # labels restart each frame
    det = out["detections"]
    assert list(det.columns) == ["frame", "label", "y", "x", "area", "mean_intensity"]
    assert det.groupby("frame").size().tolist() == [2, 3]
    first = det[(det.frame == 0) & (det.label == 1)].iloc[0]
    assert abs(first.y - 15) < 0.5 and abs(first.x - 15) < 0.5
    assert first.area > 60 and first.mean_intensity > 900
    assert ctx.progress_values[-1] == 1.0


def test_a_single_image_is_one_frame_and_small_objects_are_dropped():
    img = blobs((48, 48), [(20, 20)], r=6)
    img[40:42, 40:42] = 1000                                                 # 4 px speck
    out = run_script(SCRIPT, {"image": img}, {"sigma": 0.0, "threshold": "li", "min_area": 20})
    assert out["labels"].data.shape == (1, 48, 48)
    assert out["count_per_frame"]["count"].tolist() == [1]


def test_cancel_stops_early():
    stack = np.stack([blobs((32, 32), [(16, 16)])] * 5)
    ctx = FakeCtx(cancel_after=2)
    assert run_script(SCRIPT, {"image": stack}, {}, ctx=ctx) == {}
    assert len(ctx.progress_values) == 2


def test_demo_timelapse_counts_follow_the_truth():
    tifffile = pytest.importorskip("tifffile")
    if not DEMO.is_file():
        pytest.skip("examples/data/demo_timelapse.tif missing (pixi run demo-data in the repo root)")
    stack = tifffile.imread(DEMO)
    out = run_script(SCRIPT, {"image": stack}, {})
    counts = out["count_per_frame"]["count"].to_numpy()
    assert stack.shape == (30, 256, 256)
    assert counts[0] == 25 and counts[-1] >= 28                              # cells divide and enter
