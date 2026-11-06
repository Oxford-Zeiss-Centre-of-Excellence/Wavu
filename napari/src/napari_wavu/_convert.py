"""napari layers <-> Wavu inputs and outputs. No Qt here, so it is easy to test."""

from __future__ import annotations

import re
from typing import Any

import numpy as np

# An integer image output whose name matches this opens as a Labels layer.
LABEL_NAME = re.compile(r"label|mask|seg|instance", re.IGNORECASE)


def layer_input(layer: Any) -> tuple[np.ndarray, dict[str, Any]]:
    """The array and metadata Wavu sends for an Image or Labels layer."""
    data = layer.data
    if getattr(layer, "multiscale", False):
        data = data[0]
    arr = np.asarray(data.compute() if hasattr(data, "compute") else data)
    meta: dict[str, Any] = {"title": layer.name}
    scale = tuple(float(s) for s in getattr(layer, "scale", ())[-2:])
    units = [str(u) for u in getattr(layer, "units", ())][-2:]
    if len(scale) == 2 and scale[0] == scale[1] and scale[0] != 1.0:
        if not units or all(u in ("micrometer", "um", "µm", "pixel") for u in units):
            meta["pixel_um"] = scale[0]
    if getattr(layer, "rgb", False):
        meta["axes"] = "YXS" if arr.ndim == 3 else None
    return arr, {k: v for k, v in meta.items() if v is not None}


def is_labels(name: str, arr: np.ndarray, meta: dict[str, Any]) -> bool:
    hint = str(meta.get("napari", "")).lower()
    if hint in ("labels", "image"):
        return hint == "labels"
    return np.issubdtype(arr.dtype, np.integer) and bool(LABEL_NAME.search(name))


def image_layer(name: str, arr: np.ndarray, meta: dict[str, Any]) -> tuple[Any, dict[str, Any], str]:
    """A napari LayerDataTuple for an image output: ``(data, kwargs, "image" | "labels")``."""
    kwargs: dict[str, Any] = {"name": name}
    px = meta.get("pixel_um")
    axes = str(meta.get("axes") or "")
    channel_axis = axes.index("C") if "C" in axes and len(axes) == arr.ndim else None
    spatial = arr.ndim - (1 if channel_axis is not None else 0)
    if px:
        kwargs["scale"] = (1.0,) * (spatial - 2) + (float(px), float(px))
    if is_labels(name, arr, meta):
        return arr, kwargs, "labels"
    if "S" in axes and arr.shape[-1] in (3, 4):
        kwargs["rgb"] = True
    elif channel_axis is not None:
        kwargs["channel_axis"] = channel_axis
        names = meta.get("channel_names")
        kwargs["name"] = [f"{name} [{c}]" for c in names] if names else name
    return arr, kwargs, "image"


def roi_polygons(path: Any) -> list[np.ndarray]:
    """ImageJ RoiSet zip -> polygons in napari (row, col) order. Needs ``roifile``."""
    import roifile

    polys = []
    for roi in roifile.roiread(str(path)) or []:
        rois = roi if isinstance(roi, list) else [roi]
        for r in rois:
            xy = np.asarray(r.coordinates(), dtype=float)
            if xy.ndim == 2 and len(xy) >= 2:
                polys.append(xy[:, ::-1])
    return polys


def output_layers(outputs: dict[str, Any], defaults: dict[str, Any] | None = None
                  ) -> tuple[list[tuple[Any, dict[str, Any], str]], list[str]]:
    """``wavu.client`` outputs -> (layer data tuples, messages for the log).

    ``defaults`` (e.g. the input's ``pixel_um``) apply to image outputs that do
    not set their own, so a plain returned array lands on top of its input.
    """
    layers: list[tuple[Any, dict[str, Any], str]] = []
    notes: list[str] = []
    for name, out in outputs.items():
        if out.kind == "image":
            layers.append(image_layer(name, np.asarray(out.value), {**(defaults or {}), **out.meta}))
        elif out.kind == "rois":
            try:
                polys = roi_polygons(out.value.path)
            except ImportError:
                notes.append(f"{name}: ROI set at {out.value.path} (install roifile to show it as shapes)")
                continue
            if polys:
                layers.append((polys, {"name": name, "shape_type": "polygon", "edge_color": "yellow",
                                       "face_color": "transparent", "edge_width": 1}, "shapes"))
        elif out.kind == "table":
            notes.append(f"{name}: table with {_len(out.value)} rows")
        elif out.kind == "file":
            notes.append(f"{name}: {out.value}")
        else:
            notes.append(f"{name} = {out.value}")
    return layers, notes


def table_rows(value: Any) -> tuple[list[str], list[list[Any]]]:
    """A DataFrame or list of dicts -> (columns, rows), for showing in a table widget."""
    if hasattr(value, "columns") and hasattr(value, "itertuples"):
        return [str(c) for c in value.columns], [list(r) for r in value.itertuples(index=False)]
    cols: list[str] = []
    for r in value:
        cols += [k for k in r if k not in cols]
    return cols, [[r.get(c, "") for c in cols] for r in value]


def _len(value: Any) -> int:
    try:
        return len(value)
    except TypeError:
        return 0
