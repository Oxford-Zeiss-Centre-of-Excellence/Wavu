"""Always fails."""

PARAMS = {}


def run(ctx, inputs, params):
    raise RuntimeError("kaboom")
