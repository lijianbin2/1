"""生成高清地图矢量素材合集的四张闲鱼图文。"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

from xianyu_common import draw_board, get_font, save_png, validate_png_files, wrap_text


W = H = 1080
BORDER = 38
BLUE = (47, 93, 255)
DARK = (30, 41, 59)
GRAY = (100, 116, 139)
PALE = (248, 250, 252)
TEAL = (14, 165, 233)
GREEN = (16, 185, 129)
ORANGE = (249, 115, 22)
ROSE = (225, 29, 72)
DEFAULT_OUT = Path("D:/闲鱼/高清一亿像素地图矢量图合集，超精细地理素材")
DEFAULT_ROOT = Path(r"M:/WebDAV/夸克/软件/高清一亿像素地图矢量图合集，超精细地理素材")

Image.MAX_IMAGE_PIXELS = None


def image_fit(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)
    return ImageEnhance.Sharpness(image).enhance(1.15)


def image_panel(base: Image.Image, image: Image.Image, box: tuple[int, int, int, int], radius: int = 20) -> None:
    left, top, right, bottom = box
    if (
        not all(isinstance(value, int) and not isinstance(value, bool) for value in box)
        or left < 0
        or top < 0
        or right <= left
        or bottom <= top
        or right > base.width
        or bottom > base.height
        or radius < 0
    ):
        raise ValueError("image panel box is invalid")
    panel = ImageOps.fit(image, (right - left, bottom - top), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", panel.size, 0)
    from PIL import ImageDraw

    ImageDraw.Draw(mask).rounded_rectangle((0, 0, panel.width - 1, panel.height - 1), radius=radius, fill=255)
    base.paste(panel, (left, top), mask)


def centered(draw, text: str, y: int, font, fill=DARK) -> None:
    draw.text(((W - draw.textlength(text, font=font)) / 2, y), text, fill=fill, font=font)


def footer(draw, right: str) -> None:
    draw.rounded_rectangle([BORDER, H - BORDER - 86, W - BORDER, H - BORDER], radius=22, fill=DARK)
    draw.text((BORDER + 40, H - BORDER - 68), "只发夸克", fill="white", font=get_font(24, True))
    font = get_font(20)
    draw.text((W - BORDER - 40 - draw.textlength(right, font=font), H - BORDER - 47), right, fill=(203, 213, 225), font=font)


def render_cover(root: Path, out: Path) -> None:
    im, d = draw_board()
    world = image_fit(root / "超高清晰世界地图.jpg", (960, 510))
    china = image_fit(root / "一亿像素中国地图.jpg", (360, 510))
    image_panel(im, china, (60, 258, 420, 768), radius=18)
    image_panel(im, world, (440, 258, 1020, 768), radius=18)
    d.rounded_rectangle([60, 258, 1020, 768], radius=18, outline=(255, 255, 255), width=6)
    d.rounded_rectangle([60, 258, 420, 768], radius=18, outline=(255, 255, 255), width=6)

    badge = "468个文件 · 约7.24GB"
    font = get_font(24, True)
    badge_w = d.textlength(badge, font=font) + 40
    d.rounded_rectangle([(W - badge_w) / 2, 78, (W + badge_w) / 2, 120], radius=21, fill=BLUE)
    centered(d, badge, 86, font, "white")
    centered(d, "高清一亿像素地图", 150, get_font(50, True))
    centered(d, "超精细地理素材合集", 224, get_font(30), GRAY)
    d.rounded_rectangle([60, 802, 1020, 914], radius=20, fill=PALE, outline=(226, 232, 240), width=1)
    d.text((86, 826), "中国地图 · 世界地图 · 各省区域 · 矢量源文件", fill=DARK, font=get_font(24, True))
    d.text((86, 869), "高清预览、分类齐全，设计排版更省心", fill=GRAY, font=get_font(21))
    footer(d, "468个文件 · 地图素材合集")
    save_png(im, out / "01.png")


def render_catalog(root: Path, out: Path) -> None:
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "素材目录", fill=DARK, font=get_font(44, True))
    d.text((BORDER + 40, BORDER + 88), "按地图类型与源文件格式整理，查找更直观", fill=GRAY, font=get_font(24))
    image_panel(im, image_fit(root / "一亿像素中国地图.jpg", (420, 265)), (60, 170, 480, 435), radius=16)
    image_panel(im, image_fit(root / "超高清晰世界地图.jpg", (540, 265)), (500, 170, 1040, 435), radius=16)
    categories = [
        ("高清地图", "中国地图、世界地图、各省区域图", BLUE),
        ("矢量源文件", "CDR、AI、PSD、EPS等格式", TEAL),
        ("专题地图", "交通、区域、自然、旅游等分类", GREEN),
        ("办公与设计", "PDF、PPT、SWF等配套素材", ORANGE),
    ]
    y = 480
    for index, (title, desc, color) in enumerate(categories):
        x = 60 + (index % 2) * 500
        yy = y + (index // 2) * 150
        d.rounded_rectangle([x, yy, x + 460, yy + 120], radius=18, fill=PALE, outline=(226, 232, 240), width=1)
        d.rounded_rectangle([x + 20, yy + 22, x + 72, yy + 74], radius=16, fill=color)
        d.text((x + 39, yy + 34), str(index + 1), fill="white", font=get_font(22, True))
        d.text((x + 94, yy + 23), title, fill=DARK, font=get_font(24, True))
        d.text((x + 94, yy + 65), desc, fill=GRAY, font=get_font(18))
    footer(d, "高清图片 · 矢量源文件 · 468个文件")
    save_png(im, out / "02.png")


def render_outcomes(root: Path, out: Path) -> None:
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "使用收获", fill=DARK, font=get_font(44, True))
    d.text((BORDER + 40, BORDER + 88), "一套素材，覆盖多种地图视觉与设计需求", fill=GRAY, font=get_font(24))
    preview = image_fit(root / "中国各省高清晰巨幅地图/中国.jpg", (930, 410))
    image_panel(im, preview, (60, 170, 1020, 580), radius=18)
    d.rounded_rectangle([60, 170, 1020, 580], radius=18, outline=(255, 255, 255), width=6)
    points = [
        ("高清预览", "中国、世界、各省及区域地图，打开即可查看细节", BLUE),
        ("分类齐全", "按地图主题和文件格式整理，查找目标素材更方便", TEAL),
        ("可编辑源文件", "包含 CDR、AI、PSD、EPS 等多种格式", GREEN),
        ("使用场景广", "适合设计排版、宣传物料、地理类内容制作", ORANGE),
    ]
    for index, (title, desc, color) in enumerate(points):
        x = 60 + (index % 2) * 500
        y = 625 + (index // 2) * 140
        d.rounded_rectangle([x, y, x + 460, y + 110], radius=18, fill=PALE, outline=(226, 232, 240), width=1)
        d.ellipse([x + 20, y + 28, x + 72, y + 80], fill=color)
        d.text((x + 38, y + 41), str(index + 1), fill="white", font=get_font(22, True))
        d.text((x + 94, y + 18), title, fill=DARK, font=get_font(23, True))
        font = get_font(17)
        for line_no, line in enumerate(wrap_text(desc, font, 340, d)[:2]):
            d.text((x + 94, y + 56 + line_no * 23), line, fill=GRAY, font=font)
    footer(d, "真实地图预览 · 多种格式")
    save_png(im, out / "03.png")


def render_guide(root: Path, out: Path) -> None:
    im, d = draw_board()
    d.text((BORDER + 40, BORDER + 30), "购买前说明", fill=DARK, font=get_font(44, True))
    d.text((BORDER + 40, BORDER + 88), "虚拟资料 · 下单后提供网盘链接与提取码", fill=GRAY, font=get_font(24))
    steps = [
        ("1", "资料内容", "中国地图、世界地图、各省区域图、专题地图及源文件"),
        ("2", "文件格式", "JPG、CDR、AI、PSD、EPS、PDF、PPT等格式，按目录分类"),
        ("3", "使用方式", "先浏览目录，再根据设计项目选择地图或可编辑源文件"),
        ("4", "交付方式", "拍后提供网盘链接与提取码，链接不写入商品文案"),
    ]
    y = 190
    for number, title, desc in steps:
        d.rounded_rectangle([BORDER + 40, y, W - BORDER - 40, y + 112], radius=18, fill=PALE, outline=(226, 232, 240), width=1)
        d.ellipse([BORDER + 62, y + 31, BORDER + 108, y + 77], fill=BLUE)
        d.text((BORDER + 78, y + 41), number, fill="white", font=get_font(22, True))
        d.text((BORDER + 132, y + 21), title, fill=DARK, font=get_font(24, True))
        font = get_font(18)
        for line_no, line in enumerate(wrap_text(desc, font, W - BORDER * 2 - 170, d)[:2]):
            d.text((BORDER + 132, y + 58 + line_no * 24), line, fill=GRAY, font=font)
        y += 132
    d.rounded_rectangle([BORDER + 40, 750, W - BORDER - 40, 912], radius=18, fill=(255, 251, 235), outline=(253, 230, 138), width=1)
    d.text((BORDER + 62, 778), "温馨提示", fill=(146, 64, 14), font=get_font(23, True))
    tip = "素材包含不同尺寸和格式，请根据软件兼容性、设计需求和使用场景选择文件。购买前可先咨询需要的地图或格式。"
    font = get_font(18)
    for line_no, line in enumerate(wrap_text(tip, font, W - BORDER * 2 - 130, d)[:3]):
        d.text((BORDER + 62, 822 + line_no * 25), line, fill=(120, 113, 108), font=font)
    footer(d, "468个文件 · 约7.24GB")
    save_png(im, out / "04.png")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成高清地图矢量素材合集四张图文")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="地图素材源目录")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="图片输出目录")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    render_cover(args.root, args.out)
    render_catalog(args.root, args.out)
    render_outcomes(args.root, args.out)
    render_guide(args.root, args.out)
    invalid = validate_png_files(args.out, size=(W, H))
    if invalid:
        raise RuntimeError("图片文件校验失败：" + ", ".join(str(path) for path in invalid))
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
