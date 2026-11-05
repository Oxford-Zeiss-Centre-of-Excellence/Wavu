"""Gaussian blur -- the Wavu example script.

Smooths the chosen image with a Gaussian of the given width (in pixels) and
returns the result, which Fiji opens as a new image.
"""

import numpy as np
from scipy import ndimage

# Each entry becomes a field in Fiji's dialog. Types: float, int, str, bool,
# choice (needs "choices"), image (Fiji lets the user pick an open image).
PARAMS = {
    "image": {"type": "image", "label": "Image"},
    "sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
    "mode": {"type": "choice", "default": "reflect", "choices": ["reflect", "nearest", "constant"], "label": "Edges"},
    "keep_dtype": {"type": "bool", "default": True, "label": "Keep the input's pixel type"},
}


def run(ctx, inputs, params):
    image = np.asarray(inputs["image"])
    ctx.log(f"Blurring a {image.shape} {image.dtype} image with sigma={params['sigma']}")

    # Blur plane by plane so progress and Cancel work on stacks too.
    planes = image.reshape((-1,) + image.shape[-2:])
    out = np.empty(planes.shape, dtype=np.float32)
    for i, plane in enumerate(planes):
        if ctx.cancelled():
            ctx.log("Cancelled")
            return {}
        out[i] = ndimage.gaussian_filter(plane.astype(np.float32), params["sigma"], mode=params["mode"])
        ctx.progress((i + 1) / len(planes))
    out = out.reshape(image.shape)

    if params["keep_dtype"] and np.issubdtype(image.dtype, np.integer):
        info = np.iinfo(image.dtype)
        out = np.clip(np.rint(out), info.min, info.max).astype(image.dtype)
    return {"blurred": out}
