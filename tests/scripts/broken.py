"""Fails at import time."""

import this_module_does_not_exist_anywhere  # noqa: F401


def run(ctx, inputs, params):
    return {}
