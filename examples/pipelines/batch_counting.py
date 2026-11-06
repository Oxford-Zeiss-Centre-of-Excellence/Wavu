"""Batch: the dag_counting pipeline for every time-lapse in a folder.

    pixi run -e napari python examples/pipelines/batch_counting.py <folder> [<output folder>]
"""
import sys
from pathlib import Path

import pandas as pd
import tifffile
from matplotlib.figure import Figure

from dag_counting import FRAME_MIN, PIXEL_UM, SEGMENT, TRACK
from wavu.client import JobCancelled, Worker


def analyse_one(movie_path, seg, trk):
    """Steps 1-4 of dag_counting.analyse(), with workers that are already running."""
    movie = tifffile.imread(movie_path)
    res = seg.run("script", {"sigma": 2.0, "threshold": "otsu", "min_area": 30},
                  {"image": movie}, meta={"image": {"pixel_um": PIXEL_UM}})
    detections = res.outputs["detections"].value
    res = trk.run("script", {"search_range": 10.0, "memory": 2},
                  {"detections": detections})
    tracks = res.outputs["tracks"].value
    counts = (detections.groupby("frame").size()
              .reindex(range(len(movie)), fill_value=0).rename("cells").reset_index())
    counts["minutes"] = counts["frame"] * FRAME_MIN
    per_track = tracks.groupby("particle")["frame"].agg(start="min", end="max", length="size")
    row = {
        "frames": len(movie),
        "first_count": int(counts["cells"].iloc[0]),
        "last_count": int(counts["cells"].iloc[-1]),
        "mean_cells": float(counts["cells"].mean()),
        "tracks": int(tracks["particle"].nunique()),
        "new_tracks": int((per_track["start"] > 0).sum()),
    }
    return counts, row


def main(folder: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(folder.glob("*.tif"))
    rows, curves = [], {}
    with Worker.start(SEGMENT, on_log=print) as seg, Worker.start(TRACK, on_log=print) as trk:
        for i, path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] {path.name}")
            try:
                counts, row = analyse_one(path, seg, trk)
            except JobCancelled:
                raise                                   # cancelled: stop the whole batch
            except Exception as e:                      # one bad file: log it, go on
                print(f"  skipped {path.name}: {e}")
                rows.append({"file": path.name, "error": str(e).split("\n")[0]})
                continue
            counts.to_csv(out / f"{path.stem}-counts.csv", index=False)
            rows.append({"file": path.name, **row})
            curves[path.stem] = counts

    summary = pd.DataFrame(rows)
    summary.to_csv(out / "batch-summary.csv", index=False)
    print(summary.to_string(index=False))

    fig = Figure(figsize=(6, 3.5), layout="constrained")
    ax = fig.add_subplot()
    for name, counts in curves.items():
        ax.plot(counts["minutes"], counts["cells"], label=name)
    ax.set_xlabel("time (min)")
    ax.set_ylabel("cells")
    ax.set_title("Cells per frame, all files")
    ax.legend(fontsize="small")
    fig.savefig(out / "batch-summary.png", dpi=120)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else Path("batch_out"))
