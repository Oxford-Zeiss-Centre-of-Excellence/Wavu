"""Gaussian blur, optionally with a label image."""

import numpy as np

PARAMS = {
    "image": {"type": "image"},
    "sigma": {"type": "float", "default": 1.0},
    "label_it": {"type": "bool", "default": False, "label": "Also return labels"},
}


def run(ctx, inputs, params):
    from scipy import ndimage

    ctx.log(f"pixel size {ctx.meta['image'].get('pixel_um')}")
    ctx.progress(0.5)
    out = ndimage.gaussian_filter(inputs["image"].astype(np.float32), params["sigma"])
    result = {"blurred": out}
    if params["label_it"]:
        result["labels"] = (out > out.mean()).astype(np.uint16)
    return result
