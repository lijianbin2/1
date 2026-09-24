"""Shared helpers for Xianyu image-text rendering scripts."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_REGULAR = r"C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = r"C:/Windows/Fonts/msyhbd.ttc"


def get_font(size, bold=False, strict=True):
    """Load the configured Chinese font, failing loudly by default."""
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except OSError as exc:
        if strict:
            raise RuntimeError(f"无法加载字体：{path}（{exc}）") from exc
        return ImageFont.load_default()


def draw_board(w=1080, h=1080, border=38, blue=(47, 93, 255), radius=32):
    """Blue outer board + white rounded inner card. Returns (img, draw)."""
    im = Image.new("RGB", (w, h), blue)
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle(
        [border, border, w - border, h - border], radius=radius, fill="white"
    )
    return im, draw


def wrap_text(text, font, max_w, draw):
    """按像素宽度逐字换行，空文本返回空列表。"""
    if not text:
        return []
    if max_w <= 0:
        raise ValueError("max_w must be greater than zero")

    lines = []
    line = ""
    for ch in text:
        test = line + ch
        if draw.textlength(test, font=font) > max_w:
            if line:
                lines.append(line)
            line = ch
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def badge_geometry(draw, text, font, pad_x=40, height=42):
    """返回徽章的 ``(width, height)``；横向位置由调用方计算。"""
    w = draw.textlength(text, font=font) + pad_x
    return w, height


def save_png(im, path):
    """创建父目录并保存 PNG，返回文件大小（字节）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p, format="PNG")
    size = p.stat().st_size
    print(f"saved {p} bytes={size}")
    return size


def check_text_rules(title, body, forbidden, required):
    """执行标题和正文的禁用词、必需词检查，返回违规代码列表。"""
    violations = []
    for i, word in enumerate(forbidden):
        if word in title:
            violations.append("forbidden[%d]-in-title" % i)
        if word in body:
            violations.append("forbidden[%d]-in-body" % i)
    for i, word in enumerate(required):
        if word not in title and word not in body:
            violations.append("required[%d]-missing" % i)
    return violations
