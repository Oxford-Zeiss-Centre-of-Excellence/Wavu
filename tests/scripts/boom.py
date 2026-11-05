"""Always fails."""

PARAMS = {}


def run(ctx, inputs, params):
    ctx.log("about to fail")
    raise RuntimeError("kaboom from script")
