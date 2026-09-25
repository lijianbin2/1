"""生成宣传片背景音乐合集的四张闲鱼图文。"""

from __future__ import annotations

import argparse
from pathlib import Path

from xianyu_common import draw_board, get_font, save_png, validate_png_files, wrap_text


W = H = 1080
BORDER = 38
BLUE = (47, 93, 255)
DARK = (30, 41, 59)
GRAY = (100, 116, 139)
PALE = (248, 250, 252)
PURPLE = (124, 58, 237)
TEAL = (14, 165, 233)
GREEN = (16, 185, 129)
ORANGE = (249, 115, 22)
ROSE = (225, 29, 72)
DEFAULT_OUT = Path("D:/闲鱼/宣传片背景音乐合集，一键提升影片质感与感染力")

CATEGORIES = [
    ("汽车宣传片", "37首", BLUE),
    ("校园宣传片", "68首", PURPLE),
    ("广告宣传片", "69首", TEAL),
    ("城市宣传片", "88首", GREEN),
    ("旅游宣传片", "111首", ORANGE),
    ("ZF宣传片", "112首", ROSE),
    ("大气企业宣传片", "487首", BLUE),
]


def centered(draw, text, y, font, fill=DARK):
    width = draw.textlength(text, font=font)
    draw.text(((W - width) // 2, y), text, fill=fill, font=font)


def footer(draw, right="1072首 · 7大分类 · 宣传片配乐"):
    height = 86
    draw.rounded_rectangle(
        [BORDER, H - BORDER - height, W - BORDER, H - BORDER],
        radius=22,
        fill=DARK,
    )
    draw.text(
        (BORDER + 40, H - BORDER - 68),
        "只发夸克",
        fill="white",
        font=get_font(24, True),
    )
    font = get_font(20)
    width = draw.textlength(right, font=font)
    draw.text(
        (W - BORDER - 40 - width, H - BORDER - 47),
        right,
        fill=(203, 213, 225),
        font=font,
    )


def render_cover(out: Path) -> None:
    im, d = draw_board()
    badge = "7大分类  1072首背景音乐"
    badge_font = get_font(25, True)
    badge_w = d.textlength(badge, font=badge_font) + 40
    badge_y = 78
    d.rounded_rectangle(
        [(W - badge_w) // 2, badge_y, (W + badge_w) // 2, badge_y + 42],
        radius=21,
        fill=BLUE,
    )
    centered(d, badge, badge_y + 8, badge_font, "white")
    centered(d, "宣传片背景音乐合集", 150, get_font(54, True))
    centered(d, "一键提升影片质感与感染力", 232, get_font(30), GRAY)
    d.line([400, 308, 680, 308], fill=BLUE, width=4)

    cards = [
        ("汽车", "37首", BLUE),
        ("校园", "68首", PURPLE),
        ("广告", "69首", TEAL),
        ("城市", "88首", GREEN),
        ("旅游", "111首", ORANGE),
        ("企业", "487首", ROSE),
    ]
    card_w, card_h, gap = 280, 136, 24
    start_x = (W - card_w * 3 - gap * 2) // 2
    for i, (name, count, color) in enumerate(cards):
        row, col = divmod(i, 3)
        x = start_x + col * (card_w + gap)
        y = 370 + row * (card_h + gap)
        d.rounded_rectangle(
            [x, y, x + card_w, y + card_h],
            radius=20,
            fill=PALE,
            outline=(226, 232, 240),
            width=1,
        )
        d.ellipse([x + 24, y + 28, x + 88, y + 92], fill=color)
        d.text((x + 42, y + 49), "音", fill="white", font=get_font(25, True))
        d.text((x + 106, y + 32), name, fill=DARK, font=get_font(25, True))
        d.text((x + 106, y + 75), count, fill=color, font=get_font(25, True))

    d.text(
        (BORDER + 40, 815),
        "汽车 · 校园 · 广告 · 城市 · 旅游 · ZF · 企业",
        fill=DARK,
        font=get_font(22, True),
    )
    d.text(
        (BORDER + 40, 858),
        "按场景选音乐，让画面情绪、节奏和氛围更到位",
        fill=GRAY,
        font=get_font(21),
    )
    footer(d)
    save_png(im, out / "01.png")


def render_catalog(out: Path) -> None:
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "分类目录", fill=DARK, font=get_font(44, True))
    d.text(
        (BORDER + 40, BORDER + 88),
        "7大宣传片场景 · 1072首背景音乐",
        fill=GRAY,
        font=get_font(24),
    )
    badge = "共1072首"
    bf = get_font(24, True)
    bw = d.textlength(badge, font=bf) + 34
    d.rounded_rectangle(
        [W - BORDER - 40 - bw, BORDER + 36, W - BORDER - 40, BORDER + 76],
        radius=19,
        fill=(239, 246, 255),
    )
    d.text(
        (W - BORDER - 40 - bw + 17, BORDER + 45),
        badge,
        fill=BLUE,
        font=bf,
    )

    card_w = (W - BORDER * 2 - 80 - 24) // 2
    card_h = 154
    for i, (name, count, color) in enumerate(CATEGORIES):
        row, col = divmod(i, 2)
        x = BORDER + 40 + col * (card_w + 24)
        y = 190 + row * (card_h + 22)
        d.rounded_rectangle(
            [x, y, x + card_w, y + card_h],
            radius=18,
            fill=PALE,
            outline=(226, 232, 240),
            width=1,
        )
        d.rounded_rectangle([x, y, x + card_w, y + 8], radius=5, fill=color)
        d.text((x + 18, y + 24), f"{i + 1:02d} {name}", fill=DARK, font=get_font(23, True))
        d.text((x + 18, y + 70), count, fill=color, font=get_font(29, True))
        label = "宣传片背景音乐"
        label_font = get_font(18)
        d.text((x + 18, y + 112), label, fill=GRAY, font=label_font)
    footer(d, "按截图分类 · 1072首")
    save_png(im, out / "02.png")


def render_outcomes(out: Path) -> None:
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "使用收获", fill=DARK, font=get_font(44, True))
    d.text(
        (BORDER + 40, BORDER + 88),
        "不同场景都有对应音乐，选择更快，剪辑更顺手",
        fill=GRAY,
        font=get_font(24),
    )
    points = [
        ("按场景选曲", "汽车、校园、广告、城市、旅游、企业等分类清晰", BLUE),
        ("提升节奏", "用音乐带动剪辑节奏，强化画面推进和转场", PURPLE),
        ("强化情绪", "匹配宣传片主题，增强氛围、情绪和感染力", TEAL),
        ("提高效率", "减少反复寻找配乐的时间，拿来即可筛选使用", GREEN),
    ]
    card_w, card_h, gap = 460, 190, 24
    for i, (title, desc, color) in enumerate(points):
        row, col = divmod(i, 2)
        x = BORDER + 40 + col * (card_w + gap)
        y = 190 + row * (card_h + gap)
        d.rounded_rectangle(
            [x, y, x + card_w, y + card_h],
            radius=20,
            fill=PALE,
            outline=(226, 232, 240),
            width=1,
        )
        d.rounded_rectangle([x + 22, y + 22, x + 76, y + 76], radius=20, fill=color)
        d.text((x + 37, y + 35), str(i + 1), fill="white", font=get_font(24, True))
        d.text((x + 96, y + 25), title, fill=DARK, font=get_font(25, True))
        body_font = get_font(18)
        for line_no, line in enumerate(
            wrap_text(desc, body_font, card_w - 120, d)[:3]
        ):
            d.text((x + 96, y + 77 + line_no * 27), line, fill=GRAY, font=body_font)
    d.rounded_rectangle(
        [BORDER + 40, 850, W - BORDER - 40, 932],
        radius=18,
        fill=(239, 246, 255),
    )
    d.text((BORDER + 60, 875), "适合：宣传片、广告片、企业片、校园片、城市片、旅游片等", fill=DARK, font=get_font(21, True))
    footer(d, "7大分类 · 1072首 · 按需选曲")
    save_png(im, out / "03.png")


def render_guide(out: Path) -> None:
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "购买前说明", fill=DARK, font=get_font(44, True))
    d.text(
        (BORDER + 40, BORDER + 88),
        "虚拟资料 · 按截图分类整理 · 拍后发夸克链接",
        fill=GRAY,
        font=get_font(24),
    )
    steps = [
        ("1", "资料内容", "汽车、校园、广告、城市、旅游、ZF、大气企业宣传片背景音乐"),
        ("2", "数量说明", "共1072首，按截图中各分类标注数量整理"),
        ("3", "使用方式", "先确定宣传片场景，再按分类挑选适合的音乐"),
        ("4", "交付方式", "拍下后发送夸克网盘链接与提取码"),
    ]
    y = 190
    for number, title, desc in steps:
        d.rounded_rectangle(
            [BORDER + 40, y, W - BORDER - 40, y + 110],
            radius=18,
            fill=PALE,
            outline=(226, 232, 240),
            width=1,
        )
        d.ellipse([BORDER + 60, y + 30, BORDER + 106, y + 76], fill=BLUE)
        number_font = get_font(23, True)
        nw = d.textlength(number, font=number_font)
        d.text((BORDER + 83 - nw / 2, y + 40), number, fill="white", font=number_font)
        d.text((BORDER + 130, y + 22), title, fill=DARK, font=get_font(24, True))
        desc_font = get_font(18)
        for line_no, line in enumerate(
            wrap_text(desc, desc_font, W - BORDER * 2 - 155, d)[:2]
        ):
            d.text(
                (BORDER + 130, y + 59 + line_no * 24),
                line,
                fill=GRAY,
                font=desc_font,
            )
        y += 128
    d.rounded_rectangle(
        [BORDER + 40, 735, W - BORDER - 40, 868],
        radius=18,
        fill=(255, 251, 235),
        outline=(253, 230, 138),
        width=1,
    )
    d.text((BORDER + 62, 760), "温馨提示", fill=(146, 64, 14), font=get_font(23, True))
    tip = "音乐素材适合宣传片、广告片、企业片等视频创作使用，建议结合画面主题、剪辑节奏和授权要求合理选择。"
    tip_font = get_font(18)
    for i, line in enumerate(wrap_text(tip, tip_font, W - BORDER * 2 - 130, d)[:3]):
        d.text((BORDER + 62, 804 + i * 25), line, fill=(120, 113, 108), font=tip_font)
    footer(d, "1072首 · 宣传片背景音乐合集")
    save_png(im, out / "04.png")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成宣传片背景音乐合集四张图文")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"输出目录（默认：{DEFAULT_OUT}）")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    render_cover(args.out)
    render_catalog(args.out)
    render_outcomes(args.out)
    render_guide(args.out)

    invalid = validate_png_files(args.out, size=(W, H))
    if invalid:
        raise RuntimeError("图片文件校验失败：" + ", ".join(str(path) for path in invalid))
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
