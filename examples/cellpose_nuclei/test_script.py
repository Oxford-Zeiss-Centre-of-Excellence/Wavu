"""Cellpose example tests. Heavy: marked `cellpose`, run weekly in CI.

    pixi run test   (in this folder) -- a synthetic image, plus the BBBC039 image and
                    ground-truth mask committed in ../../tests/data (CC0).
"""

from pathlib import Path

import numpy as np
import pytest

from wavu.testing import FakeCtx, run_script

pytestmark = pytest.mark.cellpose

HERE = Path(__file__).parent
SCRIPT = HERE / "script.py"
DATA = HERE.parent.parent / "tests" / "data" / "BBBC039"


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


def bbbc039_labels(path):
    """Channel 0 of a BBBC039 mask is a 4-colouring; each nucleus is one connected component of one colour."""
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


def test_f1_against_bbbc039_ground_truth():
    import tifffile

    img = tifffile.imread(DATA / "A02_s1.tif")
    gt = bbbc039_labels(DATA / "A02_s1_mask.png")
    labels = run_script(SCRIPT, {"image": img}, {"use_gpu": False})["labels"]
    # True positives: ground-truth nuclei whose best-overlapping prediction has IoU > 0.5.
    gt_ids = [i for i in np.unique(gt) if i]
    tp = 0
    for i in gt_ids:
        m = gt == i
        ids, counts = np.unique(labels[m], return_counts=True)
        best = ids[np.argmax(counts)]
        if best and (m & (labels == best)).sum() / (m | (labels == best)).sum() > 0.5:
            tp += 1
    n_pred = int(len(np.unique(labels)) - 1)
    f1 = 2 * tp / (len(gt_ids) + n_pred)
    assert f1 > 0.7, f"F1 {f1:.2f} (TP {tp}, GT {len(gt_ids)}, predicted {n_pred})"
