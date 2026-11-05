"""Verify (or re-create) the committed BBBC039 test image + ground-truth mask.

    pixi run fetch-test-data

tests/data/BBBC039/ is committed (CC0, ~0.74 MB), so normally this only checks
the sha256 of the two files. If they are missing, it downloads BBBC039's
images.zip (~78 MB) and masks.zip (~2.8 MB) once into a cache folder, extracts
the single pair and verifies it. See docs/test-data.md. Standard library only.
"""

from __future__ import annotations

import hashlib
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

STEM = "IXMtest_A02_s1_w1051DAA7C-7042-435F-99F0-1E847D9B42CB"
BASE = "https://data.broadinstitute.org/bbbc/BBBC039/"
# (zip, member, local name, sha256 of the member exactly as published)
FILES = [
    ("images.zip", f"images/{STEM}.tif", "A02_s1.tif", "9eacee0e5a4c29af70307af4d310320632e31ed84b4d8b5fd4fce42930f780ec"),
    ("masks.zip", f"masks/{STEM}.png", "A02_s1_mask.png", "c56c246edcd456f81fb0d61d318c2b7a378afba207bd0b409834db16d30cfb72"),
]
REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "tests" / "data" / "BBBC039"
CACHE = Path(os.environ.get("WAVU_CACHE", Path.home() / ".cache" / "wavu"))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(zip_name: str) -> Path:
    path = CACHE / "BBBC039" / zip_name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {BASE}{zip_name} ...", flush=True)
        tmp = path.with_suffix(".part")
        with urllib.request.urlopen(BASE + zip_name, timeout=300) as r, open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        tmp.replace(path)
    return path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for zip_name, member, name, expected in FILES:
        target = OUT / name
        if not target.exists():
            try:
                with zipfile.ZipFile(fetch(zip_name)) as z:
                    target.write_bytes(z.read(member))
            except OSError as e:
                print(f"Download failed: {e}")
                return 1
        got = sha256(target.read_bytes())
        if got != expected:
            print(f"sha256 mismatch for {target}: expected {expected}, got {got}")
            return 1
        print(f"  {name}: sha256 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
