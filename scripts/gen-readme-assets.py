#!/usr/bin/env python3
"""README visuals for dsh-hazplan-check — drawn from this plugin's real run.

Two figures, both read off the shipped source and rule pack:

  hero 1440×576 (Pillow, four files: zh/en × light/dark)
      The worksheet itself, excerpted. Two rows of the repository's own sample
      material sit under the sheet's own column names (节点 / 工艺参数 / 引导词 /
      偏差 / 原因). Row 1 has an empty 原因 (HZ-001, clause 6.6.4). Row 2 writes
      「液位高」 against parameter 流量 and guide word 无 (HZ-007: the literal
      composition the rule compares is 流量 ⊕ 无 → 无流量). The header carries a
      declared subject, which is what HZ-006 reads. Under the rows is the
      derivation the pack actually performs, and then the two report channels.

  flow 1100×660 (hand-written SVG, two files: light/dark)
      A scorecard, not a row of boxes. The material becomes one WorksheetInput
      (left lane: JSON/YAML → parseMaterial() → rows[] / columns[] / warnings[]).
      Three sample rows then meet six row-level rules on a grid — every cell is
      that row's outcome under that rule: × difference → issues[], √ no
      difference → neither channel, – skipped → skipped[]. HZ-006 is a
      header-level check, so it occupies its own band above the rows. The HZ-007
      derivation (参数 ⊕ 引导词 → 偏差) is spelled out in a dashed detail strip,
      and the two channels feed buildView()'s projection: markdown / reportJson /
      counts, with the verdict left to the reviewer.

Every outcome in both figures was produced by running this repository's own
src/check.ts over those three rows (subject 「某装置 HAZOP 分析」, riskLevels
unset): warn 3, info 0, error 0; issues = HZ-001 row 1 (原因), HZ-002 row 3
(节点), HZ-007 row 2 (偏差); skipped = HZ-005 (riskLevels 未配置), HZ-003,
HZ-004, HZ-006 (precondition met, no difference). No invented data.

Run:  python scripts/gen-readme-assets.py
Needs: Pillow + the Windows faces msyh.ttc / msyhbd.ttc / consola.ttf /
       consolab.ttf. A missing face aborts instead of shipping tofu boxes.
"""
from __future__ import annotations

import math
import os
from html import escape

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")
NAME = "dsh-hazplan-check"

FONT_CJK = r"C:\Windows\Fonts\msyh.ttc"
FONT_CJK_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"
FONT_MONO_BOLD = r"C:\Windows\Fonts\consolab.ttf"
FONT_FILES = {"cjk": FONT_CJK, "cjk_bold": FONT_CJK_BOLD,
              "mono": FONT_MONO, "mono_bold": FONT_MONO_BOLD}
for _path in FONT_FILES.values():
    if not os.path.exists(_path):
        raise SystemExit(f"FATAL: font missing: {_path}")

RADIUS = 20
SHADOW = 22

SKIN = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        card="#ffffff", edge="#e6e2ef",
        text="#141419", sub="#4d5261", faint="#8b90a0",
        accent="#4B67B4", accent_soft="#ece7f9",
        mark="#b45309", mark_bg="#fdf3e9", mark_edge="#e8b483",
        ok="#15803d", ok_bg="#e8f5ec", ok_edge="#9dcdb0",
        band="#f5f2fb", band_alt="#faf8fe", grid="#e3dfee",
        shadow=(34, 27, 70), glow="#7a68c9",
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        card="#1b2231", edge="#2e374b",
        text="#f0f3f9", sub="#a8b1c4", faint="#7c8497",
        accent="#8496f5", accent_soft="#242d42",
        mark="#e0a44e", mark_bg="#2a2216", mark_edge="#7a5a24",
        ok="#4bc46c", ok_bg="#16281d", ok_edge="#2f6b41",
        band="#202839", band_alt="#1e2534", grid="#2b3348",
        shadow=(0, 0, 0), glow="#8496f5",
    ),
}

_SCRATCH = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def font(size: float, kind: str = "cjk_bold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_FILES[kind], int(round(size)))


def hx(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def tw(text: str, size: float, kind: str = "cjk") -> float:
    return _SCRATCH.textlength(text, font=font(size, kind))


def require_w(text: str, size: float, kind: str, max_w: float,
              what: str) -> None:
    width = tw(text, size, kind)
    if width > max_w + 0.4:
        raise SystemExit(f"FATAL: {what} overflows: {text!r} needs "
                         f"{width:.1f}px > {max_w}px")


def fit(text: str, kind: str, max_w: float, start: int, minimum: int) -> int:
    size = start
    while size > minimum:
        if tw(text, size, kind) <= max_w:
            return size
        size -= 1
    if tw(text, minimum, kind) > max_w + 0.4:
        raise SystemExit(f"FATAL: text does not fit {max_w}px at >= {minimum}px:"
                         f" {text!r}")
    return minimum


def fit_lines(lines: list[str], kind: str, max_w: float, start: int,
              minimum: int) -> int:
    return min(fit(line, kind, max_w, start, minimum) for line in lines)


def gradient(width: int, height: int, c1: str, c2: str) -> Image.Image:
    base = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(base)
    a, b = hx(c1), hx(c2)
    for y in range(height):
        t = 0.12 * (y / height) + 0.88 * (y / height) ** 1.3
        draw.line([(0, y), (width, y)],
                  fill=tuple(int(round(p + (q - p) * t)) for p, q in zip(a, b)))
    return base


def glow(img: Image.Image, cx: int, cy: int, radius: int, color: str,
         alpha: int = 30) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rgb = hx(color)
    for i in range(10, 0, -1):
        r = radius * i / 10
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=rgb + (int(alpha * (1 - i / 11)),))
    layer = layer.filter(ImageFilter.GaussianBlur(18))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def card(img: Image.Image, box: tuple, s: dict, radius: int = RADIUS,
         shadow: int = SHADOW, fill: str | None = None,
         edge: str | None = None) -> Image.Image:
    """A soft-shadowed rounded card on the gradient background."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for i in range(shadow, 0, -2):
        alpha = int(9 * (1 - i / shadow))
        if alpha <= 0:
            continue
        draw.rounded_rectangle([x0 - i // 7, y0 + i // 4, x1 + i // 7, y1 + i],
                               radius=radius + i // 4,
                               fill=s["shadow"] + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(10))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(box, radius=radius, fill=hx(fill or s["card"]),
                           outline=hx(edge or s["edge"]), width=2)
    return img


def dash_rect(draw: ImageDraw.ImageDraw, box: tuple, color: str,
              width: int = 2, dash: int = 7, gap: int = 5) -> None:
    x0, y0, x1, y1 = box
    for a, b in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)),
                 ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if length == 0:
            continue
        count = int(length // (dash + gap)) + 1
        for i in range(count):
            t0 = i * (dash + gap) / length
            t1 = min((i * (dash + gap) + dash) / length, 1.0)
            if t0 >= 1:
                break
            draw.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                       (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)],
                      fill=hx(color), width=width)


def pill(img: Image.Image, xy: tuple, text: str, s: dict, size: float = 17,
         fg: str | None = None, bg: str | None = None,
         kind: str = "cjk_bold", pad: int = 16) -> tuple[int, int]:
    draw = ImageDraw.Draw(img)
    face = font(size, kind)
    width = draw.textlength(text, font=face)
    x, y = xy
    box_h = int(size * 1.95)
    draw.rounded_rectangle([x, y, x + width + pad * 2, y + box_h],
                           radius=box_h // 2,
                           fill=hx(bg or s["accent_soft"]))
    draw.text((x + pad, y + box_h / 2), text, font=face,
              fill=hx(fg or s["accent"]), anchor="lm")
    return int(x + width + pad * 2), int(y + box_h)


def chip(img: Image.Image, x: int, y: int, text: str, s: dict, size: float = 11,
         fg: str | None = None, bg: str | None = None,
         kind: str = "cjk_bold", anchor: str = "left", pad: int = 9,
         height: int = 21) -> int:
    draw = ImageDraw.Draw(img)
    face = font(size, kind)
    width = draw.textlength(text, font=face)
    box_w = width + pad * 2
    x0 = int(x - box_w) if anchor == "right" else int(x)
    draw.rounded_rectangle([x0, y, x0 + box_w, y + height],
                           radius=height // 2,
                           fill=hx(bg or s["band"]))
    draw.text((x0 + pad, y + height / 2), text, font=face,
              fill=hx(fg or s["sub"]), anchor="lm")
    return int(box_w)


# ---------------------------------------------------------------------------
# Hero — 1440 × 576, four files (zh/en × light/dark)
# ---------------------------------------------------------------------------
HERO_W, HERO_H = 1440, 576
LEFT_X = 64
LEFT_W = 776
RIGHT_X0, RIGHT_X1 = 868, 1376
RIGHT_W = RIGHT_X1 - RIGHT_X0          # 508
INNER_X = RIGHT_X0 + 20                # 888
INNER_W = RIGHT_W - 40                 # 468

HERO = {
    "zh": dict(
        kicker="DeepSeek Harness 插件 · 核对器",
        value=["七条规则逐行核对一份 HAZOP 工作表，",
               "哪一行、哪一栏、差什么，一次列清。"],
        sub="只列材料内部能逐条指认的差异；合规与责任判断留给分析小组。",
        meta="HZ-001…HZ-007 · 0 error · skipped 逐条写明原因",
        foot="Apache-2.0 · DeepSeek Harness 插件家族 · 只读 · 不联网",
        t1="工作表 · 两行样例",
        t1_chip="只读原件",
        head_label="表头 subject 已声明",
        head_value="某装置 HAZOP 分析",
        head_rule="HZ-006",
        cols=["节点", "工艺参数", "引导词", "偏差", "原因"],
        row1=["进料单元", "流量", "无", "无流量", "（空）"],
        row2=["进料单元", "流量", "无", "液位高", "进料泵故障"],
        t1_rules="本图两处差异：HZ-001 原因空、HZ-007 偏差≠参数⊕引导词",
        t1_note="列名中英文都认，大小写 / 空格 / _ 归一",
        t2="偏差 = 工艺参数 ⊕ 引导词",
        t2_chip="HZ-007",
        parameter="流量",
        guide="无",
        l_parameter="工艺参数",
        l_guide="引导词",
        l_should="应写",
        l_written="表里写",
        should="无流量",
        written="液位高",
        neq="与应写值不符",
        t2_note="只做字面组合比对；命中提示可能复制粘贴串行",
        c_issue="issues[] 差异",
        c_issue_sub="行号 + 栏名 + 应填",
        c_skip="skipped[] 未执行",
        c_skip_sub="每条写明规则与原因",
        c_note="空 issues ≠ 全部通过：先读 skipped",
    ),
    "en": dict(
        kicker="DeepSeek Harness plugin · checker",
        value=["Seven rules read one HAZOP worksheet;",
               "which row, which column, what is missing."],
        sub="Differences only — compliance and blame stay with the team.",
        meta="HZ-001…HZ-007 · no errors by design · every skip explained",
        foot="Apache-2.0 · DeepSeek Harness plugin family · read-only · offline",
        t1="Worksheet · two sample rows",
        t1_chip="read-only",
        head_label="Header subject declared",
        head_value="某装置 HAZOP 分析",
        head_rule="HZ-006",
        cols=["节点", "工艺参数", "引导词", "偏差", "原因"],
        row1=["进料单元", "流量", "无", "无流量", "（空）"],
        row2=["进料单元", "流量", "无", "液位高", "进料泵故障"],
        t1_rules="Marked: HZ-001 cause empty, HZ-007 deviation ≠ parameter ⊕ guide word",
        t1_note="Chinese or English column names; case and spacing ignored",
        t2="Deviation = parameter ⊕ guide word",
        t2_chip="HZ-007",
        parameter="流量",
        guide="无",
        l_parameter="parameter",
        l_guide="guide word",
        l_should="should read",
        l_written="sheet says",
        should="无流量",
        written="液位高",
        neq="not the expected value",
        t2_note="Literal comparison only; a hit suggests a copy-paste slip",
        c_issue="issues[] differences",
        c_issue_sub="row + column + expected",
        c_skip="skipped[] not run",
        c_skip_sub="rule and reason stated",
        c_note="empty issues ≠ all clear: read skipped first",
    ),
}


def hero(lang: str, skin: str) -> None:
    s = SKIN[skin]
    h = HERO[lang]
    img = gradient(HERO_W, HERO_H, s["bg_from"], s["bg_to"])
    img = glow(img, 1180, 20, 380, s["glow"], 26 if skin == "light" else 40)
    img = glow(img, 90, 560, 260, s["glow"], 10 if skin == "light" else 18)

    d = ImageDraw.Draw(img)

    # ---- left column: kicker / title / value / sub / meta / footer --------
    kicker_size = 17.5
    require_w(h["kicker"], kicker_size, "cjk_bold", LEFT_W, "hero kicker")
    pill(img, (LEFT_X, 52), h["kicker"], s, size=kicker_size)
    d = ImageDraw.Draw(img)

    title_size = fit(NAME, "mono_bold", LEFT_W, 84, 79)
    if title_size * 880 / HERO_W < 48:
        raise SystemExit("FATAL: hero title below 48px at 880px width")
    d.text((LEFT_X - 2, 208), NAME, font=font(title_size, "mono_bold"),
           fill=hx(s["text"]), anchor="ls")

    value_size = fit_lines(h["value"], "cjk_bold", LEFT_W, 34, 30)
    for i, line in enumerate(h["value"]):
        require_w(line, value_size, "cjk_bold", LEFT_W, f"hero value {i}")
        d.text((LEFT_X, 272 + i * 50), line, font=font(value_size, "cjk_bold"),
               fill=hx(s["text"]), anchor="ls")

    sub_size = fit(h["sub"], "cjk", LEFT_W, 25, 24)
    if sub_size * 880 / HERO_W < 15:
        raise SystemExit("FATAL: hero subtitle below 15px at 880px width")
    d.text((LEFT_X, 378), h["sub"], font=font(sub_size, "cjk"),
           fill=hx(s["sub"]), anchor="ls")

    meta_size = 20
    require_w(h["meta"], meta_size, "cjk", LEFT_W, "hero meta")
    if meta_size * 880 / HERO_W < 12:
        raise SystemExit("FATAL: hero meta below 12px at 880px width")
    d.text((LEFT_X, 430), h["meta"], font=font(meta_size, "cjk"),
           fill=hx(s["faint"]), anchor="ls")

    foot_size = 19
    require_w(h["foot"], foot_size, "cjk", LEFT_W, "hero footer")
    d.line([LEFT_X, 466, LEFT_X + LEFT_W - 12, 466], fill=hx(s["grid"]),
           width=2)
    d.text((LEFT_X, 504), h["foot"], font=font(foot_size, "cjk"),
           fill=hx(s["faint"]), anchor="ls")

    # ---- right card 1: the worksheet excerpt ------------------------------
    img = card(img, (RIGHT_X0, 44, RIGHT_X1, 280), s)
    d = ImageDraw.Draw(img)
    d.text((INNER_X, 64), h["t1"], font=font(13.5, "cjk_bold"),
           fill=hx(s["accent"]), anchor="ls")
    chip(img, RIGHT_X1 - 20, 54, h["t1_chip"], s, size=11, anchor="right")
    d = ImageDraw.Draw(img)

    # header strip — what HZ-006 reads
    d.rounded_rectangle([INNER_X - 4, 78, RIGHT_X1 - 20, 110], radius=9,
                        fill=hx(s["band"]))
    require_w(h["head_label"], 11, "cjk", 142, "hero header label")
    d.text((INNER_X + 6, 94), h["head_label"], font=font(11, "cjk"),
           fill=hx(s["sub"]), anchor="ls")
    require_w(h["head_value"], 11.5, "cjk", 150, "hero subject value")
    d.text((INNER_X + 152, 94), h["head_value"], font=font(11.5, "cjk"),
           fill=hx(s["text"]), anchor="ls")
    require_w(f'{h["head_rule"]} √', 11, "mono_bold", 80, "hero header rule")
    d.text((RIGHT_X1 - 26, 94), f'{h["head_rule"]} √',
           font=font(11, "mono_bold"), fill=hx(s["ok"]), anchor="rs")

    col_x = [INNER_X, INNER_X + 92, INNER_X + 176, INNER_X + 242,
             INNER_X + 342]
    col_w = [92, 84, 66, 100, 106]
    for i, name in enumerate(h["cols"]):
        require_w(name, 12, "cjk", col_w[i] - 6, "hero column header")
        d.text((col_x[i], 134), name, font=font(12, "cjk"),
               fill=hx(s["sub"]), anchor="ls")

    row_top = [144, 188]
    rows = [h["row1"], h["row2"]]
    for r in range(len(rows)):
        d.line([INNER_X - 4, row_top[r], RIGHT_X1 - 20, row_top[r]],
               fill=hx(s["grid"]), width=1)

    # ring the two cells the rules report on, before their text is drawn
    cell1 = (col_x[4] - 5, row_top[0] + 3, col_x[4] + col_w[4] - 4,
             row_top[0] + 41)
    cell2 = (col_x[3] - 5, row_top[1] + 3, col_x[3] + col_w[3] - 4,
             row_top[1] + 41)
    for box in (cell1, cell2):
        d.rounded_rectangle(box, radius=9, fill=hx(s["mark_bg"]))
        dash_rect(d, box, s["mark_edge"], width=2, dash=6, gap=4)

    for r, values in enumerate(rows):
        top = row_top[r]
        for i, value in enumerate(values):
            hot = (r == 0 and i == 4) or (r == 1 and i == 3)
            require_w(value, 14, "cjk", col_w[i] - 8, "hero table cell")
            d.text((col_x[i], top + 27), value, font=font(14, "cjk"),
                   fill=hx(s["mark"] if hot else s["text"]), anchor="ls")

    d.line([INNER_X - 4, 232, RIGHT_X1 - 20, 232], fill=hx(s["grid"]), width=1)
    require_w(h["t1_note"], 11.5, "cjk", INNER_W, "hero table note")
    d.text((INNER_X, 248), h["t1_note"], font=font(11.5, "cjk"),
           fill=hx(s["faint"]), anchor="ls")
    require_w(h["t1_rules"], 11, "cjk", INNER_W, "hero table rule note")
    d.text((INNER_X, 264), h["t1_rules"], font=font(11, "cjk"),
           fill=hx(s["mark"]), anchor="ls")

    # ---- right card 2: the derivation -------------------------------------
    img = card(img, (RIGHT_X0, 292, RIGHT_X1, 458), s)
    d = ImageDraw.Draw(img)
    require_w(h["t2"], 13.5, "cjk_bold", 330, "hero derivation title")
    d.text((INNER_X, 312), h["t2"], font=font(13.5, "cjk_bold"),
           fill=hx(s["accent"]), anchor="ls")
    chip(img, RIGHT_X1 - 20, 302, h["t2_chip"], s, size=11, anchor="right")
    d = ImageDraw.Draw(img)

    for label, x, max_w in ((h["l_parameter"], 0, 96), (h["l_guide"], 102, 92),
                            (h["l_should"], 196, 104)):
        require_w(label, 11, "cjk", max_w, "hero equation label")
        d.text((INNER_X + x, 336), label, font=font(11, "cjk"),
               fill=hx(s["faint"]), anchor="ls")

    def operand(box: tuple, text: str, fill: str, edge: str,
                text_fill: str) -> None:
        d.rounded_rectangle(box, radius=9, fill=hx(fill), outline=hx(edge),
                            width=2)
        d.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), text,
               font=font(15, "cjk_bold"), fill=hx(text_fill), anchor="mm")

    operand((INNER_X, 346, INNER_X + 92, 378), h["parameter"], s["band"],
            s["grid"], s["text"])
    d.text((INNER_X + 112, 362), "⊕", font=font(16, "cjk"), fill=hx(s["sub"]),
           anchor="mm")
    operand((INNER_X + 128, 346, INNER_X + 176, 378), h["guide"], s["band"],
            s["grid"], s["text"])
    d.text((INNER_X + 192, 362), "→", font=font(16, "cjk"), fill=hx(s["accent"]),
           anchor="mm")
    operand((INNER_X + 208, 346, INNER_X + 300, 378), h["should"], s["ok_bg"],
            s["ok_edge"], s["ok"])
    d.text((INNER_X + 282, 362), "√", font=font(14, "cjk_bold"),
           fill=hx(s["ok"]), anchor="ls")

    require_w(h["l_written"], 11, "cjk", 58, "hero written label")
    d.text((INNER_X, 412), h["l_written"], font=font(11, "cjk"),
           fill=hx(s["faint"]), anchor="ls")
    wrong = (INNER_X + 62, 394, INNER_X + 154, 430)
    d.rounded_rectangle(wrong, radius=9, fill=hx(s["mark_bg"]))
    dash_rect(d, wrong, s["mark_edge"], width=2, dash=6, gap=4)
    d.text(((wrong[0] + wrong[2]) / 2, (wrong[1] + wrong[3]) / 2), h["written"],
           font=font(15, "cjk_bold"), fill=hx(s["mark"]), anchor="mm")
    require_w(h["neq"], 11.5, "cjk_bold", 170, "hero inequality")
    d.text((INNER_X + 172, 412), f'× {h["neq"]}',
           font=font(11.5, "cjk_bold"), fill=hx(s["mark"]), anchor="ls")
    require_w(h["t2_note"], 11, "cjk", INNER_W, "hero derivation note")
    d.text((INNER_X, 446), h["t2_note"], font=font(11, "cjk"),
           fill=hx(s["faint"]), anchor="ls")

    # ---- right card 3: the two channels -----------------------------------
    img = card(img, (RIGHT_X0, 468, RIGHT_X1, 544), s)
    d = ImageDraw.Draw(img)
    require_w(h["c_issue"], 13, "cjk_bold", 200, "hero issues title")
    d.text((INNER_X, 490), h["c_issue"], font=font(13, "cjk_bold"),
           fill=hx(s["accent"]), anchor="ls")
    require_w(h["c_issue_sub"], 11, "cjk", 210, "hero issues sub")
    d.text((INNER_X, 510), h["c_issue_sub"], font=font(11, "cjk"),
           fill=hx(s["sub"]), anchor="ls")
    d.line([INNER_X + 230, 480, INNER_X + 230, 532], fill=hx(s["grid"]),
           width=1)
    require_w(h["c_skip"], 13, "cjk_bold", 180, "hero skip title")
    d.text((INNER_X + 250, 490), h["c_skip"], font=font(13, "cjk_bold"),
           fill=hx(s["sub"]), anchor="ls")
    require_w(h["c_skip_sub"], 11, "cjk", 190, "hero skip sub")
    d.text((INNER_X + 250, 510), h["c_skip_sub"], font=font(11, "cjk"),
           fill=hx(s["sub"]), anchor="ls")
    require_w(h["c_note"], 11, "cjk", INNER_W, "hero channel note")
    d.text((INNER_X, 530), h["c_note"], font=font(11, "cjk"),
           fill=hx(s["mark"]), anchor="ls")

    name = f"{NAME}-hero-{lang}-{skin}.webp"
    img.save(os.path.join(OUT, name), "WEBP", quality=92, method=6)
    print(f"wrote {name} ({HERO_W}×{HERO_H})")


# ---------------------------------------------------------------------------
# Flow — 1100 × 660, hand-written SVG (light + dark)
# ---------------------------------------------------------------------------
FLOW_W, FLOW_H = 1100, 660

FLOW = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        panel="#ffffff", edge="#e6e2ef",
        band="#f5f2fb", band_alt="#faf8fe", grid="#e3dfee",
        text="#141419", sub="#4d5261", faint="#8b90a0",
        accent="#4B67B4", accent_soft="#ece7f9",
        ok="#15803d", ok_bg="#e8f5ec", ok_edge="#9dcdb0",
        mark="#b45309", mark_bg="#fdf3e9", mark_edge="#e8b483",
        shadow="#3a2c66", shadow_op="0.10",
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        panel="#1b2231", edge="#2e374b",
        band="#202839", band_alt="#1e2534", grid="#2b3348",
        text="#f0f3f9", sub="#a8b1c4", faint="#7c8497",
        accent="#8496f5", accent_soft="#242d42",
        ok="#4bc46c", ok_bg="#16281d", ok_edge="#2f6b41",
        mark="#e0a44e", mark_bg="#2a2216", mark_edge="#7a5a24",
        shadow="#000000", shadow_op="0.45",
    ),
}

FONT_CSS_CJK = ("'Microsoft YaHei','PingFang SC','Noto Sans CJK SC',"
                "'Source Han Sans SC',sans-serif")
FONT_CSS_MONO = ("'Consolas','SFMono-Regular','Menlo',ui-monospace,monospace")

# rule id, read face (the column header)
RULES = [
    ("HZ-001", "必填栏"),
    ("HZ-002", "节点"),
    ("HZ-003", "引导词表"),
    ("HZ-004", "偏差/参数"),
    ("HZ-005", "风险档位"),
    ("HZ-007", "偏差推导"),
]

# row label, sheet row, outcome per RULES, short note for its issue cell
SAMPLE_ROWS = [
    ("第 1 行", "进料单元",
     ["issue", "clean", "clean", "clean", "skip", "clean"], "缺原因"),
    ("第 2 行", "进料单元",
     ["clean", "clean", "clean", "clean", "skip", "issue"], "组合不符"),
    ("第 3 行", "（无节点）",
     ["clean", "issue", "clean", "clean", "skip", "clean"], "节点空"),
]

# rule, locator, short finding
ISSUES = [
    ("HZ-001", "第 1 行", "缺少 原因"),
    ("HZ-002", "第 3 行 · 节点", "1 行未写节点（行 3）"),
    ("HZ-007", "第 2 行 · 偏差", "「液位高」≠ 流量⊕无"),
]


class Svg:
    """Tiny SVG writer that measures every label before it is emitted."""

    def __init__(self, skin: str) -> None:
        self.s = FLOW[skin]
        self.parts: list[str] = []
        self.overflows: list[str] = []

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def text(self, x: float, y: float, content: str, size: float, fill: str, *,
             anchor: str = "start", weight: int | None = None,
             mono: bool = False, max_w: float | None = None,
             opacity: float | None = None) -> None:
        kind = ("mono" if mono else "cjk") + ("_bold" if weight else "")
        if mono and weight:
            kind = "mono_bold"
        if max_w is not None:
            width = tw(content, size, kind)
            if width > max_w + 0.4:
                self.overflows.append(
                    f"{content!r} needs {width:.1f}px > {max_w}px")
        family = FONT_CSS_MONO if mono else FONT_CSS_CJK
        attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill}"',
                 f'font-family="{family}"', f'font-size="{size}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if weight:
            attrs.append(f'font-weight="{weight}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.add(f'<text {" ".join(attrs)}>{escape(content)}</text>')

    def rect(self, x: float, y: float, w: float, h: float, *, fill: str,
             rx: float = 0, stroke: str | None = None, sw: float = 1.5,
             shadow: bool = False, dash: str | None = None,
             opacity: float | None = None) -> None:
        attrs = [f'x="{x}"', f'y="{y}"', f'width="{w}"', f'height="{h}"']
        if rx:
            attrs.append(f'rx="{rx}"')
        attrs.append(f'fill="{fill}"')
        if stroke:
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{sw}"')
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        if shadow:
            attrs.append('filter="url(#soft)"')
        self.add(f'<rect {" ".join(attrs)}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, *, stroke: str,
             sw: float = 1.5, dash: str | None = None,
             opacity: float | None = None) -> None:
        attrs = [f'x1="{x1}"', f'y1="{y1}"', f'x2="{x2}"', f'y2="{y2}"',
                 f'stroke="{stroke}"', f'stroke-width="{sw}"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.add(f'<line {" ".join(attrs)}/>')

    def path(self, d: str, *, stroke: str, sw: float = 1.5,
             marker: str | None = None, dash: str | None = None,
             fill: str = "none", opacity: float | None = None) -> None:
        attrs = [f'd="{d}"', f'fill="{fill}"', f'stroke="{stroke}"',
                 f'stroke-width="{sw}"', 'stroke-linecap="round"',
                 'stroke-linejoin="round"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if marker:
            attrs.append(f'marker-end="url(#{marker})"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        self.add(f'<path {" ".join(attrs)}/>')

    def arrow(self, x1: float, y1: float, x2: float, y2: float, *,
              stroke: str, sw: float = 1.6, marker: str = "arr") -> None:
        self.path(f"M{x1} {y1} L{x2} {y2}", stroke=stroke, sw=sw,
                  marker=marker)

    def chip(self, x: float, y: float, text: str, *, size: float = 11,
             fg: str, bg: str, mono: bool = False, weight: int | None = 700,
             pad: float = 9, h: float = 22, anchor: str = "start") -> float:
        kind = ("mono" if mono else "cjk") + ("_bold" if weight else "")
        if mono and weight:
            kind = "mono_bold"
        width = tw(text, size, kind) + pad * 2
        x0 = x - width if anchor == "end" else x
        self.rect(x0, y, width, h, fill=bg, rx=h / 2)
        self.text(x0 + pad, y + h / 2 + size * 0.36, text, size, fg,
                  mono=mono, weight=weight, max_w=width - pad * 2)
        return width

    def svg(self, width: int, height: int, label: str) -> str:
        s = self.s
        head = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
            f'aria-label="{escape(label)}">',
            f'<title>{escape(label)}</title>',
            "<defs>",
            f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{s["bg_from"]}"/>'
            f'<stop offset="1" stop-color="{s["bg_to"]}"/></linearGradient>',
            f'<filter id="soft" x="-20%" y="-20%" width="140%" height="150%">'
            f'<feDropShadow dx="0" dy="6" stdDeviation="9" '
            f'flood-color="{s["shadow"]}" '
            f'flood-opacity="{s["shadow_op"]}"/></filter>',
            f'<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M1 1 L9 5 L1 9 z" fill="{s["accent"]}"/></marker>',
            "</defs>",
            f'<rect width="{width}" height="{height}" rx="22" fill="url(#bg)"/>',
        ]
        return "\n".join(head + self.parts + ["</svg>"]) + "\n"


def flow_svg(skin: str) -> str:
    s = FLOW[skin]
    v = Svg(skin)

    # ---- header ------------------------------------------------------------
    v.text(44, 50, NAME, 16, s["text"], weight=700, mono=True, max_w=170)
    v.text(218, 50, "结构图 · 一张示例表的一次运行", 13, s["sub"], max_w=320)
    v.text(1056, 48, "GB/T 35320-2017 · 表1 · 表2 · 附录 A.2", 11, s["sub"],
           anchor="end", max_w=330)
    v.text(1056, 68, "0 error · 推荐性条款 → 严重级封顶 warn / info", 11,
           s["faint"], anchor="end", max_w=360)
    v.text(44, 72, "材料 → parseMaterial() → 七条规则 → issues[] / skipped[] "
                   "→ buildView()", 11.5, s["faint"], max_w=600)
    v.line(44, 88, 1056, 88, stroke=s["grid"], sw=1)

    # ---- left lane: the material ------------------------------------------
    v.rect(44, 100, 196, 424, fill=s["panel"], rx=18, stroke=s["edge"],
           sw=1.5, shadow=True)
    lane = 60

    def section(y: float, title: str) -> None:
        v.rect(lane, y - 12, 4, 14, fill=s["accent"], rx=2)
        v.text(lane + 12, y, title, 13, s["text"], weight=700, max_w=150)

    section(124, "材料")
    v.text(lane, 152, "JSON · YAML", 12, s["accent"], mono=True, max_w=164)
    v.text(lane, 172, "subject · revision", 11, s["sub"], mono=True, max_w=164)
    v.text(lane, 192, "rows[]", 11, s["sub"], mono=True, max_w=164)
    v.text(lane, 210, "（file 或 material）", 11, s["faint"], max_w=164)

    v.line(lane, 226, 224, 226, stroke=s["grid"], sw=1, dash="4 5")
    v.arrow(142, 232, 142, 248, stroke=s["accent"], sw=1.4)

    section(276, "parseMaterial()")
    v.text(lane, 302, "列名中英文都认", 11, s["sub"], max_w=164)
    v.text(lane, 320, "大小写 / 空格 / _ 归一", 11, s["sub"], max_w=164)
    v.text(lane, 344, "空表 · 无已知列", 11, s["mark"], max_w=164)
    v.text(lane, 362, "→ MaterialError", 11, s["mark"], max_w=164)

    v.line(lane, 380, 224, 380, stroke=s["grid"], sw=1, dash="4 5")
    v.arrow(142, 386, 142, 402, stroke=s["accent"], sw=1.4)

    section(428, "WorksheetInput")
    v.text(lane, 452, "rows[N] · columns[]", 11, s["sub"], mono=True, max_w=164)
    v.text(lane, 470, "subject? · warnings[]", 11, s["sub"], mono=True,
           max_w=164)
    v.text(lane, 492, "缺 subject 只警告", 11, s["faint"], max_w=164)
    v.text(lane, 510, "不中断读取", 11, s["faint"], max_w=164)

    v.arrow(240, 300, 257, 300, stroke=s["accent"], sw=1.8)

    # ---- scorecard ---------------------------------------------------------
    v.rect(260, 100, 796, 286, fill=s["panel"], rx=18, stroke=s["edge"],
           sw=1.5, shadow=True)
    v.text(276, 122, "核对矩阵 · 三行示例表", 14, s["text"], weight=700,
           max_w=300)
    v.text(276, 142, "每个单元格 = 该行在该条规则下的结果（样例取自 "
           "tests/fixtures）", 11, s["faint"], max_w=430)
    v.chip(1040, 110, "3 warn · 4 skipped", size=11, fg=s["accent"],
           bg=s["accent_soft"], anchor="end")

    # HZ-006 reads the header, not a row: its own band above the grid
    v.rect(276, 156, 764, 30, fill=s["band"], rx=9)
    v.text(290, 176, "表头 · subject 已声明「某装置 HAZOP 分析」", 11, s["sub"],
           max_w=470)
    v.text(1026, 176, "HZ-006 √", 11, s["ok"], weight=700, mono=True,
           anchor="end", max_w=90)

    v.text(276, 210, "样例行", 11, s["faint"], max_w=90)
    col0, cell_w, gap = 404, 100, 6
    for i, (rule, face) in enumerate(RULES):
        x = col0 + i * (cell_w + gap)
        v.text(x + cell_w / 2, 204, rule, 13,
               s["faint"] if i == 4 else s["accent"], weight=700, mono=True,
               anchor="middle", max_w=cell_w - 8)
        v.text(x + cell_w / 2, 221, face, 11, s["sub"], anchor="middle",
               max_w=cell_w - 8)

    row_top, row_h = 228, 40
    for r, (label, node, outcomes, issue_tag) in enumerate(SAMPLE_ROWS):
        top = row_top + r * row_h
        v.line(276, top, 1040, top, stroke=s["grid"], sw=1)
        v.text(288, top + 17, label, 11, s["sub"], weight=700, mono=True,
               max_w=80)
        v.text(288, top + 34, node, 11,
               s["mark"] if node.startswith("（") else s["text"], max_w=106)
        for i, outcome in enumerate(outcomes):
            x = col0 + i * (cell_w + gap)
            if outcome == "clean":
                v.rect(x, top + 5, cell_w, 31, fill=s["band_alt"], rx=8)
                v.text(x + cell_w / 2, top + 26, "√", 13, s["ok"],
                       weight=700, anchor="middle")
            elif outcome == "skip":
                v.rect(x, top + 5, cell_w, 31, fill=s["band_alt"], rx=8,
                       stroke=s["grid"], sw=1, dash="4 3")
                v.text(x + 12, top + 26, "–", 13, s["faint"], weight=700,
                       mono=True)
                v.text(x + 26, top + 25, "未配置", 11, s["faint"], max_w=66)
            else:
                v.rect(x, top + 5, cell_w, 31, fill=s["mark_bg"], rx=8,
                       stroke=s["mark_edge"], sw=1)
                v.text(x + 12, top + 26, "×", 13, s["mark"], weight=700,
                       anchor="middle")
                v.text(x + 26, top + 25, issue_tag, 11, s["mark"], max_w=70)
    v.line(276, row_top + 3 * row_h, 1040, row_top + 3 * row_h,
           stroke=s["grid"], sw=1)

    # legend — a rule that ran clean is still reported in skipped[]
    ly = 370
    v.text(280, ly, "×", 12, s["mark"], weight=700, anchor="middle")
    v.text(292, ly - 1, "差异 → issues[]", 11, s["sub"], max_w=110)
    v.text(430, ly, "√", 12, s["ok"], weight=700, anchor="middle")
    v.text(442, ly - 1, "已执行、无差异 → 进 skipped[]", 11, s["sub"],
           max_w=190)
    v.text(650, ly, "–", 12, s["faint"], weight=700, anchor="middle")
    v.text(662, ly - 1, "未执行 → skipped[]（写明原因）", 11, s["sub"],
           max_w=250)

    # ---- HZ-007 detail strip (dashed: an inset, not a pipeline stage) ------
    v.rect(260, 402, 340, 122, fill=s["panel"], rx=16, stroke=s["accent"],
           sw=1.4, dash="6 5")
    v.text(276, 426, "偏差 = 工艺参数 ⊕ 引导词", 13, s["accent"], weight=700,
           max_w=240)
    v.chip(584, 414, "HZ-007 细节", size=11, fg=s["accent"],
           bg=s["accent_soft"], anchor="end", mono=True)
    v.text(276, 444, "工艺参数", 11, s["faint"], max_w=60)
    v.text(362, 444, "引导词", 11, s["faint"], max_w=40)
    v.text(428, 444, "应写", 11, s["faint"], max_w=36)

    def operand(x: float, text: str, fg: str, bg: str, edge: str,
                width: float) -> None:
        v.rect(x, 452, width, 30, fill=bg, rx=8, stroke=edge, sw=1.4)
        v.text(x + width / 2, 472, text, 12, fg, weight=700, anchor="middle",
               max_w=width - 8)

    operand(276, "流量", s["text"], s["band"], s["grid"], 64)
    v.text(352, 472, "⊕", 12, s["sub"], anchor="middle")
    operand(362, "无", s["text"], s["band"], s["grid"], 42)
    v.text(414, 472, "→", 12, s["accent"], anchor="middle")
    operand(428, "无流量", s["ok"], s["ok_bg"], s["ok_edge"], 72)
    v.text(276, 500, "表里写「液位高」≠ 流量⊕无 · 两种语序与连接符都归一", 11,
           s["faint"], max_w=310)
    v.text(276, 518, "命中只提示可能的复制粘贴串行，不判该偏差在工艺上对错", 11,
           s["faint"], max_w=310)

    # ---- issues channel -----------------------------------------------------
    v.rect(616, 402, 210, 122, fill=s["panel"], rx=16, stroke=s["edge"],
           sw=1.5, shadow=True)
    v.text(632, 426, "issues[]", 13, s["accent"], weight=700, mono=True,
           max_w=70)
    v.text(702, 426, "3 条", 11, s["faint"], max_w=40)
    for i, (rule, where, finding) in enumerate(ISSUES):
        y = 446 + i * 29
        v.text(632, y, rule, 11, s["accent"], weight=700, mono=True, max_w=44)
        v.text(680, y, where, 11, s["sub"], max_w=112)
        v.text(632, y + 14, finding, 11, s["text"], max_w=170)

    # ---- skipped channel ----------------------------------------------------
    v.rect(842, 402, 214, 122, fill=s["panel"], rx=16, stroke=s["edge"],
           sw=1.5, shadow=True)
    v.text(858, 426, "skipped[]", 13, s["sub"], weight=700, mono=True,
           max_w=80)
    v.text(932, 426, "4 条", 11, s["faint"], max_w=40)
    v.text(858, 446, "HZ-005 · riskLevels 未配置", 11, s["text"], max_w=182)
    v.text(858, 466, "标准未规定刻度 → 档位自定", 11, s["faint"], max_w=182)
    v.text(858, 486, "HZ-003/004/006 已执行无差异", 11, s["sub"], max_w=182)
    v.text(858, 506, "空 issues ≠ 全部通过", 11, s["mark"], max_w=182)

    # ---- buildView projection ----------------------------------------------
    v.rect(260, 540, 796, 52, fill=s["panel"], rx=16, stroke=s["edge"],
           sw=1.5, shadow=True)
    v.text(276, 566, "buildView()", 13, s["accent"], weight=700, mono=True,
           max_w=110)
    v.text(378, 566, "markdown · reportJson · summary{error,warn,info}", 11,
           s["sub"], mono=True, max_w=330)
    v.text(706, 566, "issueCount 3 / skippedCount 4", 11, s["sub"], mono=True,
           max_w=200)
    v.text(1040, 566, "结论留给审核人", 11, s["ok"], weight=700, anchor="end",
           max_w=110)
    v.text(276, 584, "报告只列差异，不判合规、不认定责任；始终带免责声明", 11,
           s["faint"], max_w=560)

    v.arrow(723, 386, 723, 400, stroke=s["accent"], sw=1.6)
    v.arrow(949, 386, 949, 400, stroke=s["accent"], sw=1.6)
    v.arrow(723, 524, 723, 538, stroke=s["accent"], sw=1.6)
    v.arrow(949, 524, 949, 538, stroke=s["accent"], sw=1.6)

    # ---- bottom notes -------------------------------------------------------
    v.text(44, 562, "只读材料 · 不联网", 11, s["faint"], max_w=190)
    v.text(44, 582, "不调用模型 · 原件不改", 11, s["faint"], max_w=190)

    v.line(44, 610, 1056, 610, stroke=s["grid"], sw=1)
    v.text(44, 628, "PerryLink DSH plugin family · Apache-2.0 · 由 "
                    "scripts/gen-readme-assets.py 生成", 11, s["faint"],
           max_w=620)
    v.text(1056, 628, "规则库即数据：rules/hazplan-check.yaml", 11,
           s["faint"], anchor="end", max_w=320)

    if v.overflows:
        raise SystemExit("FATAL: SVG label overflow:\n  " +
                         "\n  ".join(v.overflows))
    return v.svg(
        FLOW_W, FLOW_H,
        "dsh-hazplan-check 结构图：材料经 parseMaterial() 读成 WorksheetInput；"
        "三行示例表在核对矩阵里逐行对上六条行级规则（× 差异进 issues[]、"
        "√ 已执行无差异也进 skipped[]、– 未执行进 skipped[]），表头 subject 由 "
        "HZ-006 单独核对；HZ-007 要求偏差等于工艺参数与引导词的组合；两条通道"
        "汇入 buildView() 的投影")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    font(12)  # load-probe the CJK face; raises if the file is unusable
    for skin in ("light", "dark"):
        for lang in ("zh", "en"):
            hero(lang, skin)
        name = f"{NAME}-flow-v5-{skin}.svg"
        with open(os.path.join(OUT, name), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(flow_svg(skin))
        print(f"wrote {name} ({FLOW_W}×{FLOW_H})")


if __name__ == "__main__":
    main()
