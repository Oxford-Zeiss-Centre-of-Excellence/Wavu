"""Build dist/wavu-fiji-<version>.zip: the Fiji client, ready to unzip into Fiji.app.

    pixi run fiji-zip [-- VERSION]

The version (default: the installed wavu's, i.e. the git tag via hatch-vcs)
replaces the @WAVU_VERSION@ placeholder in the client library, so the Fiji
side reports the same version as the Python side. Also used by release.yml to
stage the update-site upload.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "fiji"
PLACEHOLDER = "@WAVU_VERSION@"


def default_version() -> str:
    try:
        from wavu import __version__

        return __version__
    except ImportError:
        return "0.0.0"


def stage(dest: Path, version: str) -> list[Path]:
    """Copy fiji/ into dest with the version filled in; returns the files written."""
    written = []
    for src in sorted(SRC.rglob("*")):
        if src.is_dir() or "__pycache__" in src.parts:
            continue
        out = dest / src.relative_to(SRC)
        out.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in {".groovy", ".txt"}:
            out.write_text(src.read_text(encoding="utf-8").replace(PLACEHOLDER, version), encoding="utf-8")
        else:
            shutil.copy2(src, out)
        written.append(out)
    return written


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("version", nargs="?", default=None)
    p.add_argument("--stage-dir", type=Path, help="also (only) stage the files into this folder, e.g. a Fiji.app")
    p.add_argument("--out", type=Path, default=REPO / "dist")
    args = p.parse_args(argv)
    version = (args.version or default_version()).lstrip("v")
    if args.stage_dir:
        files = stage(args.stage_dir, version)
        print(f"Staged {len(files)} files into {args.stage_dir} (version {version})")
        return 0
    args.out.mkdir(parents=True, exist_ok=True)
    zip_path = args.out / f"wavu-fiji-{version}.zip"
    tmp = args.out / f".stage-{version}"
    shutil.rmtree(tmp, ignore_errors=True)
    files = stage(tmp, version)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(tmp).as_posix())
    shutil.rmtree(tmp)
    print(f"Wrote {zip_path} ({len(files)} files, version {version}) -- unzip it into your Fiji.app folder")
    return 0


if __name__ == "__main__":
    sys.exit(main())
