"""Cellpose example tests. Heavy: marked `cellpose`, run weekly in CI.

    pixi run test   (in this folder) -- uses the CTC frame from `pixi run fetch-test-data`
                    at the repo root when present, plus a synthetic image always.
"""

from pathlib import Path

import numpy as np
import pytest

from wavu.testing import FakeCtx, run_script

pytestmark = pytest.mark.cellpose

HERE = Path(__file__).parent
SCRIPT = HERE / "script.py"
DATA = HERE.parent.parent / "tests" / "data" / "Fluo-N2DH-GOWT1"


def synthetic_nuclei():
    rng = np.random.default_rng(1)
    yy, xx = np.mgrid[:256, :256]
    img = np.zeros((256, 256), np.float32)
    centres = [(60, 60), (60, 180), (180, 70), (190, 190), (128, 128)]
    for cy, cx in centres:
        img += 200 * (((yy - cy) ** 2 + (xx - cx) ** 2) < 18**2)
    return (img + rng.normal(10, 3, img.shape)).clip(0, 255).astype(np.uint8), len(centres)


def test_segments_synthetic_nuclei():
    img, expected = synthetic_nuclei()
    ctx = FakeCtx()
    out = run_script(SCRIPT, {"image": img}, {"diameter": 36.0, "use_gpu": False}, ctx=ctx)
    assert abs(out["count"] - expected) <= 1
    assert out["labels"].shape == img.shape
    assert out["rois"].path.is_file()
    assert ctx.progress_values[-1] == 1.0


@pytest.mark.skipif(not (DATA / "t021.tif").exists(), reason="run `pixi run fetch-test-data` at the repo root")
def test_matches_ctc_ground_truth():
    import tifffile

    img = tifffile.imread(DATA / "t021.tif")
    gt = tifffile.imread(DATA / "man_seg021.tif")
    labels = run_script(SCRIPT, {"image": img}, {"use_gpu": False})["labels"]
    # Fraction of ground-truth nuclei matched by a predicted nucleus with IoU > 0.5.
    gt_ids = [i for i in np.unique(gt) if i]
    matched = 0
    for i in gt_ids:
        m = gt == i
        ids, counts = np.unique(labels[m], return_counts=True)
        best = ids[np.argmax(counts)]
        if best == 0:
            continue
        p = labels == best
        if (m & p).sum() / (m | p).sum() > 0.5:
            matched += 1
    assert matched / len(gt_ids) > 0.7, f"{matched}/{len(gt_ids)} GT nuclei matched"
