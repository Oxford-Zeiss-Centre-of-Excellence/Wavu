"""A napari viewer *model* (layers, add_image, ...) without an OpenGL canvas.

The widget only uses the layer model and, for tables, window.add_dock_widget,
so the tests run on machines without OpenGL (CI, Windows offscreen).
"""

from __future__ import annotations

import pytest


class _Window:
    def __init__(self) -> None:
        self.docked: list[tuple[object, dict]] = []

    def add_dock_widget(self, widget, **kw):
        self.docked.append((widget, kw))
        return widget


class _Viewer:
    """ViewerModel plus a stand-in window (ViewerModel itself takes no new attributes)."""

    def __init__(self) -> None:
        from napari.components import ViewerModel

        self._model = ViewerModel()
        self.window = _Window()

    def __getattr__(self, name):
        return getattr(self._model, name)


@pytest.fixture
def viewer(qtbot):
    return _Viewer()
