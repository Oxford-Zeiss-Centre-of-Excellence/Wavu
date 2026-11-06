"""The Python pipeline of the guide (examples/pipelines/dag_counting.py), for real.

Starts two workers through pixi (examples/segment_frames, examples/track_trackpy),
each in its own environment. Slow the first time (installs both).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.pixi_env, pytest.mark.timeout(3600)]

REPO = Path(__file__).resolve().parents[2]
PIPELINE = REPO / "examples" / "pipelines" / "dag_counting.py"
# examples/data/README.md: true nuclei per frame, frames 0-29
TRUTH = [25] * 6 + [26] * 3 + [25] * 3 + [26] * 5 + [27] * 2 + [28] * 4 + [29] * 7


def test_pipeline_counts_and_tracks(tmp_path):
    from wavu.client import find_pixi

    if find_pixi() is None:
        pytest.skip("pixi not found")
    if not PIPELINE.is_file():
        pytest.skip(f"no pipeline at {PIPELINE}")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, str(PIPELINE), "--no-viewer", "--out", str(tmp_path)],
                       capture_output=True, text=True, encoding="utf-8", env=env, timeout=3500)
    assert p.returncode == 0, p.stdout + p.stderr
    m = re.search(r"WAVU_DAG_PY_OK frames=(\d+) tracks=(\d+) counts=([\d,]+)", p.stdout)
    assert m, p.stdout
    frames, tracks = int(m.group(1)), int(m.group(2))
    counts = [int(c) for c in m.group(3).split(",")]
    assert frames == 30 and len(counts) == 30
    close = sum(abs(c - t) <= 1 for c, t in zip(counts, TRUTH))
    assert close >= 25, list(zip(counts, TRUTH))
    assert tracks > 20
    assert (tmp_path / "counts.csv").is_file() and (tmp_path / "plot.png").is_file()
