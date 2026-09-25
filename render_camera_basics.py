import argparse
from pathlib import Path

from xianyu_common import draw_board, get_font, save_png, validate_png_files, wrap_text


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


def centered(draw, text, y, font, fill=DARK):
    width = draw.textlength(text, font=font)
    draw.text(((W - width) // 2, y), text, fill=fill, font=font)


def footer(draw, right="相机基础 · 41节 · 摄影入门"):
    h = 86
    draw.rounded_rectangle(
        [BORDER, H - BORDER - h, W - BORDER, H - BORDER],
        radius=22,
        fill=DARK,
    )
    draw.text((BORDER + 40, H - BORDER - 68), "只发夸克", fill="white", font=get_font(24, True))
    rf = get_font(20)
    rw = draw.textlength(right, font=rf)
    draw.text((W - BORDER - 40 - rw, H - BORDER - 47), right, fill=(203, 213, 225), font=rf)


def render_cover(out: Path) -> None:
    """生成封面。"""
    im, d = draw_board()
    bf = get_font(26, True)
    badge = "41节全  摄影基础实战"
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
    start = (W - card_w * 3 - GAP * 2) // 2
    for i, (title, sub) in enumerate(features):
        x = start + i * (card_w + GAP)
        y = 560
        d.rounded_rectangle(
            [x, y, x + card_w, y + 150],
            radius=20,
            fill=PALE,
            outline=(226, 232, 240),
            width=1,
        )
        cx, cy = x + card_w // 2, y + 51
        d.ellipse(
            [cx - 31, y + 20, cx + 31, y + 82],
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
        d.text((x + (card_w - tw) / 2, y + 92), title, fill=DARK, font=title_font)
        sw = d.textlength(sub, font=sub_font)
        d.text((x + (card_w - sw) / 2, y + 124), sub, fill=GRAY, font=sub_font)

    d.text(
        (BORDER + 40, 840),
        "焦距 · 透视 · 测光 · 白平衡 · 对焦 · 景深 · 构图",
        fill=INK,
        font=get_font(22),
    )
    d.text(
        (BORDER + 40, 878),
        "适合摄影新手、相机入门用户与想提升拍摄基础的人群",
        fill=GRAY,
        font=get_font(20),
    )
    footer(d)
    save_png(im, out / "01.png")


def render_catalog(out: Path) -> None:
    """生成 Catalog。"""
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "课程目录", fill=DARK, font=get_font(44, True))
    d.text((BORDER + 40, BORDER + 88), "41节视频 · 12个章节 · 从基础概念到实拍技巧", fill=GRAY, font=get_font(24))
    badge2 = "41节"
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
    for i, (name, rng, desc, color) in enumerate(modules):
        col, row = i % 3, i // 3
        x = BORDER + 40 + col * (cw + GAP)
        y = 188 + row * 146
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=18, fill=PALE, outline=(226, 232, 240), width=1)
        d.rounded_rectangle([x, y, x + cw, y + 7], radius=6, fill=color)
        d.text((x + 16, y + 20), name, fill=DARK, font=get_font(22, True))
        d.text((x + 16, y + 60), rng, fill=color, font=get_font(20, True))
        for line in wrap_text(desc, get_font(18), cw - 32, d)[:2]:
            d.text((x + 16, y + 91), line, fill=INK, font=get_font(18))
    footer(d, "12个章节 · 41节视频")
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
    for i, (title, desc, color) in enumerate(points):
        col, row = i % 2, i // 2
        x = BORDER + 40 + col * (cw2 + GAP)
        y = 190 + row * 150
        d.rounded_rectangle([x, y, x + cw2, y + 125], radius=18, fill=PALE, outline=(226, 232, 240), width=1)
        d.rounded_rectangle([x + 14, y + 14, x + 50, y + 50], radius=18, fill=color)
        num = str(i + 1)
        nw = d.textlength(num, font=get_font(20, True))
        d.text((x + 32 - nw / 2, y + 25), num, fill="white", font=get_font(20, True))
        d.text((x + 66, y + 21), title, fill=DARK, font=get_font(24, True))
        for line in wrap_text(desc, get_font(18), cw2 - 36, d)[:2]:
            d.text((x + 18, y + 70), line, fill=GRAY, font=get_font(18))

    d.rounded_rectangle([BORDER + 40, 830, W - BORDER - 40, 930], radius=18, fill=(239, 246, 255))
    d.text((BORDER + 60, 850), "适合谁", fill=DARK, font=get_font(22, True))
    scenes = ["摄影新手", "相机入门", "旅行拍摄", "人像与风光"]
    sx = BORDER + 60
    for scene in scenes:
        sf = get_font(19)
        sw2 = d.textlength(scene, font=sf) + 28
        d.rounded_rectangle([sx, 890, sx + sw2, 920], radius=15, fill="white", outline=BLUE, width=1)
        d.text((sx + 14, 895), scene, fill=BLUE, font=sf)
        sx += sw2 + 14
    footer(d, "摄影入门 · 基础实拍 · 构图提升")
    save_png(im, out / "03.png")


def render_guide(out: Path) -> None:
    """生成 Guide。"""
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "购买前说明", fill=DARK, font=get_font(44, True))
    d.text((BORDER + 40, BORDER + 88), "虚拟资料 · 只发夸克网盘 · 按需学习", fill=GRAY, font=get_font(24))
    steps = [
        ("1", "资料内容", "41节MP4视频，按章节顺序学习"),
        ("2", "适合人群", "摄影新手、相机入门及基础提升用户"),
        ("3", "交付方式", "拍下后发送夸克网盘链接与提取码"),
        ("4", "使用提示", "建议边看边练，结合相机参数实践"),
    ]
    y = 190
    for num, title, desc in steps:
        d.rounded_rectangle([BORDER + 40, y, W - BORDER - 40, y + 104], radius=18, fill=PALE, outline=(226, 232, 240), width=1)
        d.ellipse([BORDER + 60, y + 28, BORDER + 104, y + 72], fill=BLUE)
        nw = d.textlength(num, font=get_font(24, True))
        d.text((BORDER + 82 - nw / 2, y + 38), num, fill="white", font=get_font(24, True))
        d.text((BORDER + 126, y + 22), title, fill=DARK, font=get_font(24, True))
        d.text((BORDER + 126, y + 58), desc, fill=GRAY, font=get_font(20))
        y += 122

    d.rounded_rectangle([BORDER + 40, 710, W - BORDER - 40, 825], radius=18, fill=(255, 251, 235), outline=(253, 230, 138), width=1)
    d.text((BORDER + 62, 730), "提醒", fill=(146, 64, 14), font=get_font(22, True))
    for i, line in enumerate(wrap_text("本资料为摄影基础知识课程，适合自学与实操练习；请根据自身设备和拍摄需求选择使用。", get_font(18), W - 2 * BORDER - 130, d)[:3]):
        d.text((BORDER + 62, 770 + i * 23), line, fill=(120, 113, 108), font=get_font(18))
    footer(d, "相机基础 · 41节视频 · 即学即练")
    save_png(im, out / "04.png")

def main() -> int:
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

    invalid = validate_png_files(args.out, size=(W, H))
    if invalid:
        raise RuntimeError("图片文件校验失败：" + ", ".join(str(path) for path in invalid))
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
