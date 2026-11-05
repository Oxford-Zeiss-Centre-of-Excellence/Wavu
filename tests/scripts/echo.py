"""Returns its input image and params unchanged."""

PARAMS = {
    "image": {"type": "image"},
    "factor": {"type": "int", "default": 1},
    "note": {"type": "str", "default": "hi", "label": "A note"},
    "flag": {"type": "bool", "default": False},
    "which": {"type": "choice", "choices": ["a", "b"], "default": "b"},
    "sigma": {"type": "float", "default": 0.5},
}


def run(ctx, inputs, params):
    img = inputs["image"] * params["factor"]
    return {"image": img, "params": f"{params['note']}|{params['flag']}|{params['which']}|{params['sigma']}",
            "meta": str(ctx.meta.get("image", {}).get("pixel_um"))}
