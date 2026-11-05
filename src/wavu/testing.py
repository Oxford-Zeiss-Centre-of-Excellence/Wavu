"""Unit-test a Wavu script without a server or Fiji.

    from wavu.testing import FakeCtx, run_script

    def test_blur():
        ctx = FakeCtx()
        out = run_script("script.py", {"image": img}, {"sigma": 2.0}, ctx=ctx)
        assert out["blurred"].shape == img.shape
        assert ctx.progress_values[-1] == 1.0
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

from wavu.scripts import coerce_params, load_script, normalize_params
from wavu.types import Cancelled


class FakeCtx:
    """Stands in for the worker's ``ctx``: records logs and progress in lists."""

    def __init__(self, tmpdir: Path | str | None = None, cancel_after: int | None = None, meta: dict | None = None):
        self.tmpdir = Path(tmpdir) if tmpdir is not None else Path(tempfile.mkdtemp(prefix="wavu-test-"))
        self.meta: dict[str, dict[str, Any]] = dict(meta or {})
        self.messages: list[str] = []
        self.progress_values: list[float] = []
        self._cancel_after = cancel_after
        self._cancel_checks = 0
        self.cancel_requested = False

    def log(self, msg: Any) -> None:
        self.messages.append(str(msg))

    def progress(self, frac: float) -> None:
        self.progress_values.append(max(0.0, min(1.0, float(frac))))

    def cancel(self) -> None:
        """Simulate the user pressing Esc / Cancel in Fiji."""
        self.cancel_requested = True

    def cancelled(self) -> bool:
        self._cancel_checks += 1
        if self._cancel_after is not None and self._cancel_checks > self._cancel_after:
            self.cancel_requested = True
        return self.cancel_requested

    def check_cancelled(self) -> None:
        if self.cancelled():
            raise Cancelled()


def run_script(
    script: str | Path | ModuleType,
    inputs: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    ctx: FakeCtx | None = None,
) -> dict[str, Any]:
    """Call ``run`` the way the worker does: PARAMS defaults and type conversion applied."""
    if isinstance(script, ModuleType):
        schema = normalize_params(getattr(script, "PARAMS", {}))
        run = script.run
    else:
        info = load_script(Path(script))
        schema, run = info.params, info.module.run
    result = run(ctx or FakeCtx(), dict(inputs or {}), coerce_params(schema, params))
    return {} if result is None else result
