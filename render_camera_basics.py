import argparse
from pathlib import Path

from xianyu_common import (
    assert_no_overlap,
    draw_board,
    enable_utf8_stdout,
    get_font,
    require_valid_pngs,
    save_png,
    stack_blocks,
    stack_layout,
    wrap_text_fit,
)


W = H = 1080
BORDER = 38
BLUE = (47, 93, 255)
DARK = (30, 41, 59)
GRAY = (100, 116, 139)
PALE = (248, 250, 252)
INK = (51, 65, 85)
GAP = 24
ORANGE = (249, 115, 22)
TEAL = (14, 165, 233)
GREEN = (16, 185, 129)
PURPLE = (124, 58, 237)
ROSE = (225, 29, 72)

DEFAULT_OUT = Path("D:/闲鱼/相机基础入门课，光圈快门曝光度一次搞懂")
FOOTER_H = 86
FOOTER_TOP = H - BORDER - FOOTER_H

# 课程规模来自 verify_source.py 对源目录的实测结果，改数量只改这里。
LESSONS = 41
CHAPTERS = 12
LESSON_LABEL = f"{LESSONS}节"
CHAPTER_LABEL = f"{CHAPTERS}个章节"


def centered(draw, text, y, font, fill=DARK):
    width = draw.textlength(text, font=font)
    draw.text(((W - width) // 2, y), text, fill=fill, font=font)


def footer(draw, right=None):
    right = right or f"相机基础 · {LESSON_LABEL} · 摄影入门"
    draw.rounded_rectangle(
        [BORDER, FOOTER_TOP, W - BORDER, H - BORDER],
        radius=22,
        fill=DARK,
    )
    # 两行按 FOOTER_TOP 相对定位，别再用 H-BORDER-68/-47 硬写：
    # 24px 与 20px 两行墨迹几乎占满行高，差值一旦被改小就会连成一片。
    draw.text((BORDER + 40, FOOTER_TOP + 12), "只发夸克", fill="white", font=get_font(24, True))
    rf = get_font(20)
    rw = draw.textlength(right, font=rf)
    draw.text((W - BORDER - 40 - rw, FOOTER_TOP + 48), right, fill=(203, 213, 225), font=rf)


def render_cover(out: Path) -> None:
    """生成封面。"""
    im, d = draw_board()
    bf = get_font(26, True)
    badge = f"{LESSON_LABEL}全  摄影基础实战"
    bw = d.textlength(badge, font=bf) + 40
    by = BORDER + 36
    d.rounded_rectangle([(W - bw) // 2, by, (W + bw) // 2, by + 42], radius=21, fill=BLUE)
    centered(d, badge, by + 8, bf, "white")

    centered(d, "相机基础入门课", by + 94, get_font(58, True))
    centered(d, "光圈 · 快门 · 曝光度一次搞懂", by + 172, get_font(32), GRAY)
    d.line([440, by + 248, 640, by + 248], fill=BLUE, width=4)

    features = [
        ("入门体系", "从概念到实拍"),
        ("曝光基础", "光圈快门一次掌握"),
        ("构图实战", "对焦景深同步学习"),
    ]
    card_w = 270
    card_h = 150
    meta_h = 76
    # 特色卡吸收分隔线与页脚之间的剩余空间，说明文字紧随其后
    (cards_y, meta_y), (card_h, _) = stack_layout(
        [card_h, meta_h],
        by + 248 + 60,
        FOOTER_TOP - 40,
        grow=[0],
        max_grow=110,
        max_gap=90,
    )
    start = (W - card_w * 3 - GAP * 2) // 2
    for i, (title, sub) in enumerate(features):
        x = start + i * (card_w + GAP)
        y = cards_y
        # 图标、标题、副标题整体在卡片内垂直居中，卡片变高也不会顶到边
        content_h = 62 + 10 + 30 + 2 + 24
        top = y + (card_h - content_h) // 2
        d.rounded_rectangle(
            [x, y, x + card_w, y + card_h],
            radius=20,
            fill=PALE,
            outline=(226, 232, 240),
            width=1,
        )
        cx, cy = x + card_w // 2, top + 31
        d.ellipse(
            [cx - 31, top, cx + 31, top + 62],
            fill=(239, 246, 255),
            outline=BLUE,
            width=2,
        )
        if i == 0:
            d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=BLUE)
        elif i == 1:
            d.pieslice([cx - 19, cy - 19, cx + 19, cy + 19], -90, 90, fill=BLUE)
        else:
            d.rounded_rectangle(
                [cx - 18, cy - 18, cx + 18, cy + 18],
                radius=4,
                outline=BLUE,
                width=3,
            )
            d.line([cx, cy - 18, cx, cy + 18], fill=BLUE, width=2)
        title_font = get_font(24, True)
        sub_font = get_font(18)
        tw = d.textlength(title, font=title_font)
        d.text((x + (card_w - tw) / 2, top + 72), title, fill=DARK, font=title_font)
        sw = d.textlength(sub, font=sub_font)
        d.text((x + (card_w - sw) / 2, top + 104), sub, fill=GRAY, font=sub_font)

    d.text(
        (BORDER + 40, meta_y),
        "焦距 · 透视 · 测光 · 白平衡 · 对焦 · 景深 · 构图",
        fill=INK,
        font=get_font(22),
    )
    d.text(
        (BORDER + 40, meta_y + 38),
        "适合摄影新手、相机入门用户与想提升拍摄基础的人群",
        fill=GRAY,
        font=get_font(20),
    )
    assert_no_overlap(
        [(cards_y, cards_y + card_h), (meta_y, meta_y + meta_h)],
        "封面",
    )
    footer(d)
    save_png(im, out / "01.png")


def render_catalog(out: Path) -> None:
    """生成 Catalog。"""
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "课程目录", fill=DARK, font=get_font(44, True))
    d.text((BORDER + 40, BORDER + 88), f"{LESSON_LABEL}视频 · {CHAPTER_LABEL} · 从基础概念到实拍技巧", fill=GRAY, font=get_font(24))
    badge2 = LESSON_LABEL
    bf2 = get_font(26, True)
    bw2 = d.textlength(badge2, font=bf2) + 34
    d.rounded_rectangle([W - BORDER - 40 - bw2, BORDER + 36, W - BORDER - 40, BORDER + 78], radius=20, fill=(239, 246, 255))
    d.text((W - BORDER - 40 - bw2 + 17, BORDER + 45), badge2, fill=BLUE, font=bf2)

    modules = [
        ("01 摄影概论", "1.1", "拍出好照片", BLUE),
        ("02 焦距基础", "2.1-2.4", "焦距、等效焦距", PURPLE),
        ("03 取景透视", "3.1-3.2", "透视与取景时机", TEAL),
        ("04 曝光表达", "4.1-4.4", "测光与曝光控制", GREEN),
        ("05 曝光模式", "5.1-5.4", "互易率与M档", ORANGE),
        ("06 曝光判断", "6.1-6.4", "直方图与测光方法", ROSE),
        ("07 光线色温", "7.1-7.4", "光线性质与白平衡", BLUE),
        ("08 对焦基础", "8.1-8.4", "对焦模式与选择", PURPLE),
        ("09 景深控制", "9.1-9.4", "背景虚化与超焦距", TEAL),
        ("10 快门应用", "10.1-10.4", "高速慢门与闪光灯", GREEN),
        ("11 构图方法", "11.1-11.3", "居中、三分与场景构图", ORANGE),
        ("12 实例练习", "12.1-12.3", "技巧实例与毕业寄语", ROSE),
    ]
    cw = (W - 2 * BORDER - 80 - GAP * 2) // 3
    ch = 132
    rows = (len(modules) + 2) // 3
    grid_top = stack_blocks(
        [ch * rows + (rows - 1) * 14],
        188,
        FOOTER_TOP - 40,
    )[0]
    for i, (name, rng, desc, color) in enumerate(modules):
        col, row = i % 3, i // 3
        x = BORDER + 40 + col * (cw + GAP)
        y = grid_top + row * (ch + 14)
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=18, fill=PALE, outline=(226, 232, 240), width=1)
        d.rounded_rectangle([x, y, x + cw, y + 7], radius=6, fill=color)
        d.text((x + 16, y + 20), name, fill=DARK, font=get_font(22, True))
        d.text((x + 16, y + 60), rng, fill=color, font=get_font(20, True))
        body_font = get_font(18)
        for line_no, line in enumerate(
            wrap_text_fit(desc, body_font, cw - 32, 2, d, label=f"02 页 {name}")
        ):
            d.text((x + 16, y + 91 + line_no * 22), line, fill=INK, font=body_font)
    footer(d, f"{CHAPTER_LABEL} · {LESSON_LABEL}视频")
    save_png(im, out / "02.png")


def render_outcomes(out: Path) -> None:
    """生成 Outcomes。"""
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "学完你将掌握", fill=DARK, font=get_font(44, True))
    d.text((BORDER + 40, BORDER + 88), "把光圈、快门与曝光度真正用起来", fill=GRAY, font=get_font(24))
    points = [
        ("看懂焦距", "理解焦距变化与题材的关系", BLUE),
        ("理解透视", "掌握取景范围、角度与时机", PURPLE),
        ("控制曝光", "学会测光、白加黑减与曝光模式", GREEN),
        ("用好光线", "理解色温、白平衡与光线分类", ORANGE),
        ("精准对焦", "掌握对焦模式、对焦点与先对焦还是构图", TEAL),
        ("拍出层次", "运用景深、超焦距、快门与构图", ROSE),
    ]
    cw2 = (W - 2 * BORDER - 80 - GAP) // 2
    card_h = 125
    suit_h = 100
    pt_rows = (len(points) + 1) // 2
    (grid_y, suit_y), (grid_h, suit_h) = stack_layout(
        [125 * pt_rows + (pt_rows - 1) * GAP, 100],
        190,
        FOOTER_TOP - 40,
        grow=[0, 1],
        max_grow=40,
    )
    card_h = (grid_h - (pt_rows - 1) * GAP) / pt_rows
    for i, (title, desc, color) in enumerate(points):
        col, row = i % 2, i // 2
        x = BORDER + 40 + col * (cw2 + GAP)
        y = grid_y + row * (card_h + GAP)
        # 编号、标题和描述在卡片内垂直居中，卡片被拉高时不会挤在顶部
        body = "\n".join(
            wrap_text_fit(desc, get_font(18), cw2 - 36, 2, d, label=f"03 页 {title}")
        )
        content_h = 36 + 8 + 8 + 22 * body.count("\n") + 22
        top = y + (card_h - content_h) / 2
        d.rounded_rectangle([x, y, x + cw2, y + card_h], radius=18, fill=PALE, outline=(226, 232, 240), width=1)
        d.rounded_rectangle([x + 14, top + 2, x + 50, top + 38], radius=18, fill=color)
        num = str(i + 1)
        nw = d.textlength(num, font=get_font(20, True))
        d.text((x + 32 - nw / 2, top + 13), num, fill="white", font=get_font(20, True))
        d.text((x + 66, top + 9), title, fill=DARK, font=get_font(24, True))
        for line_no, line in enumerate(body.splitlines()):
            d.text((x + 18, top + 54 + line_no * 22), line, fill=GRAY, font=get_font(18))

    d.rounded_rectangle([BORDER + 40, suit_y, W - BORDER - 40, suit_y + suit_h], radius=18, fill=(239, 246, 255))
    suit_top = suit_y + (suit_h - 70) / 2
    d.text((BORDER + 60, suit_top), "适合谁", fill=DARK, font=get_font(22, True))
    scenes = ["摄影新手", "相机入门", "旅行拍摄", "人像与风光"]
    sx = BORDER + 60
    for scene in scenes:
        sf = get_font(19)
        sw2 = d.textlength(scene, font=sf) + 28
        d.rounded_rectangle([sx, suit_top + 40, sx + sw2, suit_top + 70], radius=15, fill="white", outline=BLUE, width=1)
        d.text((sx + 14, suit_top + 45), scene, fill=BLUE, font=sf)
        sx += sw2 + 14
    assert_no_overlap(
        [(grid_y, grid_y + grid_h), (suit_y, suit_y + suit_h)],
        "收获",
    )
    footer(d, "摄影入门 · 基础实拍 · 构图提升")
    save_png(im, out / "03.png")


def render_guide(out: Path) -> None:
    """生成 Guide。"""
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "购买前说明", fill=DARK, font=get_font(44, True))
    d.text((BORDER + 40, BORDER + 88), "虚拟资料 · 只发夸克网盘 · 按需学习", fill=GRAY, font=get_font(24))
    steps = [
        ("1", "资料内容", f"{LESSON_LABEL}MP4视频，按章节顺序学习"),
        ("2", "适合人群", "摄影新手、相机入门及基础提升用户"),
        ("3", "交付方式", "拍下后发送夸克网盘链接与提取码"),
        ("4", "使用提示", "建议边看边练，结合相机参数实践"),
    ]
    step_h = 104
    step_gap = 18
    warn_h = 115
    steps_y, warn_y = stack_blocks(
        [step_h * len(steps) + step_gap * (len(steps) - 1), warn_h],
        190,
        FOOTER_TOP - 40,
    )
    y = steps_y
    for num, title, desc in steps:
        d.rounded_rectangle([BORDER + 40, y, W - BORDER - 40, y + step_h], radius=18, fill=PALE, outline=(226, 232, 240), width=1)
        ncy = y + (step_h - 44) // 2
        d.ellipse([BORDER + 60, ncy, BORDER + 104, ncy + 44], fill=BLUE)
        nw = d.textlength(num, font=get_font(24, True))
        d.text((BORDER + 82 - nw / 2, ncy + 7), num, fill="white", font=get_font(24, True))
        ty = y + (step_h - 62) // 2
        d.text((BORDER + 126, ty), title, fill=DARK, font=get_font(24, True))
        d.text((BORDER + 126, ty + 34), desc, fill=GRAY, font=get_font(20))
        y += step_h + step_gap

    d.rounded_rectangle([BORDER + 40, warn_y, W - BORDER - 40, warn_y + warn_h], radius=18, fill=(255, 251, 235), outline=(253, 230, 138), width=1)
    d.text((BORDER + 62, warn_y + 18), "提醒", fill=(146, 64, 14), font=get_font(22, True))
    warn_font = get_font(18)
    for i, line in enumerate(
        wrap_text_fit(
            "本资料为摄影基础知识课程，适合自学与实操练习；请根据自身设备和拍摄需求选择使用。",
            warn_font,
            W - 2 * BORDER - 130,
            3,
            d,
            label="04 页提醒",
        )
    ):
        d.text((BORDER + 62, warn_y + 58 + i * 23), line, fill=(120, 113, 108), font=warn_font)
    footer(d, f"相机基础 · {LESSON_LABEL}视频 · 即学即练")
    save_png(im, out / "04.png")

def main() -> int:
    enable_utf8_stdout()
    parser = argparse.ArgumentParser(description="生成相机基础课程四张图文")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"输出目录（默认：{DEFAULT_OUT}）",
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    render_cover(args.out)
    render_catalog(args.out)
    render_outcomes(args.out)
    render_guide(args.out)

    require_valid_pngs(args.out, size=(W, H))
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
