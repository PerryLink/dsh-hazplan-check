#!/usr/bin/env python3
"""Generate README image assets for dsh-hazplan-check (docs/assets/).

Outputs (idempotent overwrite):
  dsh-hazplan-check-flow-light.svg / dsh-hazplan-check-flow-dark.svg
      Hero flow diagram. Two hand-written SVG files (vector — never
      rasterized to webp). Text inside is command-surface tokens only
      (worksheet, parse, rules/hazplan-check.yaml, hazplan_check, skipped),
      so all five README languages share the same pair.
  Evidence charts: none. This repository publishes no benchmark dataset,
  and the family standard forbids inventing one; WEBP_QUALITY is kept so
  the same skeleton can emit evidence images when real measurements land.

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow (pip install pillow)
"""
from __future__ import annotations

import os
import sys

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

FAMILY = "#4B67B4"   # PerryLink family accent (badges labelColor is #2B3245)
GREEN = {"light": "#16a34a", "dark": "#3fb950"}
SKIN = {
    "light": dict(bg="#ffffff", box="#f6f8fa", border="#d0d7de",
                  text="#1f2328", sub="#57606a"),
    "dark": dict(bg="#0d1117", box="#161b22", border="#30363d",
                 text="#f0f6fc", sub="#8b949e"),
}
WEBP_QUALITY = 90  # unused while there is no evidence dataset; kept for parity

# --- CJK font probe: any future Chinese label must never render as tofu ------
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei
    r"C:\Windows\Fonts\simhei.ttf",    # SimHei
    r"C:\Windows\Fonts\Deng.ttf",      # DengXian
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
if FONT_PATH is None:
    sys.exit("FATAL: no CJK font found (looked for msyh.ttc, simhei.ttf, "
             "Deng.ttf, Noto Sans CJK, PingFang). Refusing to render Chinese "
             "as tofu boxes; install one of the probed fonts and re-run.")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


# ---------------------------------------------------------------------------
# Hero flow SVG (light + dark). Tokens only — no prose sentence in the image.
# ---------------------------------------------------------------------------
FLOW_NODES = [
    ("worksheet", "JSON · YAML"),
    ("parse", "zh / en columns"),
    ("rules", "hazplan-check.yaml"),
    ("check", "warn · info"),
    ("hazplan_check", "issues + skipped"),
]


def flow_svg(skin: str) -> str:
    s = SKIN[skin]
    w, h = 1200, 400
    nw, nh, gap = 180, 96, 45
    y0 = 150
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="dsh-hazplan-check flow">',
        '<title>dsh-hazplan-check flow</title>',
        f'<rect width="{w}" height="{h}" rx="18" fill="{s["bg"]}"/>',
        f'<text x="60" y="62" fill="{s["text"]}" font-family="ui-sans-serif,'
        f'system-ui,sans-serif" font-size="30" font-weight="700">'
        f'dsh-hazplan-check</text>',
        f'<text x="60" y="94" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="16">HAZOP worksheet · rule pack · report'
        f'</text>',
        f'<line x1="60" y1="116" x2="1140" y2="116" stroke="{s["border"]}"/>',
    ]
    for i, (label, sub) in enumerate(FLOW_NODES):
        x = 60 + i * (nw + gap)
        accent = GREEN[skin] if i == len(FLOW_NODES) - 1 else (
            FAMILY if i == 2 else s["border"])
        parts.append(
            f'<rect x="{x}" y="{y0}" width="{nw}" height="{nh}" rx="14" '
            f'fill="{s["box"]}" stroke="{accent}" stroke-width="2"/>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 40}" fill="{s["text"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="16" font-weight="700">{label}</text>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 68}" fill="{s["sub"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="12">{sub}</text>')
        if i < len(FLOW_NODES) - 1:
            ax = x + nw + 6
            ay = y0 + nh // 2
            parts.append(
                f'<path d="M{ax} {ay}h{gap - 12}" stroke="{s["sub"]}" '
                f'stroke-width="3"/>')
            parts.append(
                f'<path d="M{ax + gap - 14} {ay - 7}l10 7-10 7" fill="none" '
                f'stroke="{s["sub"]}" stroke-width="3" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    # skipped branch: a check that cannot run is reported, never a silent pass
    sx, sy, sw, sh = 735, 290, 180, 52
    parts.append(
        f'<path d="M{sx + sw // 2} {y0 + nh}v{sy - y0 - nh}" '
        f'stroke="{FAMILY}" stroke-width="2" stroke-dasharray="5 5"/>')
    parts.append(
        f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="12" '
        f'fill="{s["box"]}" stroke="{FAMILY}" stroke-width="2"/>')
    parts.append(
        f'<text x="{sx + sw // 2}" y="{sy + 23}" fill="{s["text"]}" '
        f'text-anchor="middle" font-family="ui-monospace,monospace" '
        f'font-size="14" font-weight="700">skipped</text>')
    parts.append(
        f'<text x="{sx + sw // 2}" y="{sy + 42}" fill="{s["sub"]}" '
        f'text-anchor="middle" font-family="ui-monospace,monospace" '
        f'font-size="12">missing column</text>')
    parts.append(
        f'<text x="60" y="380" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="13">reads: [file] · writes: [] · '
        f'network: false · model: none</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    font(12)  # load-probe the CJK face; raises if the file is unusable
    for skin in ("light", "dark"):
        path = os.path.join(OUT, f"dsh-hazplan-check-flow-{skin}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(flow_svg(skin))
    print("wrote 2 SVG assets to docs/assets/ (no evidence chart: no "
          "benchmark data in this repository)")


if __name__ == "__main__":
    main()
