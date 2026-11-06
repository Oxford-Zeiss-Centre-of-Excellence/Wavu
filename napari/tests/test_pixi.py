"""The real path: wavu.client starts Wavu's template through `pixi run`, from inside this pixi env.

Uses the template of this repository (templates/wavu-script). Slow the first time.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytestmark = [pytest.mark.pixi_env, pytest.mark.timeout(1800)]

TEMPLATE = Path(__file__).resolve().parents[2] / "templates" / "wavu-script"


def test_widget_runs_the_template_in_its_own_env(viewer, qtbot):
    from wavu.client import find_pixi

    from napari_wavu._widget import WavuWidget

    if not TEMPLATE.is_dir():
        pytest.skip(f"no template at {TEMPLATE}")
    if find_pixi() is None:
        pytest.skip("pixi not found")
    img = np.zeros((16, 16), np.uint8)
    img[8, 8] = 200
    viewer.add_image(img, name="spot")
    w = WavuWidget(viewer)
    try:
        w._folder.value = TEMPLATE
        w._start.changed.emit(True)
        qtbot.waitUntil(lambda: bool(w._script.choices) or "Error" in w._log.value, timeout=1_500_000)
        assert "Error" not in w._log.value, w._log.value
        w._script.value = "script"
        w._params["sigma"].value = 1.5
        w._run.changed.emit(True)
        qtbot.waitUntil(lambda: "Done." in w._log.value or "Error" in w._log.value, timeout=120_000)
        assert "Error" not in w._log.value, w._log.value
        out = viewer.layers["blurred"].data
        assert 0 < out[8, 8] < 200
    finally:
        w.stop_all()
