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
    env = dict(
        os.environ,
        WAVU_LIB=str(REPO / "fiji/scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt"),
        WAVU_SCRIPT_DIR=str(REPO / "templates/wavu-script"),
    )
    cmd = [str(launcher), "--headless", "--console", "--run", str(REPO / "tests/fiji/smoke_test.groovy")]
    if platform.system() == "Linux":
        cmd = [str(launcher), "--headless", "--run", str(REPO / "tests/fiji/smoke_test.groovy")]
    r = subprocess.run(cmd, cwd=fiji, env=env, capture_output=True, text=True, timeout=1800)
    out = r.stdout + r.stderr
    print(out[-6000:])
    assert "WAVU_SMOKE_INLINE" in out and "WAVU_SMOKE_FILE" in out
    assert "WAVU_SMOKE_OK" in out, out[-3000:]
