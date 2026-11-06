"""Minimal dynamic cell counting, as a pipeline in Python and napari.

    pixi run -e napari python examples/pipelines/dag_counting.py              # opens napari
    pixi run -e napari python examples/pipelines/dag_counting.py --no-viewer  # counts.csv + plot.png

Five steps; two run in Wavu workers, each in its own pixi environment:

    1. load       (native)  the time-lapse, with tifffile
    2. segment    (Wavu)    examples/segment_frames  -- scikit-image
    3. track      (Wavu)    examples/track_trackpy   -- trackpy
    4. tabulate   (native)  cells per frame, tracks, new tracks, with pandas
    5. visualise  (native)  napari layers + a matplotlib plot docked in the viewer

This environment (the napari one) needs no trackpy and runs no segmentation
code: those live in the two script folders, each with its own packages.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import tifffile

from wavu.client import Worker

REPO = Path(__file__).resolve().parents[2]
MOVIE = REPO / "examples" / "data" / "demo_timelapse.tif"
SEGMENT = REPO / "examples" / "segment_frames"
TRACK = REPO / "examples" / "track_trackpy"
PIXEL_UM = 0.65        # micrometres per pixel
FRAME_MIN = 5.0        # minutes between frames


def analyse(movie_path: Path = MOVIE, log=print):
    # 1. Load (native)
    movie = tifffile.imread(movie_path)                                   # (T, Y, X)
    log(f"loaded {movie_path.name}: {movie.shape}")

    # 2 + 3. Segment, then track: two kitchens, two environments
    with Worker.start(SEGMENT, on_log=log) as seg, Worker.start(TRACK, on_log=log) as trk:
        res = seg.run("script", {"sigma": 2.0, "threshold": "otsu", "min_area": 30},
                      {"image": movie}, meta={"image": {"pixel_um": PIXEL_UM}})
        labels = res.outputs["labels"].value                              # uint16 (T, Y, X)
        detections = res.outputs["detections"].value                      # frame, label, y, x, area, ...
        res = trk.run("script", {"search_range": 10.0, "memory": 2},
                      {"detections": detections})
        tracks = res.outputs["tracks"].value                              # ... plus 'particle'

    # 4. Tabulate (native)
    counts = (detections.groupby("frame").size()
              .reindex(range(len(movie)), fill_value=0).rename("cells").reset_index())
    counts["minutes"] = counts["frame"] * FRAME_MIN
    per_track = tracks.groupby("particle")["frame"].agg(start="min", end="max", length="size")
    # A track that starts after frame 0 is a cell that was not there before:
    # a daughter after a division, or a cell drifting in from the edge (or a
    # tracking break). We count them; we do not claim which is which.
    new_tracks = per_track[per_track["start"] > 0]
    summary = {
        "frames": len(movie),
        "tracks": int(tracks["particle"].nunique()),
        "new_tracks": len(new_tracks),
        "median_track_length": float(per_track["length"].median()),
    }
    return movie, labels, tracks, counts, summary


def plot_counts(counts: pd.DataFrame):
    from matplotlib.figure import Figure

    fig = Figure(figsize=(5, 3), layout="constrained")
    ax = fig.add_subplot()
    ax.plot(counts["minutes"], counts["cells"], marker="o", markersize=3, color="#2e7d32")
    ax.set_xlabel("time (min)")
    ax.set_ylabel("cells")
    ax.set_title("Cells per frame")
    ax.grid(alpha=0.3)
    return fig


def show_in_napari(viewer, movie, labels, tracks, counts):
    """Step 5: the script decides names, colours and tail length."""
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

    scale = (1, PIXEL_UM, PIXEL_UM)                                        # t, y, x
    viewer.add_image(movie, name="nuclei", scale=scale, colormap="gray")
    viewer.add_labels(labels, name="segmentation", scale=scale, opacity=0.4)
    data = tracks[["particle", "frame", "y", "x"]].to_numpy(float)         # napari: [id, t, y, x]
    viewer.add_tracks(data, name="tracks", scale=scale, tail_length=10,
                      tail_width=2, colormap="turbo")
    canvas = FigureCanvasQTAgg(plot_counts(counts))
    canvas.setMinimumSize(320, 220)
    viewer.window.add_dock_widget(canvas, name="Cells per frame", area="right")
    return canvas


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-viewer", action="store_true", help="no napari: save counts.csv and plot.png")
    ap.add_argument("--out", type=Path, default=Path("dag_counting_out"), help="output folder (--no-viewer)")
    args = ap.parse_args(argv)

    movie, labels, tracks, counts, s = analyse()
    print(f"{s['frames']} frames, {s['tracks']} tracks, {s['new_tracks']} start after frame 0, "
          f"median length {s['median_track_length']:.0f} frames")

    if args.no_viewer:
        args.out.mkdir(parents=True, exist_ok=True)
        counts.to_csv(args.out / "counts.csv", index=False)
        plot_counts(counts).savefig(args.out / "plot.png", dpi=120)
        print(f"WAVU_DAG_PY_OK frames={s['frames']} tracks={s['tracks']} "
              f"counts={','.join(map(str, counts['cells']))}")
        return

    import napari

    viewer = napari.Viewer(title="Cell counting pipeline")
    show_in_napari(viewer, movie, labels, tracks, counts)
    napari.run()


if __name__ == "__main__":
    main()
