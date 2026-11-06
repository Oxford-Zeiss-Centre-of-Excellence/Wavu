"""Headless Fiji smoke test: WAVU_FIJI=<Fiji.app> pixi run test-fiji.

Fiji runs tests/fiji/smoke_test.groovy, which drives the real client library
(fiji/scripts/Plugins/Wavu/lib) against a worker started through pixi in the
template script's own environment.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import REPO

pytestmark = pytest.mark.fiji

LAUNCHERS = [
    "fiji-windows-x64.exe", "ImageJ-win64.exe",
    "fiji-linux-x64", "ImageJ-linux64",
    "fiji-macos-arm64", "fiji-macos-x64", "fiji-macos", "Contents/MacOS/fiji-macos", "Contents/MacOS/ImageJ-macosx",
    "fiji", "ImageJ",
]


def find_launcher(fiji: Path) -> Path | None:
    preferred = os.environ.get("WAVU_FIJI_LAUNCHER")
    names = [preferred] if preferred else LAUNCHERS
    for name in names:
        p = fiji / name
        if p.is_file():
            return p
    return None


def test_fiji_runs_the_template_script_through_a_pixi_worker():
    fiji = os.environ.get("WAVU_FIJI")
    if not fiji:
        pytest.skip("set WAVU_FIJI to a Fiji.app folder")
    launcher = find_launcher(Path(fiji))
    if launcher is None:
        pytest.skip(f"no Fiji launcher found in {fiji}")
    if shutil.which("pixi") is None and not os.environ.get("PIXI_EXE"):
        pytest.skip("pixi not on PATH")
    if os.environ.get("WAVU_FIJI_INSTALL"):
        # Install this checkout's Fiji client (menu commands such as Run Script (Macro)).
        dest = Path(fiji) / "scripts" / "Plugins" / "Wavu"
        shutil.copytree(REPO / "fiji" / "scripts" / "Plugins" / "Wavu", dest, dirs_exist_ok=True)
    env = dict(
        os.environ,
        WAVU_LIB=str(REPO / "fiji/scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt"),
        WAVU_SCRIPT_DIR=str(REPO / "templates/wavu-script"),
        # A second folder: a ResultsTable / CSV path as wavu.run() inputs (chained steps).
        WAVU_SCRIPT_DIR2=str(REPO / "tests/fiji/table_echo"),
    )
    if os.environ.get("WAVU_FIJI_INSTALL"):
        env["WAVU_SMOKE_MACRO"] = "1"
    cmd = [str(launcher), "--headless", "--console", "--run", str(REPO / "tests/fiji/smoke_test.groovy")]
    if platform.system() == "Linux":
        cmd = [str(launcher), "--headless", "--run", str(REPO / "tests/fiji/smoke_test.groovy")]
    r = subprocess.run(cmd, cwd=fiji, env=env, capture_output=True, text=True, timeout=1800)
    out = r.stdout + r.stderr
    print(out[-6000:])
    assert "WAVU_SMOKE_INLINE" in out and "WAVU_SMOKE_FILE" in out
    assert "WAVU_SMOKE_RUN" in out, out[-3000:]
    assert "WAVU_SMOKE_TABLE rows=3" in out, out[-3000:]
    if os.environ.get("WAVU_FIJI_INSTALL"):
        assert "WAVU_SMOKE_MACRO_DONE" in out and "script finished" in out, out[-3000:]
    assert "WAVU_SMOKE_OK" in out, out[-3000:]


# The "Pipeline in Fiji" guide page (guide/workflows/pipeline-fiji.md): both
# versions of the counting DAG, run for real on examples/data/demo_timelapse.tif.
# Off by default: the first run installs the segment_frames and track_trackpy
# environments (minutes). Installs this checkout's Fiji client into WAVU_FIJI,
# because both pipelines use it the way a user would (Fiji's own scripts folder).
DEMO = REPO / "examples" / "data" / "demo_timelapse.tif"
TRUE_COUNTS = [25] * 6 + [26] * 3 + [25] * 3 + [26] * 5 + [27] * 2 + [28] * 4 + [29] * 7


def _dag_setup():
    if not os.environ.get("WAVU_SMOKE_DAG"):
        pytest.skip("set WAVU_SMOKE_DAG=1 to run the pipeline guide's Groovy and macro versions")
    fiji = os.environ.get("WAVU_FIJI")
    if not fiji:
        pytest.skip("set WAVU_FIJI to a Fiji.app folder")
    launcher = find_launcher(Path(fiji))
    if launcher is None:
        pytest.skip(f"no Fiji launcher found in {fiji}")
    if shutil.which("pixi") is None and not os.environ.get("PIXI_EXE"):
        pytest.skip("pixi not on PATH")
    if not DEMO.is_file():
        pytest.skip("examples/data/demo_timelapse.tif missing (pixi run demo-data)")
    dest = Path(fiji) / "scripts" / "Plugins" / "Wavu"
    shutil.copytree(REPO / "fiji" / "scripts" / "Plugins" / "Wavu", dest, dirs_exist_ok=True)
    return Path(fiji), launcher


def _marker_counts(out: str, marker: str) -> tuple[int, int, list[int]]:
    line = next((ln for ln in out.splitlines() if marker + " " in ln), None)
    assert line is not None, out[-3000:]
    kv = dict(part.split("=", 1) for part in line.split(marker, 1)[1].split())
    return int(kv["frames"]), int(kv["tracks"]), [int(c) for c in kv["counts"].split(",")]


def _check(frames: int, tracks: int, counts: list[int], out_dir: Path):
    assert frames == 30 and len(counts) == 30
    # Thresholding may merge two touching nuclei now and then: allow one off per frame.
    assert all(abs(c - t) <= 1 for c, t in zip(counts, TRUE_COUNTS)), counts
    assert 25 <= tracks <= 45, tracks
    assert (out_dir / "demo_timelapse-counts.csv").is_file()
    assert (out_dir / "demo_timelapse-counts.png").stat().st_size > 1000


def test_pipeline_guide_groovy(tmp_path):
    fiji, launcher = _dag_setup()
    args = (f"timelapse='{DEMO.as_posix()}',segmentDir='{(REPO / 'examples/segment_frames').as_posix()}',"
            f"outDir='{tmp_path.as_posix()}'")
    flags = ["--headless"] if platform.system() == "Linux" else ["--headless", "--console"]
    cmd = [str(launcher), *flags, "--run", str(REPO / "tests/fiji/dag_counting.groovy"), args]
    r = subprocess.run(cmd, cwd=fiji, capture_output=True, text=True, timeout=1800)
    out = r.stdout + r.stderr
    print(out[-4000:])
    _check(*_marker_counts(out, "WAVU_DAG_OK"), tmp_path)


def test_pipeline_guide_macro(tmp_path):
    fiji, launcher = _dag_setup()
    arg = "|".join(p.as_posix() for p in [DEMO, REPO / "examples/segment_frames",
                                          REPO / "examples/track_trackpy", tmp_path])
    flags = [] if platform.system() == "Linux" else ["--console"]
    cmd = [str(launcher), *flags, "-batch", str(REPO / "tests/fiji/dag_counting.ijm"), arg]
    r = subprocess.run(cmd, cwd=fiji, capture_output=True, text=True, timeout=1800)
    out = r.stdout + r.stderr
    print(out[-4000:])
    _check(*_marker_counts(out, "WAVU_DAG_MACRO_OK"), tmp_path)
