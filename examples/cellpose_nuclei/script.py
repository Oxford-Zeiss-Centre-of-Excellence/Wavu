"""Cellpose nuclei -- segment nuclei (DAPI/Hoechst-like images) with Cellpose's nuclei model.

Returns a label image (one integer per nucleus) and the outlines as an
ImageJ RoiSet, which Fiji opens in the ROI Manager.
"""

from pathlib import Path

import numpy as np

import wavu

PARAMS = {
    "image": {"type": "image", "label": "Nuclei image"},
    "diameter": {"type": "float", "default": 0.0, "label": "Nucleus diameter in pixels (0 = estimate)"},
    "flow_threshold": {"type": "float", "default": 0.4, "label": "Flow threshold"},
    "cellprob_threshold": {"type": "float", "default": 0.0, "label": "Cell probability threshold"},
    "use_gpu": {"type": "bool", "default": True, "label": "Use GPU if available (CUDA / Apple MPS)"},
}


def run(ctx, inputs, params):
    import roifile
    from cellpose import models, utils

    image = np.asarray(inputs["image"])
    if image.ndim != 2:
        raise ValueError(
            f"expected a single 2-D nuclei channel, got shape {image.shape} -- pick one channel/plane in Fiji first"
        )
    ctx.log(f"Cellpose nuclei on a {image.shape} {image.dtype} image")
    ctx.progress(0.05)

    model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
    ctx.log(f"Model on {model.device}")
    if ctx.cancelled():
        return {}
    ctx.progress(0.2)

    masks, _flows, _styles, diams = model.eval(
        image,
        diameter=params["diameter"] or None,
        channels=[0, 0],
        flow_threshold=params["flow_threshold"],
        cellprob_threshold=params["cellprob_threshold"],
    )
    ctx.progress(0.9)
    n = int(masks.max())
    ctx.log(f"Found {n} nuclei (diameter {float(np.atleast_1d(diams)[0]):.1f} px)")

    rois = []
    for i, outline in enumerate(utils.outlines_list(masks), start=1):
        if len(outline) < 3:
            continue
        roi = roifile.ImagejRoi.frompoints(outline)  # cellpose outlines are (x, y) pairs
        roi.name = f"nucleus-{i:04d}"
        rois.append(roi)
    ctx.progress(1.0)

    out = {"labels": masks.astype(np.uint16 if n < 65536 else np.int32), "count": n}
    if rois:
        zip_path = Path(ctx.tmpdir) / "RoiSet.zip"
        zip_path.unlink(missing_ok=True)
        roifile.roiwrite(zip_path, rois)
        out["rois"] = wavu.RoiSet(zip_path)
    return out
