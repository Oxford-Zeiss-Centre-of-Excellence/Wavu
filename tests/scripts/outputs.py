"""Returns one of every output kind."""

from pathlib import Path

import numpy as np

import wavu

PARAMS = {}


def run(ctx, inputs, params):
    import pandas as pd
    import roifile

    labels = np.zeros((20, 30), dtype=np.int64)
    labels[2:6, 3:9] = 1
    roi = roifile.ImagejRoi.frompoints([[3, 2], [9, 2], [9, 6], [3, 6]])
    roi.name = "cell-1"
    zip_path = Path(ctx.tmpdir) / "RoiSet.zip"
    roifile.roiwrite(zip_path, [roi])
    return {
        "labels": labels,
        "big": wavu.Image(np.ones((4, 40, 50), dtype=np.float64), pixel_um=0.5, axes="ZYX"),
        "table": pd.DataFrame({"label": [1], "area": [24.0]}),
        "rows": [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}],
        "rois": wavu.RoiSet(zip_path),
        "count": np.int64(1),
    }
