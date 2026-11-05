"""Tests for script.py -- run with `pixi run test` in this folder. No Fiji needed."""

from pathlib import Path

import numpy as np

from wavu.testing import FakeCtx, run_script

SCRIPT = Path(__file__).with_name("script.py")


def test_blur_smooths_a_single_bright_pixel():
    img = np.zeros((32, 32), dtype=np.uint16)
    img[16, 16] = 1000
    ctx = FakeCtx()
    out = run_script(SCRIPT, {"image": img}, {"sigma": 2.0}, ctx=ctx)

    blurred = out["blurred"]
    assert blurred.shape == img.shape
    assert blurred.dtype == np.uint16  # keep_dtype defaults to True
    assert blurred[16, 16] < 1000 and blurred[16, 18] > 0
    assert ctx.progress_values[-1] == 1.0
    assert any("sigma=2.0" in m for m in ctx.messages)


def test_stack_is_blurred_plane_by_plane():
    stack = np.random.default_rng(0).random((3, 16, 16)).astype(np.float32)
    out = run_script(SCRIPT, {"image": stack}, {"sigma": 1, "keep_dtype": False})
    assert out["blurred"].shape == (3, 16, 16)
    assert out["blurred"].std() < stack.std()


def test_cancel_stops_early():
    stack = np.zeros((5, 8, 8), dtype=np.uint8)
    ctx = FakeCtx(cancel_after=2)
    assert run_script(SCRIPT, {"image": stack}, {}, ctx=ctx) == {}
    assert len(ctx.progress_values) == 2
