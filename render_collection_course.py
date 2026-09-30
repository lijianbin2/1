import argparse
import json
from pathlib import Path

from xianyu_common import (
    assert_no_overlap,
    chip_positions,
    draw_board,
    enable_utf8_stdout,
    fit_font,
    get_font,
    require_valid_pngs,
    save_png,
    stack_layout,
    wrap_text_fit,
)


W = H = 1080
BORDER = 38
DARK = (30, 41, 59)
GRAY = (100, 116, 139)
PALE = (248, 250, 252)
INK = (51, 65, 85)
LINE = (226, 232, 240)
BLUE = (47, 93, 255)
ORANGE = (249, 115, 22)
TEAL = (14, 165, 233)
GREEN = (16, 185, 129)
PURPLE = (124, 58, 237)
ROSE = (225, 29, 72)

ACCENTS = {
    "blue": BLUE,
    "orange": ORANGE,
    "teal": TEAL,
    "green": GREEN,
    "purple": PURPLE,
    "rose": ROSE,
}

FOOTER_H = 86
FOOTER_TOP = H - BORDER - FOOTER_H

# 死区扫描器只带 --out 调用公开入口，所以 --spec 必须有默认值：
# 渲染哪份数据不影响版式校验，扫描器要的是四页产物本身。
DEFAULT_SPEC = Path(__file__).resolve().parent / "specs" / "keep_fitness.json"

CATALOG_TOP = 188
CATALOG_BOTTOM = FOOTER_TOP - 40
GRID_GAP = 14
# 卡片高度上限。区域有 728px 高，模块少的时候把卡片拉满会在卡内底部留出
# 一大片空白——死区扫描只看整幅横带，查不出卡内空洞，所以这里按内容限高，
# 再把整块网格在区域里居中。
CARD_MAX_H = 233


def accent(spec: dict) -> tuple[int, int, int]:
    """把 spec 里的强调色名换成 RGB，未知名字直接报错。"""
    name = spec.get("accent", "blue")
    if name not in ACCENTS:
        raise ValueError(f"未知强调色：{name}，可选 {sorted(ACCENTS)}")
    return ACCENTS[name]


def centered(draw, text: str, y: float, font, fill=DARK) -> None:
    width = draw.textlength(text, font=font)
    draw.text(((W - width) // 2, y), text, fill=fill, font=font)


def footer(draw, right: str) -> None:
    draw.rounded_rectangle(
        [BORDER, FOOTER_TOP, W - BORDER, H - BORDER], radius=22, fill=DARK
    )
    # 两行都按 FOOTER_TOP 相对定位，不要写 H-BORDER-68/-47 这类字面量。
    draw.text(
        (BORDER + 40, FOOTER_TOP + 12), "只发夸克", fill="white", font=get_font(24, True)
    )
    rf = get_font(20)
    rw = draw.textlength(right, font=rf)
    draw.text(
        (W - BORDER - 40 - rw, FOOTER_TOP + 48), right, fill=(203, 213, 225), font=rf
    )


def page_title(draw, title: str, subtitle: str) -> None:
    """02/03/04 页共用的标题区。"""
    draw.text((BORDER + 40, BORDER + 30), title, fill=DARK, font=get_font(44, True))
    draw.text(
        (BORDER + 40, BORDER + 88), subtitle, fill=GRAY, font=get_font(24)
    )


def grid_columns(count: int) -> int:
    """按模块数选列数，让卡片高度尽量贴近 ``CARD_MAX_H``。"""
    best = 5
    best_delta = None
    for cols in (2, 3, 4, 5):
        rows = -(-count // cols)
        height = (CATALOG_BOTTOM - CATALOG_TOP - (rows - 1) * GRID_GAP) / rows
        if height < 104:
            continue
        delta = abs(min(height, CARD_MAX_H) - CARD_MAX_H)
        if best_delta is None or delta < best_delta:
            best, best_delta = cols, delta
    return best


def render_cover(spec: dict, out: Path) -> None:
    im, d = draw_board()
    main = accent(spec)
    badge = spec["badge"]
    bf = get_font(26, True)
    bw = d.textlength(badge, font=bf) + 40
    by = BORDER + 36
    d.rounded_rectangle([(W - bw) // 2, by, (W + bw) // 2, by + 42], radius=21, fill=main)
    centered(d, badge, by + 8, bf, "white")

    title_font, _ = fit_font(d, spec["title"], W - 2 * BORDER - 120, 56, bold=True, min_size=38)
    centered(d, spec["title"], by + 94, title_font)
    sub_font, _ = fit_font(
        d, spec["subtitle"], W - 2 * BORDER - 120, 32, min_size=24
    )
    centered(d, spec["subtitle"], by + 172, sub_font, GRAY)
    d.line([440, by + 248, 640, by + 248], fill=main, width=4)

    features = spec["cover_features"]
    if len(features) != 3:
        raise ValueError("cover_features 必须正好 3 项")
    card_w = 270
    meta_h = 76
    # 特色卡吸收分隔线到页脚之间的剩余空间，说明文字紧随其后。
    (cards_y, meta_y), (card_h, _) = stack_layout(
        [150, meta_h],
        by + 248 + 60,
        FOOTER_TOP - 40,
        grow=[0],
        max_grow=110,
        max_gap=90,
    )
    start = (W - card_w * 3 - 24 * 2) // 2
    for i, (head, sub) in enumerate(features):
        x = start + i * (card_w + 24)
        content_h = 62 + 10 + 30 + 2 + 24
        top = cards_y + (card_h - content_h) // 2
        d.rounded_rectangle(
            [x, cards_y, x + card_w, cards_y + card_h],
            radius=20,
            fill=PALE,
            outline=LINE,
            width=1,
        )
        cx = x + card_w // 2
        d.ellipse(
            [cx - 31, top, cx + 31, top + 62],
            fill=(239, 246, 255),
            outline=main,
            width=2,
        )
        # 三种几何图标：实心圆、半圆、方框。不引入字体里可能缺字形的符号。
        if i == 0:
            d.ellipse([cx - 6, top + 25, cx + 6, top + 37], fill=main)
        elif i == 1:
            d.pieslice([cx - 19, top + 12, cx + 19, top + 50], -90, 90, fill=main)
        else:
            d.rounded_rectangle(
                [cx - 18, top + 13, cx + 18, top + 49], radius=4, outline=main, width=3
            )
            d.line([cx, top + 13, cx, top + 49], fill=main, width=2)
        tf = get_font(24, True)
        sf = get_font(18)
        tw = d.textlength(head, font=tf)
        d.text((x + (card_w - tw) / 2, top + 72), head, fill=DARK, font=tf)
        for n, line in enumerate(
            wrap_text_fit(sub, sf, card_w - 28, 2, d, label=f"封面 {head}")
        ):
            sw = d.textlength(line, font=sf)
            d.text((x + (card_w - sw) / 2, top + 104 + n * 22), line, fill=GRAY, font=sf)

    d.text(
        (BORDER + 40, meta_y), spec["keywords"], fill=INK, font=get_font(22)
    )
    d.text(
        (BORDER + 40, meta_y + 38), spec["audience"], fill=GRAY, font=get_font(20)
    )
    assert_no_overlap(
        [(cards_y, cards_y + card_h), (meta_y, meta_y + meta_h)], "封面"
    )
    footer(d, spec["footer"])
    save_png(im, out / "01.png")


def render_catalog(spec: dict, out: Path) -> None:
    im, d = draw_board()
    main = accent(spec)
    page_title(d, "合集目录", spec["catalog_subtitle"])

    badge = spec["count_label"]
    bf = get_font(26, True)
    bw = d.textlength(badge, font=bf) + 34
    d.rounded_rectangle(
        [W - BORDER - 40 - bw, BORDER + 36, W - BORDER - 40, BORDER + 78],
        radius=20,
        fill=(239, 246, 255),
    )
    d.text((W - BORDER - 40 - bw + 17, BORDER + 45), badge, fill=BLUE, font=bf)

    modules = spec["modules"]
    if not modules:
        raise ValueError("modules 不能为空")
    cols = grid_columns(len(modules))
    rows = -(-len(modules) // cols)
    cw = (W - 2 * BORDER - 80 - 24 * (cols - 1)) // cols
    available = CATALOG_BOTTOM - CATALOG_TOP
    ch = min((available - (rows - 1) * GRID_GAP) / rows, CARD_MAX_H)
    if ch < 90:
        raise ValueError(f"{len(modules)} 个模块排不下：行高只剩 {ch:.0f}px")
    # 限高之后整块在可用区域里居中，避免顶部堆内容、底部空一大片。
    grid_top = CATALOG_TOP + (available - (rows * ch + (rows - 1) * GRID_GAP)) / 2
    palette = [BLUE, PURPLE, TEAL, GREEN, ORANGE, ROSE]
    for i, (name, rng, desc) in enumerate(modules):
        col, row = i % cols, i // cols
        x = BORDER + 40 + col * (cw + 24)
        y = grid_top + row * (ch + GRID_GAP)
        color = palette[i % len(palette)]
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=18, fill=PALE, outline=LINE, width=1)
        d.rounded_rectangle([x, y, x + cw, y + 7], radius=6, fill=color)
        nf, _ = fit_font(d, name, cw - 32, 22, bold=True, min_size=18)
        rf = get_font(19, True)
        body = get_font(17)
        lines = wrap_text_fit(desc, body, cw - 32, 3, d, label=f"02 页 {name}")
        # 名称、数量、说明作为一整块在卡内垂直居中，卡片高度变化不顶到边。
        block_h = 26 + 6 + 24 + 8 + 21 * len(lines)
        top = y + (ch - block_h) / 2
        d.text((x + 16, top), name, fill=DARK, font=nf)
        d.text((x + 16, top + 32), rng, fill=color, font=rf)
        for n, line in enumerate(lines):
            d.text((x + 16, top + 64 + n * 21), line, fill=INK, font=body)
    footer(d, spec["footer"])
    save_png(im, out / "02.png")


def render_outcomes(spec: dict, out: Path) -> None:
    im, d = draw_board()
    main = accent(spec)
    page_title(d, "学完你将掌握", spec["outcomes_subtitle"])

    points = spec["outcomes"]
    cols = 2 if len(points) >= 4 else 1
    rows = -(-len(points) // cols)
    cw = (W - 2 * BORDER - 80 - 24 * (cols - 1)) // cols
    suit_h = 100
    (grid_y, suit_y), (grid_h, _) = stack_layout(
        [125 * rows + (rows - 1) * 24, suit_h],
        190,
        FOOTER_TOP - 40,
        grow=[0],
        max_grow=40,
    )
    ch = (grid_h - (rows - 1) * 24) / rows
    palette = [BLUE, PURPLE, GREEN, ORANGE, TEAL, ROSE]
    for i, (head, desc) in enumerate(points):
        col, row = i % cols, i // cols
        x = BORDER + 40 + col * (cw + 24)
        y = grid_y + row * (ch + 24)
        color = palette[i % len(palette)]
        body = wrap_text_fit(desc, get_font(18), cw - 36, 2, d, label=f"03 页 {head}")
        content_h = 36 + 8 + 8 + 22 * (len(body) - 1) + 22
        top = y + (ch - content_h) / 2
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=18, fill=PALE, outline=LINE, width=1)
        d.rounded_rectangle([x + 14, top + 2, x + 50, top + 38], radius=18, fill=color)
        num = str(i + 1)
        nw = d.textlength(num, font=get_font(20, True))
        d.text((x + 32 - nw / 2, top + 13), num, fill="white", font=get_font(20, True))
        hf, _ = fit_font(d, head, cw - 90, 24, bold=True, min_size=19)
        d.text((x + 66, top + 9), head, fill=DARK, font=hf)
        for n, line in enumerate(body):
            d.text((x + 18, top + 54 + n * 22), line, fill=GRAY, font=get_font(18))

    d.rounded_rectangle(
        [BORDER + 40, suit_y, W - BORDER - 40, suit_y + suit_h],
        radius=18,
        fill=(239, 246, 255),
    )
    suit_top = suit_y + (suit_h - 70) / 2
    d.text((BORDER + 60, suit_top), "适合谁", fill=DARK, font=get_font(22, True))
    sf = get_font(19)
    for scene, sx, sw in chip_positions(
        d,
        spec["scenes"],
        font=sf,
        left=BORDER + 60,
        right=W - BORDER - 60,
        label="03 页适合谁",
    ):
        d.rounded_rectangle([sx, suit_top + 40, sx + sw, suit_top + 70], radius=15, fill="white", outline=main, width=1)
        d.text((sx + 14, suit_top + 45), scene, fill=main, font=sf)
    assert_no_overlap([(grid_y, grid_y + grid_h), (suit_y, suit_y + suit_h)], "收获")
    footer(d, spec["footer"])
    save_png(im, out / "03.png")


def render_guide(spec: dict, out: Path) -> None:
    im, d = draw_board()
    main = accent(spec)
    page_title(d, "购买前说明", "虚拟资料 · 只发夸克网盘 · 按需学习")

    steps = spec["steps"]
    step_h = 104
    step_gap = 18
    warn_h = 115
    # 步骤块与提醒块的位置由步数推导，不写死坐标。
    steps_y, warn_y = stack_layout(
        [step_h * len(steps) + step_gap * (len(steps) - 1), warn_h],
        190,
        FOOTER_TOP - 40,
    )[0]
    y = steps_y
    for num, head, desc in steps:
        d.rounded_rectangle(
            [BORDER + 40, y, W - BORDER - 40, y + step_h],
            radius=18,
            fill=PALE,
            outline=LINE,
            width=1,
        )
        ncy = y + (step_h - 44) // 2
        d.ellipse([BORDER + 60, ncy, BORDER + 104, ncy + 44], fill=main)
        nw = d.textlength(num, font=get_font(24, True))
        d.text((BORDER + 82 - nw / 2, ncy + 7), num, fill="white", font=get_font(24, True))
        ty = y + (step_h - 62) // 2
        d.text((BORDER + 126, ty), head, fill=DARK, font=get_font(24, True))
        d.text((BORDER + 126, ty + 34), desc, fill=GRAY, font=get_font(20))
        y += step_h + step_gap

    d.rounded_rectangle(
        [BORDER + 40, warn_y, W - BORDER - 40, warn_y + warn_h],
        radius=18,
        fill=(255, 251, 235),
        outline=(253, 230, 138),
        width=1,
    )
    d.text((BORDER + 62, warn_y + 18), "提醒", fill=(146, 64, 14), font=get_font(22, True))
    wf = get_font(18)
    for n, line in enumerate(
        wrap_text_fit(
            spec["warn"], wf, W - 2 * BORDER - 130, 3, d, label="04 页提醒"
        )
    ):
        d.text((BORDER + 62, warn_y + 58 + n * 23), line, fill=(120, 113, 108), font=wf)
    footer(d, spec["footer"])
    save_png(im, out / "04.png")


def load_spec(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    for key in (
        "badge",
        "title",
        "subtitle",
        "cover_features",
        "keywords",
        "audience",
        "count_label",
        "catalog_subtitle",
        "modules",
        "outcomes_subtitle",
        "outcomes",
        "scenes",
        "steps",
        "warn",
        "footer",
    ):
        if key not in spec:
            raise ValueError(f"spec 缺少字段：{key}")
    return spec


def main() -> int:
    enable_utf8_stdout()
    parser = argparse.ArgumentParser(description="按 JSON spec 生成合集课四张图文")
    parser.add_argument(
        "--spec", type=Path, default=DEFAULT_SPEC, help=f"渲染数据 JSON（默认：{DEFAULT_SPEC}）"
    )
    parser.add_argument("--out", type=Path, help="输出目录，缺省用 spec 里的 out")
    args = parser.parse_args()

    spec = load_spec(args.spec)
    out = args.out or Path(spec["out"])
    out.mkdir(parents=True, exist_ok=True)

    render_cover(spec, out)
    render_catalog(spec, out)
    render_outcomes(spec, out)
    render_guide(spec, out)

    require_valid_pngs(out, size=(W, H))
    print(f"generated {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
