"""Inputs and outputs on the wire: inline base64 arrays or file paths."""

from __future__ import annotations

import base64
import csv
from pathlib import Path
from typing import Any

import numpy as np

from wavu.types import Image, RoiSet

# Arrays at or below this size travel inline as base64 JSON; bigger ones (and
# anything above 3-D) go through a TIFF in the job's temp folder. Base64 adds a
# third on top, so keep it modest -- this is a bridge for small data.
INLINE_LIMIT = 4 * 1024 * 1024

TIFF_SUFFIXES = {".tif", ".tiff"}


def imagej_array(arr: Any) -> np.ndarray:
    """Convert to a dtype ImageJ can show: uint8, uint16 or float32."""
    a = np.asarray(arr)
    if a.dtype == bool:
        return a.astype(np.uint8) * 255
    if a.dtype in (np.uint8, np.uint16, np.float32):
        return np.ascontiguousarray(a)
    if np.issubdtype(a.dtype, np.integer):
        if a.size == 0 or (a.min() >= 0 and a.max() <= 65535):
            return a.astype(np.uint16)
        return a.astype(np.float32)
    if np.issubdtype(a.dtype, np.floating):
        return a.astype(np.float32)
    raise TypeError(f"cannot hand a {a.dtype} array to Fiji")


def encode_array(arr: np.ndarray, meta: dict | None = None) -> dict[str, Any]:
    a = np.ascontiguousarray(arr)
    le = a.astype(a.dtype.newbyteorder("<"), copy=False)
    return {
        "dtype": a.dtype.name,
        "shape": list(a.shape),
        "data": base64.b64encode(le.tobytes()).decode("ascii"),
        "meta": dict(meta or {}),
    }


def decode_array(spec: dict[str, Any]) -> np.ndarray:
    try:
        dtype = np.dtype(spec["dtype"]).newbyteorder("<")
        shape = tuple(int(s) for s in spec["shape"])
        raw = base64.b64decode(spec["data"])
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"bad inline array: {e}") from None
    expected = int(np.prod(shape)) * dtype.itemsize
    if len(raw) != expected:
        raise ValueError(f"inline array has {len(raw)} bytes, shape {shape} {dtype} needs {expected}")
    return np.frombuffer(raw, dtype=dtype).reshape(shape).astype(dtype.newbyteorder("="))


def read_table(path: Path) -> Any:
    try:
        import pandas as pd
    except ImportError:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    return pd.read_csv(path)


def decode_input(spec: Any) -> tuple[Any, dict[str, Any]]:
    """One entry of a /run ``inputs`` dict -> (value for the script, meta)."""
    if not isinstance(spec, dict):
        raise ValueError("each input must be a JSON object")
    meta = dict(spec.get("meta") or {})
    if "data" in spec:
        return decode_array(spec), meta
    if "path" in spec:
        p = Path(spec["path"])
        if not p.exists():
            raise ValueError(f"input file not found: {p}")
        suffix = p.suffix.lower()
        if suffix in TIFF_SUFFIXES:
            import tifffile

            return tifffile.imread(p), meta
        if suffix == ".csv":
            return read_table(p), meta
        if suffix == ".zip":
            return RoiSet(p), meta
        return p, meta  # OME-Zarr folders and anything else: the script opens it
    raise ValueError("an input needs either 'data' (inline array) or 'path'")


def _write_tiff(path: Path, arr: np.ndarray, meta: dict[str, Any]) -> None:
    import tifffile

    kwargs: dict[str, Any] = {"imagej": True}
    md: dict[str, Any] = {}
    axes = meta.get("axes")
    if isinstance(axes, str) and len(axes) == arr.ndim and set(axes) <= set("TZCYXS"):
        md["axes"] = axes
    px = meta.get("pixel_um")
    if px:
        kwargs["resolution"] = (1.0 / float(px), 1.0 / float(px))
        md["unit"] = "um"
    if md:
        kwargs["metadata"] = md
    tifffile.imwrite(path, arr, **kwargs)


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    for r in rows:
        for k in r:
            if k not in columns:
                columns.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    return columns


def _safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name) or "output"


def encode_output(name: str, value: Any, out_dir: Path, inline_limit: int = INLINE_LIMIT) -> dict[str, Any]:
    """One returned value -> a JSON description the Fiji client knows how to open."""
    out_dir = Path(out_dir)
    if isinstance(value, Image):
        arr, meta = value.data, value.meta()
    elif isinstance(value, np.ndarray):
        arr, meta = value, {}
    else:
        arr = None
    if arr is not None:
        a = imagej_array(arr)
        if a.ndim < 2:
            raise TypeError(f"output {name!r}: images need at least 2 dimensions, got shape {a.shape}")
        rgb = "S" in str(meta.get("axes") or "")  # RGB samples: let ImageJ's TIFF reader handle them
        if a.nbytes <= inline_limit and a.ndim <= 3 and not rgb:
            return {"kind": "image", **encode_array(a, meta)}
        path = out_dir / f"{_safe_name(name)}.tif"
        _write_tiff(path, a, meta)
        return {"kind": "image", "path": str(path), "dtype": a.dtype.name, "shape": list(a.shape), "meta": meta}
    if isinstance(value, RoiSet):
        return {"kind": "rois", "path": str(Path(value.path).resolve())}
    if hasattr(value, "to_csv") and hasattr(value, "columns"):  # pandas DataFrame, duck-typed
        path = out_dir / f"{_safe_name(name)}.csv"
        value.to_csv(path, index=False)
        return {"kind": "table", "path": str(path), "columns": [str(c) for c in value.columns]}
    if isinstance(value, list) and value and all(isinstance(r, dict) for r in value):
        path = out_dir / f"{_safe_name(name)}.csv"
        cols = _write_rows(path, value)
        return {"kind": "table", "path": str(path), "columns": cols}
    if isinstance(value, Path):
        return {"kind": "file", "path": str(value.resolve())}
    if value is None or isinstance(value, (bool, int, float, str)):
        return {"kind": "value", "value": value}
    if isinstance(value, (np.integer, np.floating)):
        return {"kind": "value", "value": value.item()}
    raise TypeError(
        f"output {name!r}: don't know how to return a {type(value).__name__} "
        "(use a numpy array, wavu.Image, DataFrame/list of dicts, wavu.RoiSet, Path or a plain value)"
    )
