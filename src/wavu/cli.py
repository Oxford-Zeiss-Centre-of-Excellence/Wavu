"""``wavu`` command: run a script once from the command line, or start a new one.

    wavu run <script.py> --in image=cells.tif --param sigma=2 --out results/
    wavu new-script my_analysis [--dest DIR]
    wavu package <script-dir> --name my-tool --menu "My Lab>My Tool" [--out dist/fiji]
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
NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_\-]*")


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


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def wavu_dependency(dest: Path, source: str) -> str:
    """The `wavu = ...` line for a new script's pixi.toml."""
    repo_root = Path(__file__).resolve().parents[2]
    in_checkout = (repo_root / "pyproject.toml").is_file() and (repo_root / "templates").is_dir()
    if source == "auto":
        source = "path" if in_checkout and _inside(dest, repo_root) else "git"
    released = re.fullmatch(r"\d+\.\d+\.\d+", __version__) is not None
    if source == "path":
        if not in_checkout:
            raise SystemExit("wavu: --wavu-source path only works from a git checkout of Wavu")
        try:
            rel = Path(os.path.relpath(repo_root, dest.resolve())).as_posix()
        except ValueError:  # different drive on Windows
            rel = repo_root.as_posix()
        return f'wavu = {{ path = "{rel}", editable = true }}  # wavu-dependency'
    if source == "git":
        ref = f'tag = "v{__version__}"' if released else 'branch = "main"'
        return f'wavu = {{ git = "{REPO_URL}.git", {ref} }}  # wavu-dependency'
    if source == "release":
        if not released:
            raise SystemExit(f"wavu: {__version__} is not a release version; use --wavu-source git")
        v = __version__
        return f'wavu = {{ url = "{REPO_URL}/releases/download/v{v}/wavu-{v}-py3-none-any.whl" }}  # wavu-dependency'
    return 'wavu = ">=0.1"  # wavu-dependency (PyPI)'


TEXT_SUFFIXES = {".toml", ".yml", ".yaml", ".md", ".json", ".py"}


def cmd_new_script(args: argparse.Namespace) -> int:
    name = args.name
    if not NAME_RE.fullmatch(name):
        raise SystemExit(f"wavu: {name!r} is not a usable folder name (letters, digits, _ and -)")
    dest = Path(args.dest or ".") / name
    if dest.exists():
        raise SystemExit(f"wavu: {dest} already exists")
    shutil.copytree(template_dir(), dest, ignore=lambda d, names: [n for n in names if n in SKIP])
    for f in dest.rglob("*"):
        if f.is_file() and f.suffix in TEXT_SUFFIXES:
            t = f.read_text(encoding="utf-8")
            if "__SCRIPT_NAME__" in t:
                f.write_text(t.replace("__SCRIPT_NAME__", name), encoding="utf-8")
    toml = dest / "pixi.toml"
    text = toml.read_text(encoding="utf-8")
    text = text.replace('name = "wavu-script"', f'name = "{name}"')
    text = DEV_DEP_LINE.sub(wavu_dependency(dest, args.wavu_source), text)
    toml.write_text(text, encoding="utf-8")
    print(f"Created {dest}. Next: open it in VS Code, edit script.py, then in Fiji: Plugins > Wavu > Run Python Script...")
    return 0


# Files a packaged script never needs at run time.
PACKAGE_SKIP = {".pixi", ".vscode", ".github", ".git", "__pycache__", ".pytest_cache", "wavu-out", "conftest.py",
                "Dockerfile", ".dockerignore"}
STUB = """// {menu_label} -- runs the Wavu script installed in <Fiji>/wavu/scripts/{name}.
// Generated by `wavu package`; needs the Wavu Fiji scripts (Plugins > Wavu).
// SPDX-License-Identifier: GPL-3.0-or-later
def lib = new File(ij.IJ.getDirectory("imagej"), "scripts/Plugins/Wavu/lib/wavu_lib.groovy.txt")
if (!lib.isFile()) {{
    ij.IJ.error("{title}", "This command needs Wavu. Install it first: {repo}")
    return
}}
def wavu = new GroovyShell(this.class.classLoader).evaluate(lib)
wavu.runScriptFolder(new File(ij.IJ.getDirectory("imagej"), "wavu/scripts/{name}"))
"""


def cmd_package(args: argparse.Namespace) -> int:
    """Build an update-site-shaped tree (+ zip) that installs a script folder into Fiji."""
    src = Path(args.script_dir).resolve()
    name = args.name or src.name
    if not NAME_RE.fullmatch(name):
        raise SystemExit(f"wavu: {name!r} is not a usable name (letters, digits, _ and -)")
    if not (src / "pixi.toml").is_file():
        raise SystemExit(f"wavu: {src} has no pixi.toml")
    if not (src / "pixi.lock").is_file():
        raise SystemExit(f"wavu: {src} has no pixi.lock -- run `pixi lock` (or `pixi install`) there first, and commit it")
    dep = next((l for l in (src / "pixi.toml").read_text(encoding="utf-8").splitlines() if l.strip().startswith("wavu =")), "")
    if "path =" in dep:
        raise SystemExit(
            "wavu: this script depends on wavu through a local path, which will not exist on other machines.\n"
            f"Change the line in pixi.toml to\n  {wavu_dependency(src, 'git').split('  #')[0]}\nthen run `pixi lock`."
        )
    parts = [p.strip() for p in args.menu.split(">") if p.strip()]
    if not parts or any(c in p for p in parts for c in '/\\:*?"<>|'):
        raise SystemExit(f"wavu: bad --menu {args.menu!r}; use e.g. \"My Lab>Cellpose Plus\"")
    *submenus, title = parts
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    target = out / "wavu" / "scripts" / name
    shutil.copytree(
        src, target,
        ignore=lambda d, names: [n for n in names if n in PACKAGE_SKIP or n.startswith("test_") or n.endswith("_test.py")],
    )
    stub = out.joinpath("scripts", "Plugins", *submenus, f"{title}.groovy")
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text(STUB.format(menu_label="Plugins > " + " > ".join(parts), title=title, name=name, repo=REPO_URL),
                    encoding="utf-8")
    zip_base = out.parent / f"{name}-fiji"
    zip_path = Path(shutil.make_archive(str(zip_base), "zip", root_dir=out))
    print(f"Wrote {out} and {zip_path}\nUsers unzip it into Fiji.app (needs Wavu); menu: Plugins > {' > '.join(parts)}")
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
    n.add_argument("--wavu-source", choices=["auto", "path", "git", "release", "pypi"], default="auto",
                   help="how the new env gets wavu (default: a relative path inside a Wavu checkout, else git)")
    n.set_defaults(func=cmd_new_script)
    k = sub.add_parser("package", help="build a Fiji-installable tree + zip from a script folder (needs pixi.lock)")
    k.add_argument("script_dir")
    k.add_argument("--name", help="install folder name under <Fiji>/wavu/scripts (default: the folder's name)")
    k.add_argument("--menu", required=True, help='menu path under Plugins, e.g. "My Lab>Cellpose Plus"')
    k.add_argument("--out", default="dist/fiji", help="output tree (default: dist/fiji; the zip goes next to it)")
    k.set_defaults(func=cmd_package)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
