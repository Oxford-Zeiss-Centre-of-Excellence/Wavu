"""Result figures for the pipeline guide pages, from real runs on the demo movie.

    pixi run -e napari python tools/make_results_figures.py OUT_GROOVY OUT_MACRO

OUT_GROOVY and OUT_MACRO are the output folders of the Groovy (TrackMate) and
macro (trackpy) versions of "Pipeline in Fiji" run on
examples/data/demo_timelapse.tif (tests/fiji/dag_counting.groovy / .ijm).
This script also runs the Python pipeline (examples/pipelines/dag_counting.py,
starts two Wavu workers) for the trackpy tracks. Writes to guide/assets/img/results/:

- counts.gif         left: the movie with trackpy track tails; right: cells
                     against time, growing frame by frame. Dashed grey = true
                     count, blue dots = measured cells (same for every method),
                     orange line = TrackMate lineages alive (tracks that may
                     branch at a division). No words, so one file serves all
                     languages; the pages carry the legend.
- tracks-compare.png the last frame with tracks: TrackMate (left), trackpy (right).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "guide" / "assets" / "img" / "results"
sys.path.insert(0, str(REPO / "examples" / "pipelines"))

# The demo movie's true number of cells per frame (tools/make_demo_timelapse.py).
TRUTH = [25, 25, 25, 25, 25, 25, 26, 26, 26, 25, 25, 25, 26, 26, 26, 26, 26, 27, 27, 28,
         28, 28, 28, 29, 29, 29, 29, 29, 29, 29]
GREY, BLUE, ORANGE = "#546e7a", "#1565c0", "#ef6c00"
TAIL = 8   # frames of track tail drawn behind each nucleus


def lineages_per_frame(trackmate_tracks: pd.DataFrame, n_frames: int) -> list[int]:
    """TrackMate lineages alive in each frame (a lineage branches at a division)."""
    t = trackmate_tracks
    return [int(((t.first_frame <= f) & (t.last_frame >= f)).sum()) for f in range(n_frames)]


def counts_gif(movie, tracks, cells, lineages, minutes, path: Path) -> None:
    lo, hi = np.percentile(movie, (1, 99.8))
    colours = {p: c for p, c in zip(sorted(tracks.particle.unique()),
                                    np.random.default_rng(3).uniform(0.15, 1, (10_000, 3)))}
    frames = []
    for f in range(len(movie)):
        fig = Figure(figsize=(7.2, 3.3), dpi=100, layout="constrained", facecolor="white")
        a, b = fig.subplots(1, 2, width_ratios=[1, 1.25])
        a.imshow(movie[f], cmap="gray", vmin=lo, vmax=hi)
        recent = tracks[(tracks.frame <= f) & (tracks.frame > f - TAIL)]
        for p, g in recent.groupby("particle"):
            if g.frame.max() == f:
                a.plot(g.x, g.y, color=colours[p], lw=1.5)
        a.set_axis_off()
        b.plot(minutes, TRUTH, color=GREY, lw=1.5, ls="--")
        b.plot(minutes[: f + 1], lineages[: f + 1], color=ORANGE, lw=2)
        b.plot(minutes[: f + 1], cells[: f + 1], "o", color=BLUE, ms=4)
        b.set_xlim(-3, minutes[-1] + 3)
        b.set_ylim(22.5, 30.5)
        b.set_xlabel("t (min)")
        b.set_ylabel("n")
        b.grid(alpha=0.25)
        for s in ("top", "right"):
            b.spines[s].set_visible(False)
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        frames.append(Image.fromarray(np.asarray(canvas.buffer_rgba())[..., :3]))
    pal = frames[-1].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    frames = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    frames[0].save(path, save_all=True, append_images=frames[1:] + [frames[-1]] * 6,
                   duration=[250] * len(frames) + [250] * 6, loop=0, optimize=True)


def tracks_compare(png_trackmate: Path, png_trackpy: Path, path: Path, gap: int = 8) -> None:
    a, b = Image.open(png_trackmate).convert("RGB"), Image.open(png_trackpy).convert("RGB")
    scale = 2
    a, b = (im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST) for im in (a, b))
    out = Image.new("RGB", (a.width + b.width + gap, max(a.height, b.height)), "white")
    out.paste(a, (0, 0))
    out.paste(b, (a.width + gap, 0))
    out.save(path, optimize=True)


def main(out_groovy: Path, out_macro: Path) -> None:
    from dag_counting import FRAME_MIN, analyse

    OUT.mkdir(parents=True, exist_ok=True)
    movie, _labels, tracks, counts, _ = analyse()
    minutes = np.arange(len(movie)) * FRAME_MIN
    lineages = lineages_per_frame(pd.read_csv(out_groovy / "demo_timelapse-tracks.csv"), len(movie))
    counts_gif(movie, tracks, list(counts["cells"]), lineages, minutes, OUT / "counts.gif")
    tracks_compare(out_groovy / "demo_timelapse-tracks.png", out_macro / "demo_timelapse-tracks.png",
                   OUT / "tracks-compare.png")
    for p in sorted(OUT.iterdir()):
        print(f"wrote {p} ({p.stat().st_size // 1024} KiB)")
    print("lineages:", lineages)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
