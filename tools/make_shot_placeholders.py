"""Draw grey placeholder PNGs for the guide's screenshots.

    pixi run -e docs python tools/make_shot_placeholders.py

Reads the table in guide/assets/shots/SHOT-LIST.md and writes one 1200x750
PNG per row (number + title + "screenshot coming soon"). A file is only
(re)written if it is missing or is itself a placeholder (marked with a PNG
text chunk), so real screenshots are never overwritten.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

SHOTS = Path(__file__).resolve().parent.parent / "guide" / "assets" / "shots"
ROW = re.compile(r"^\|\s*`(?P<file>\d\d-[\w-]+\.png)`\s*\|\s*(?P<title>[^|]+?)\s*\|\s*(?P<page>[^|]+?)\s*\|")
MARK = "wavu-placeholder"
W, H = 1200, 750


def font(size: int) -> ImageFont.ImageFont:
    for name in ("segoeui.ttf", "DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def is_placeholder(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            return MARK in getattr(im, "text", {})
    except OSError:
        return False


def draw(path: Path, number: str, title: str, page: str) -> None:
    im = Image.new("RGB", (W, H), (236, 239, 241))
    d = ImageDraw.Draw(im)
    d.rectangle([12, 12, W - 13, H - 13], outline=(176, 190, 197), width=4)
    d.text((W / 2, 250), number, fill=(120, 144, 156), font=font(150), anchor="mm")
    d.text((W / 2, 400), title, fill=(55, 71, 79), font=font(48), anchor="mm")
    d.text((W / 2, 470), f"Screenshot coming soon  ·  {page}", fill=(96, 125, 139), font=font(30), anchor="mm")
    d.text((W / 2, 680), path.name, fill=(120, 144, 156), font=font(26), anchor="mm")
    info = PngImagePlugin.PngInfo()
    info.add_text(MARK, "1")
    im.save(path, pnginfo=info, optimize=True)


def main() -> int:
    rows = [m.groupdict() for line in (SHOTS / "SHOT-LIST.md").read_text(encoding="utf-8").splitlines()
            if (m := ROW.match(line))]
    for r in rows:
        path = SHOTS / r["file"]
        if path.exists() and not is_placeholder(path):
            print(f"keep  {path.name} (real screenshot)")
            continue
        draw(path, r["file"][:2], r["title"], r["page"])
        print(f"draw  {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
