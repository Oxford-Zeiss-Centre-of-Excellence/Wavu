"""Fetch ONE Cell Tracking Challenge frame + its ground-truth segmentation into tests/data/.

    pixi run fetch-test-data

Downloads the Fluo-N2DH-GOWT1 training archive (~57 MB) from the official CTC
server once into a cache folder, checks the sha256 of the two files we use,
and writes them (uncompressed, so no imagecodecs is needed to read them) to
tests/data/Fluo-N2DH-GOWT1/. Nothing here is ever committed: the CTC terms
forbid redistributing ("cloning") the datasets -- see docs/test-data.md.

Standard library + tifffile/imagecodecs (both in the dev environment).
"""

from __future__ import annotations

import hashlib
import io
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://data.celltrackingchallenge.net/training-datasets/Fluo-N2DH-GOWT1.zip"
# Archive hash as downloaded on 2026-11-05; informational only (CTC may re-pack the zip).
ARCHIVE_SHA256 = "1a7bd9a7d1d10c4122c7782427b437246fb69cc3322a975485c04e206f64fc2c"
# The members we use -- these must match exactly.
MEMBERS = {
    "Fluo-N2DH-GOWT1/01/t021.tif": ("t021.tif", "e238390fc4d1edf5e38e24638b4a9165a10b8e94252b14c8c85fe2c6f32d35e5"),
    "Fluo-N2DH-GOWT1/01_GT/SEG/man_seg021.tif": (
        "man_seg021.tif",
        "abd1dee1d6ace107c908819100221774c57e13c150456e92e6d08bc59a83d94a",
    ),
}
REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "tests" / "data" / "Fluo-N2DH-GOWT1"
CACHE = Path(os.environ.get("WAVU_CACHE", Path.home() / ".cache" / "wavu"))

ATTRIBUTION = """\
Fluo-N2DH-GOWT1 (training sequence 01, frame 21 and its gold-standard segmentation)
from the Cell Tracking Challenge, https://celltrackingchallenge.net/2d-datasets/
Maska et al., "The Cell Tracking Challenge: 10 years of objective benchmarking",
Nature Methods 20, 1010-1020 (2023), https://doi.org/10.1038/s41592-023-01879-y
Used under the CTC terms of use (https://celltrackingchallenge.net/datasets/).
Do not commit or redistribute these files.
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    print(f"Downloading {URL} (~57 MB) ...", flush=True)
    with urllib.request.urlopen(URL, timeout=120) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / total:6.1%}", end="", flush=True)
    print()
    tmp.replace(dest)


def main() -> int:
    if all((OUT / name).exists() for name, _ in MEMBERS.values()):
        print(f"Test data already in {OUT}")
        return 0
    archive = CACHE / "Fluo-N2DH-GOWT1.zip"
    if not archive.exists():
        try:
            download(archive)
        except OSError as e:
            print(f"Download failed: {e}\nCheck your network / proxy, or download {URL} by hand into {archive}.")
            return 1
    data = archive.read_bytes()
    if sha256(data) != ARCHIVE_SHA256:
        print("Note: the archive's sha256 differs from the one recorded (CTC may have re-packed it); "
              "checking the individual files instead.")
    import numpy as np
    import tifffile

    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member, (name, expected) in MEMBERS.items():
            raw = z.read(member)
            got = sha256(raw)
            if got != expected:
                print(f"sha256 mismatch for {member}: expected {expected}, got {got}. Delete {archive} and retry.")
                return 1
            arr = tifffile.imread(io.BytesIO(raw))
            tifffile.imwrite(OUT / name, np.ascontiguousarray(arr))  # uncompressed copy
            print(f"  {name}: {arr.shape} {arr.dtype} (sha256 OK)")
    (OUT / "SOURCE.txt").write_text(ATTRIBUTION, encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
