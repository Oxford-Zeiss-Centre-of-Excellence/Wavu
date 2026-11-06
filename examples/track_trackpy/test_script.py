"""Tests for script.py -- run with `pixi run test` in this folder. No Fiji needed."""

from pathlib import Path

import pandas as pd
import pytest

from wavu.testing import FakeCtx, run_script

SCRIPT = Path(__file__).with_name("script.py")


def two_moving_blobs(n_frames=6):
    rows = []
    for t in range(n_frames):
        rows.append({"frame": t, "label": 1, "y": 10.0 + 2 * t, "x": 10.0 + t, "area": 50})
        rows.append({"frame": t, "label": 2, "y": 60.0 - t, "x": 40.0 + 2 * t, "area": 60})
    return rows


def test_two_blobs_moving_linearly_make_two_tracks():
    ctx = FakeCtx()
    out = run_script(SCRIPT, {"detections": pd.DataFrame(two_moving_blobs())}, {}, ctx=ctx)
    tracks = out["tracks"]
    assert out["n_tracks"] == 2
    assert {"frame", "label", "y", "x", "area", "particle"} <= set(tracks.columns)
    assert len(tracks) == 12
    for _, tr in tracks.groupby("particle"):          # each track follows one blob only
        assert tr["label"].nunique() == 1 and len(tr) == 6
    assert ctx.progress_values[-1] == 1.0


def test_a_list_of_dicts_works_too():
    rows = [{k: str(v) for k, v in r.items()} for r in two_moving_blobs()]   # as csv.DictReader gives them
    out = run_script(SCRIPT, {"detections": rows}, {"search_range": 5})
    assert out["n_tracks"] == 2


def test_memory_bridges_a_missing_frame():
    rows = [r for r in two_moving_blobs() if not (r["label"] == 1 and r["frame"] == 3)]
    assert run_script(SCRIPT, {"detections": pd.DataFrame(rows)}, {"memory": 2})["n_tracks"] == 2
    assert run_script(SCRIPT, {"detections": pd.DataFrame(rows)}, {"memory": 0})["n_tracks"] == 3


def test_missing_input_or_columns_are_explained():
    with pytest.raises(ValueError, match="table input 'detections'"):
        run_script(SCRIPT, {}, {})
    with pytest.raises(ValueError, match="lacks column"):
        run_script(SCRIPT, {"detections": pd.DataFrame({"frame": [0], "row": [1]})}, {})
