"""Logs, prints and reports progress."""

import helper_mod

PARAMS = {"steps": {"type": "int", "default": 3}}


def run(ctx, inputs, params):
    for i in range(params["steps"]):
        ctx.log(f"step {i}")
        ctx.progress((i + 1) / params["steps"])
    print("printed line")
    return {"answer": helper_mod.ANSWER}
