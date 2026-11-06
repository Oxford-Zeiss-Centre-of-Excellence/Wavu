"""Draw the home-page model diagram as SVG, one file per language.

    python tools/make_home_diagram.py

Labels live in LABELS below (one dict per language). Output:
guide/assets/img/home-model.svg (English) and home-model.<lang>.svg; the
i18n plugin serves each language its own file under the same path.
Hand-made SVG instead of Mermaid: the container must enclose the whole
kitchen, and Mermaid stacks nested group titles on top of each other.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "guide" / "assets" / "img"
FONT = "Noto Sans, Noto Sans JP, Noto Sans KR, Noto Sans TC, Noto Sans SC, sans-serif"

LABELS: dict[str, dict[str, str]] = {
    "en": dict(fe="The waiters (frontends)", f="wavu-fiji|Plugins › Wavu", n="wavu-napari|Run Python Script (Wavu)",
               be="The kitchen (backend)", w="wavu worker", s="your script.py|PARAMS + run()",
               e="its own pixi env|(the kitchenware)", order="your order", plate="the plate + live Log",
               ct="optional: the whole kitchen in a container (Docker / Apptainer)"),
    "fr": dict(fe="Les serveurs (frontends)", f="wavu-fiji|Plugins › Wavu", n="wavu-napari|Run Python Script (Wavu)",
               be="La cuisine (backend)", w="worker wavu", s="votre script.py|PARAMS + run()",
               e="son propre env. pixi|(la batterie de cuisine)", order="votre commande",
               plate="l'assiette + Log en direct",
               ct="optionnel : toute la cuisine dans un conteneur (Docker / Apptainer)"),
    "de": dict(fe="Die Kellner (Frontends)", f="wavu-fiji|Plugins › Wavu", n="wavu-napari|Run Python Script (Wavu)",
               be="Die Küche (Backend)", w="wavu-Worker", s="Ihr script.py|PARAMS + run()",
               e="eigene pixi-Umgebung|(die Küchengeräte)", order="Ihre Bestellung", plate="der Teller + Live-Log",
               ct="optional: die ganze Küche in einem Container (Docker / Apptainer)"),
    "es": dict(fe="Los camareros (frontends)", f="wavu-fiji|Plugins › Wavu", n="wavu-napari|Run Python Script (Wavu)",
               be="La cocina (backend)", w="worker de wavu", s="tu script.py|PARAMS + run()",
               e="su propio entorno pixi|(los utensilios de cocina)", order="tu pedido",
               plate="el plato + Log en directo",
               ct="opcional: toda la cocina en un contenedor (Docker / Apptainer)"),
    "ru": dict(fe="Официанты (фронтенды)", f="wavu-fiji|Plugins › Wavu", n="wavu-napari|Run Python Script (Wavu)",
               be="Кухня (бэкенд)", w="воркер wavu", s="ваш script.py|PARAMS + run()",
               e="своё pixi-окружение|(кухонная утварь)", order="ваш заказ", plate="тарелка + живой Log",
               ct="по желанию: вся кухня в контейнере (Docker / Apptainer)"),
    "ja": dict(fe="ウェイター（フロントエンド）", f="wavu-fiji|Plugins › Wavu", n="wavu-napari|Run Python Script (Wavu)",
               be="厨房（バックエンド）", w="wavu ワーカー", s="あなたの script.py|PARAMS + run()",
               e="専用の pixi 環境|（調理器具）", order="あなたの注文", plate="料理 + リアルタイムの Log",
               ct="任意：厨房ごとコンテナーに入れる（Docker / Apptainer）"),
    "ko": dict(fe="웨이터 (프론트엔드)", f="wavu-fiji|Plugins › Wavu", n="wavu-napari|Run Python Script (Wavu)",
               be="주방 (백엔드)", w="wavu 워커", s="나의 script.py|PARAMS + run()",
               e="자기만의 pixi 환경|(주방 도구)", order="주문", plate="요리 + 실시간 Log",
               ct="선택: 주방 전체를 컨테이너에 (Docker / Apptainer)"),
    "zh-Hant": dict(fe="服務生（前端）", f="wavu-fiji|Plugins › Wavu", n="wavu-napari|Run Python Script (Wavu)",
                    be="廚房（後端）", w="wavu worker", s="你的 script.py|PARAMS + run()",
                    e="它自己的 pixi 環境|（廚具）", order="你的點餐", plate="餐點 + 即時 Log",
                    ct="可選：把整個廚房放進容器（Docker / Apptainer）"),
    "zh-Hans": dict(fe="服务员（前端）", f="wavu-fiji|Plugins › Wavu", n="wavu-napari|Run Python Script (Wavu)",
                    be="厨房（后端）", w="wavu worker", s="你的 script.py|PARAMS + run()",
                    e="它自己的 pixi 环境|（厨具）", order="你点的菜", plate="上菜 + 实时 Log",
                    ct="可选：把整个厨房放进容器（Docker / Apptainer）"),
}


def text_width(s: str, size: float) -> float:
    w = 0.0
    for ch in s:
        w += size * (1.0 if unicodedata.east_asian_width(ch) in "WF" else 0.56)
    return w


def fit(lines: list[str], width: float, size: float) -> float:
    """Largest font size <= size so that every line fits in width."""
    widest = max(text_width(l, 1.0) for l in lines)
    return min(size, (width - 16) / widest) if widest else size


def label(x: float, y: float, s: str, size: float, color: str, width: float, weight: str = "normal") -> str:
    lines = s.split("|")
    size = fit(lines, width, size)
    lh = size * 1.3
    y0 = y - lh * (len(lines) - 1) / 2
    spans = "".join(
        f'<tspan x="{x:.1f}" y="{y0 + i * lh:.1f}">{escape(l)}</tspan>' for i, l in enumerate(lines))
    return (f'<text text-anchor="middle" dominant-baseline="middle" font-size="{size:.1f}" '
            f'font-weight="{weight}" fill="{color}">{spans}</text>')


def chip(x: float, y: float, s: str, size: float = 12.5) -> str:
    """An edge label on a white background."""
    w = text_width(s, size) + 12
    return (f'<rect x="{x - w / 2:.1f}" y="{y - 10:.1f}" width="{w:.1f}" height="20" rx="4" fill="#ffffff"/>'
            + label(x, y, s, size, "#263238", w + 16))


def svg(L: dict[str, str]) -> str:
    W, H = 1000, 430
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" font-family="{FONT}">',
         f'<title>{escape(L["fe"])} · {escape(L["be"])}</title>',
         '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
         'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#37474f"/></marker></defs>']
    # waiters
    p.append('<rect x="16" y="36" width="250" height="330" rx="10" fill="#f5f9ff" stroke="#90caf9" stroke-width="1.5"/>')
    p.append(label(141, 60, L["fe"], 15, "#263238", 240))
    for y, key in ((95, "f"), (245, "n")):
        p.append(f'<rect x="36" y="{y}" width="210" height="70" rx="6" fill="#e3f2fd" stroke="#1565c0" stroke-width="1.5"/>')
        p.append(label(141, y + 35, L[key], 14, "#0d47a1", 210))
    # container (dashed) enclosing the whole kitchen, its label at the bottom inside
    p.append('<rect x="430" y="16" width="554" height="398" rx="12" fill="#ffffff" stroke="#78909c" '
             'stroke-width="1.5" stroke-dasharray="7 5"/>')
    p.append(label(707, 392, L["ct"], 13.5, "#455a64", 534))
    # kitchen
    p.append('<rect x="450" y="36" width="514" height="330" rx="10" fill="#f6fbf6" stroke="#a5d6a7" stroke-width="1.5"/>')
    p.append(label(707, 60, L["be"], 15, "#263238", 500))
    p.append('<rect x="468" y="172" width="136" height="58" rx="6" fill="#e8f5e9" stroke="#2e7d32" stroke-width="1.5"/>')
    p.append(label(536, 201, L["w"], 14, "#1b5e20", 136))
    p.append('<rect x="634" y="160" width="156" height="82" rx="6" fill="#fff3e0" stroke="#ef6c00" stroke-width="1.5"/>')
    p.append(label(712, 201, L["s"], 14, "#e65100", 156))
    cx, top, bot, rx, ry = 878, 166, 236, 66, 12
    p.append(f'<path d="M{cx - rx},{top} v{bot - top} a{rx},{ry} 0 0 0 {2 * rx},0 v-{bot - top}" '
             f'fill="#f3e5f5" stroke="#6a1b9a" stroke-width="1.5"/>')
    p.append(f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="#f3e5f5" stroke="#6a1b9a" stroke-width="1.5"/>')
    p.append(label(cx, 208, L["e"], 13.5, "#4a148c", 2 * rx))
    # arrows
    A = 'fill="none" stroke="#37474f" stroke-width="1.6"'
    p.append(f'<path d="M246,130 C350,130 380,188 466,192" {A} marker-end="url(#a)"/>')
    p.append(f'<path d="M246,280 C350,280 380,214 466,210" {A} marker-end="url(#a)"/>')
    p.append(f'<path d="M466,201 L268,201" {A} marker-end="url(#a)"/>')
    p.append(f'<path d="M604,201 L632,201" {A} marker-end="url(#a)"/>')
    p.append('<path d="M790,201 L812,201" fill="none" stroke="#6a1b9a" stroke-width="1.6" stroke-dasharray="3 3"/>')
    p.append(chip(338, 118, L["order"]))
    p.append(chip(338, 292, L["order"]))
    p.append(chip(357, 201, L["plate"]))
    p.append("</svg>")
    return "\n".join(p) + "\n"


def main() -> None:
    for lang, L in LABELS.items():
        name = "home-model.svg" if lang == "en" else f"home-model.{lang}.svg"
        (OUT / name).write_text(svg(L), encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
