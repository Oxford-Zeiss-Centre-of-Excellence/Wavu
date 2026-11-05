"""Loops until cancelled (or 30 s)."""

import time

PARAMS = {}


def run(ctx, inputs, params):
    ctx.log("started")
    t0 = time.time()
    while time.time() - t0 < 30:
        if ctx.cancelled():
            ctx.log("saw cancel")
            return {}
        time.sleep(0.02)
    return {"finished": True}
