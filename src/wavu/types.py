"""Small value types a script may return (or receive) besides plain arrays."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class Cancelled(Exception):
    """Raise (or let ``ctx.check_cancelled()`` raise) to stop a job early."""


@dataclass
class RoiSet:
    """An ImageJ RoiSet ``.zip`` (as written by ImageJ's ROI Manager or roifile).

    Return one from ``run`` and Fiji opens it in the ROI Manager.
    """

    path: Path

    def __post_init__(self) -> None:
        self.path = Path(self.path)


# Short alias -- the contract docs say "wavu.Roi-style paths".
Roi = RoiSet


@dataclass
class Image:
    """An array plus the metadata Fiji should attach when it opens it.

    Returning a bare numpy array is fine; wrap it in ``Image`` only when you
    want to set the pixel size, axis order or channel names explicitly.
    """

    data: Any
    pixel_um: float | None = None
    channel_names: list[str] | None = None
    axes: str | None = None  # e.g. "YX", "ZYX", "CYX" -- ImageJ order TZCYX
    extra: dict[str, Any] = field(default_factory=dict)

    def meta(self) -> dict[str, Any]:
        m: dict[str, Any] = dict(self.extra)
        if self.pixel_um is not None:
            m["pixel_um"] = float(self.pixel_um)
        if self.channel_names is not None:
            m["channel_names"] = list(self.channel_names)
        if self.axes is not None:
            m["axes"] = self.axes
        return m
