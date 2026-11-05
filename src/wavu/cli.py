"""``wavu`` command: run a script once from the command line, or start a new one.

    wavu run <script.py> --in image=cells.tif --param sigma=2 --out results/
    wavu new-script my_analysis [--dest DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

from wavu import __version__
from wavu.codec import decode_input, encode_output
from wavu.scripts import coerce_params, load_script

REPO_URL = "https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu"
DEV_DEP_LINE = re.compile(r"^wavu\s*=.*#\s*wavu-dependency.*$", re.MULTILINE)
SKIP = {".pixi", "pixi.lock", "__pycache__", ".pytest_cache"}


class _PrintCtx:
    def __init__(self, tmpdir: Path, meta: dict) -> None:
        self.tmpdir = tmpdir
        self.meta = meta

    def log(self, msg: Any) -> None:
        print(msg, flush=True)

    def progress(self, frac: float) -> None:
        print(f"[{float(frac) * 100:5.1f}%]", file=sys.stderr, flush=True)

    def cancelled(self) -> bool:
        return False

    def check_cancelled(self) -> None:
        return None


def _kv(items: list[str], what: str) -> dict[str, str]:
    out = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"{what} must look like name=value, got {item!r}")
        k, v = item.split("=", 1)
        out[k] = v
    return out


def cmd_run(args: argparse.Namespace) -> int:
    info = load_script(Path(args.script))
    inputs, meta = {}, {}
    for k, v in _kv(args.inputs, "--in").items():
        inputs[k], meta[k] = decode_input({"path": v})
    params = coerce_params(info.params, _kv(args.params, "--param"))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = info.module.run(_PrintCtx(out_dir, meta), inputs, params) or {}
    # inline_limit=-1: every array becomes a TIFF file in --out
    summary = {k: encode_output(k, v, out_dir, inline_limit=-1) for k, v in result.items()}
    print(json.dumps(summary, indent=2))
    return 0


def template_dir() -> Path:
    packaged = Path(__file__).with_name("template")
    if packaged.is_dir():
        return packaged
    repo = Path(__file__).resolve().parents[2] / "templates" / "wavu-script"
    if repo.is_dir():
        return repo
    raise SystemExit("wavu: script template not found (broken install?)")


def wavu_dependency(dest: Path, source: str) -> str:
    """The `wavu = ...` line for a new script's pixi.toml."""
    repo_root = Path(__file__).resolve().parents[2]
    in_checkout = (repo_root / "pyproject.toml").is_file() and (repo_root / "templates").is_dir()
    if source == "auto":
        if in_checkout:
            source = "path"
        elif re.fullmatch(r"\d+\.\d+\.\d+", __version__):
            source = "release"
        else:
            source = "pypi"
    if source == "path":
        try:
            rel = Path(os.path.relpath(repo_root, dest.resolve())).as_posix()
        except ValueError:  # different drive on Windows
            rel = repo_root.as_posix()
        return f'wavu = {{ path = "{rel}", editable = true }}  # wavu-dependency'
    if source == "release":
        v = __version__
        return f'wavu = {{ url = "{REPO_URL}/releases/download/v{v}/wavu-{v}-py3-none-any.whl" }}  # wavu-dependency'
    return 'wavu = ">=0.1"  # wavu-dependency (PyPI)'


def cmd_new_script(args: argparse.Namespace) -> int:
    name = args.name
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\-]*", name):
        raise SystemExit(f"wavu: {name!r} is not a usable folder name (letters, digits, _ and -)")
    dest = Path(args.dest or ".") / name
    if dest.exists():
        raise SystemExit(f"wavu: {dest} already exists")
    shutil.copytree(template_dir(), dest, ignore=lambda d, names: [n for n in names if n in SKIP])
    toml = dest / "pixi.toml"
    text = toml.read_text(encoding="utf-8")
    text = text.replace('name = "wavu-script"', f'name = "{name}"')
    text = DEV_DEP_LINE.sub(wavu_dependency(dest, args.wavu_source), text)
    toml.write_text(text, encoding="utf-8")
    print(f"Created {dest}. Next: open it in VS Code, edit script.py, then in Fiji: Plugins > Wavu > Run Python Script...")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wavu", description="Wavu: run Python scripts from Fiji.")
    p.add_argument("--version", action="version", version=f"wavu {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a script once on files, without Fiji")
    r.add_argument("script", help="path to the script .py file")
    r.add_argument("--in", dest="inputs", action="append", default=[], metavar="NAME=PATH")
    r.add_argument("--param", dest="params", action="append", default=[], metavar="NAME=VALUE")
    r.add_argument("--out", default="wavu-out", help="folder for outputs (default: wavu-out)")
    r.set_defaults(func=cmd_run)
    n = sub.add_parser("new-script", help="copy the script template into a new folder")
    n.add_argument("name")
    n.add_argument("--dest", help="parent folder (default: current folder)")
    n.add_argument("--wavu-source", choices=["auto", "path", "release", "pypi"], default="auto",
                   help="how the new env gets wavu (default: this checkout if run from one, else the release wheel)")
    n.set_defaults(func=cmd_new_script)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
