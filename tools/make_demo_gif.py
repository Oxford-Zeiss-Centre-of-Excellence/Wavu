"""Animated GIF of the demo time-lapse, for the guide.

    pixi run -e napari python tools/make_demo_gif.py

Reads examples/data/demo_timelapse.tif (make it with `pixi run demo-data`) and
writes guide/assets/img/demo-timelapse.gif: 8-bit grey, contrast stretched over
the whole movie, 200 ms per frame, looping.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "examples" / "data" / "demo_timelapse.tif"
OUT = REPO / "guide" / "assets" / "img" / "demo-timelapse.gif"


def main() -> None:
    movie = tifffile.imread(SRC).astype(np.float32)          # (T, Y, X)
    lo, hi = np.percentile(movie, (1, 99.8))
    frames8 = np.clip((movie - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
    frames8 = (frames8 // 8) * 8 + 4                         # 32 grey levels: a much smaller GIF
    frames = [Image.fromarray(f, mode="L") for f in frames8]
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=200, loop=0, optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KiB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
