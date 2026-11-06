"""Track with trackpy -- link per-frame detections (frame, y, x) into tracks.

This script takes a **table**, not an image: run it from a scripted pipeline
(wavu.run in Fiji, or wavu.client.Worker.run in Python), passing e.g. the
``detections`` table of examples/segment_frames as ``inputs["detections"]``.
The Fiji menu dialog only offers images, so it cannot supply that input.
"""

import numpy as np

PARAMS = {
    "search_range": {"type": "float", "default": 10.0, "label": "Search range (pixels per frame)"},
    "memory": {"type": "int", "default": 2, "label": "Memory (frames an object may vanish)"},
}


def run(ctx, inputs, params):
    import pandas as pd
    import trackpy

    if "detections" not in inputs:
        raise ValueError("this script needs a table input 'detections' (columns frame, y, x, ...); "
                         "pass it from a script, e.g. wavu.run(folder, 'script', [:], [detections: table])")
    det = inputs["detections"]
    if not isinstance(det, pd.DataFrame):  # a list of dicts (CSV rows read without pandas, or passed directly)
        det = pd.DataFrame(list(det))
    missing = {"frame", "y", "x"} - set(det.columns)
    if missing:
        raise ValueError(f"the detections table lacks column(s) {sorted(missing)}; it has {list(det.columns)}")
    det = det.copy()
    det["frame"] = pd.to_numeric(det["frame"]).astype(int)
    det["y"] = pd.to_numeric(det["y"]).astype(float)
    det["x"] = pd.to_numeric(det["x"]).astype(float)
    ctx.log(f"Linking {len(det)} detections over {det['frame'].nunique()} frame(s), "
            f"search_range={params['search_range']}, memory={params['memory']}")
    ctx.progress(0.1)

    trackpy.quiet()
    tracks = trackpy.link(det, search_range=params["search_range"], memory=params["memory"],
                          pos_columns=["y", "x"], t_column="frame")
    tracks = tracks.reset_index(drop=True).sort_values(["particle", "frame"], kind="stable").reset_index(drop=True)
    tracks["particle"] = tracks["particle"].astype(np.int64)
    n_tracks = int(tracks["particle"].nunique())
    ctx.log(f"{n_tracks} tracks")
    ctx.progress(1.0)
    return {"tracks": tracks, "n_tracks": n_tracks}
