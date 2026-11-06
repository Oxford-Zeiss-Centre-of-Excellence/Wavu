"""Write examples/data/demo_timelapse.tif: a small synthetic nuclei time-lapse (CC0).

    pixi run demo-data

30 frames of 256 x 256 uint16 (ImageJ hyperstack, axes TYX, 0.65 um pixels,
5 min between frames). About 25 bright round nuclei drift with small random
walks; a few divide (one blob becomes two), one leaves the field of view and
one enters, so the number of nuclei changes over time. Deterministic (fixed
seed), numpy + tifffile only. Made by this repository; no real data involved,
dedicated to the public domain (CC0).

The true number of nuclei per frame (centre inside the image) is printed and
stored in the TIFF's ImageJ "Info" property.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np

T, H, W = 30, 256, 256
N_START = 25
PIXEL_UM = 0.65
FRAME_MIN = 5.0
BACKGROUND = 100.0
NOISE_SD = 25.0
SEED = 7
# frame -> number of nuclei that divide at that frame
DIVISIONS = {6: 1, 12: 1, 17: 1, 23: 1}
LEAVER_EXITS_BY = 12          # one nucleus near the edge drifts out of the field of view
ENTER_FRAME = 15               # one nucleus drifts in from the left edge

OUT = Path(__file__).resolve().parents[1] / "examples" / "data" / "demo_timelapse.tif"


@dataclass
class Nucleus:
    y: float
    x: float
    r: float
    brightness: float
    vy: float = 0.0  # steady drift (px/frame) on top of the random walk
    vx: float = 0.0


def place_start(rng: np.random.Generator) -> list[Nucleus]:
    cells: list[Nucleus] = []
    while len(cells) < N_START:
        y, x = rng.uniform(24, H - 24), rng.uniform(24, W - 24)
        if all((c.y - y) ** 2 + (c.x - x) ** 2 > 34**2 for c in cells):
            cells.append(Nucleus(y, x, rng.uniform(6.0, 8.0), rng.uniform(900, 1500)))
    return cells


def separate(cells: list[Nucleus], gap: float = 6.0) -> None:
    """Push apart nuclei that came too close, so each stays a separate blob."""
    for _ in range(5):
        for i, a in enumerate(cells):
            for b in cells[i + 1:]:
                dy, dx = b.y - a.y, b.x - a.x
                d = max(np.hypot(dy, dx), 1e-6)
                need = a.r + b.r + gap
                if d < need:
                    push = (need - d) / 2
                    a.y -= dy / d * push; a.x -= dx / d * push
                    b.y += dy / d * push; b.x += dx / d * push


def render(cells: list[Nucleus], rng: np.random.Generator) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.full((H, W), BACKGROUND, np.float32)
    for c in cells:
        d = np.hypot(yy - c.y, xx - c.x)
        # A disc with a soft (Gaussian-blur-like) edge, slightly brighter in the middle.
        edge = 1.0 / (1.0 + np.exp(np.minimum((d - c.r) / 1.2, 50.0)))
        img += c.brightness * edge * (1.0 + 0.15 * np.exp(-(d / c.r) ** 2))
    img += rng.normal(0.0, NOISE_SD, img.shape).astype(np.float32)
    return np.clip(img, 0, 65535).astype(np.uint16)


def inside(c: Nucleus) -> bool:
    return 0 <= c.y < H and 0 <= c.x < W


def simulate() -> tuple[np.ndarray, list[int]]:
    rng = np.random.default_rng(SEED)
    cells = place_start(rng)
    # The nucleus closest to the right edge leaves the field of view.
    leaver = max(cells, key=lambda c: c.x)
    leaver.vx = (W + 2 * leaver.r - leaver.x) / LEAVER_EXITS_BY
    frames, counts = [], []
    for t in range(T):
        if t == ENTER_FRAME:
            cells.append(Nucleus(rng.uniform(60, H - 60), -12.0, 7.0, 1200.0, vx=3.0))
        for _ in range(DIVISIONS.get(t, 0)):
            candidates = [c for c in cells if inside(c) and 30 < c.x < W - 30 and 30 < c.y < H - 30 and c.vx == 0]
            mother = candidates[int(rng.integers(len(candidates)))]
            angle = rng.uniform(0, np.pi)
            r = mother.r * 0.85
            off = r + 4.0
            cells.remove(mother)
            for s in (-1, 1):
                cells.append(Nucleus(mother.y + s * off * np.sin(angle), mother.x + s * off * np.cos(angle),
                                     r, mother.brightness))
        for c in cells:
            if t > 0:
                c.y += c.vy + rng.normal(0, 1.0)
                c.x += c.vx + rng.normal(0, 1.0)
            if c.vx == 0:  # keep the ordinary nuclei inside the field of view
                c.y = float(np.clip(c.y, 12, H - 12))
                c.x = float(np.clip(c.x, 12, W - 12))
        separate(cells)
        frames.append(render(cells, rng))
        counts.append(sum(inside(c) for c in cells))
    return np.stack(frames), counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    import tifffile

    stack, counts = simulate()
    info = (
        "Synthetic demo time-lapse made by tools/make_demo_timelapse.py (Wavu). CC0 / public domain.\n"
        f"{T} frames, {H}x{W}, uint16, {PIXEL_UM} um/pixel, {FRAME_MIN:g} min/frame.\n"
        "True nuclei per frame (centre inside the image): " + " ".join(map(str, counts))
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(
        args.out, stack, imagej=True,
        resolution=(1.0 / PIXEL_UM, 1.0 / PIXEL_UM),
        metadata={"axes": "TYX", "unit": "um", "finterval": FRAME_MIN, "tunit": "min", "Info": info},
    )
    print(f"wrote {args.out} ({args.out.stat().st_size / 1e6:.2f} MB)")
    print("nuclei per frame:", " ".join(map(str, counts)))


if __name__ == "__main__":
    main()
