"""Shared helpers for Xianyu image-text rendering scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

FONT_REGULAR = r"C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = r"C:/Windows/Fonts/msyhbd.ttc"


def get_font(size: int, bold: bool = False, strict: bool = True):
    """Load the configured Chinese font, failing loudly by default."""
    if size <= 0:
        raise ValueError("font size must be greater than zero")
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except OSError as exc:
        if strict:
            raise RuntimeError(f"无法加载字体：{path}（{exc}）") from exc
        return ImageFont.load_default()


def draw_board(
    w: int = 1080,
    h: int = 1080,
    border: int = 38,
    blue: tuple[int, int, int] = (47, 93, 255),
    radius: int = 32,
):
    """Blue outer board + white rounded inner card. Returns (img, draw)."""
    if min(w, h) <= 0 or border < 0 or border * 2 >= min(w, h):
        raise ValueError("board dimensions and border are invalid")
    im = Image.new("RGB", (w, h), blue)
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle(
        [border, border, w - border, h - border], radius=radius, fill="white"
    )
    return im, draw


def wrap_text(text: str, font, max_w: float, draw) -> list[str]:
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


def badge_geometry(draw, text: str, font, pad_x: int = 40, height: int = 42):
    """返回徽章的 ``(width, height)``；横向位置由调用方计算。"""
    if pad_x < 0 or height <= 0:
        raise ValueError("badge padding and height are invalid")
    w = draw.textlength(text, font=font) + pad_x
    return w, height


def save_png(im, path: str | Path):
    """创建父目录并保存 PNG，返回文件大小（字节）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p, format="PNG")
    size = p.stat().st_size
    print(f"saved {p} bytes={size}")
    return size


def validate_png_files(
    directory: str | Path,
    *,
    count: int = 4,
    size: tuple[int, int] = (1080, 1080),
    names: Iterable[str] | None = None,
) -> list[Path]:
    """验证一组 PNG 文件存在且尺寸正确，返回实际问题列表。"""
    if count < 1:
        raise ValueError("count must be greater than zero")
    directory = Path(directory)
    filenames = list(names) if names is not None else [f"{i:02d}.png" for i in range(1, count + 1)]
    problems: list[Path] = []
    for filename in filenames:
        path = directory / filename
        if not path.is_file():
            problems.append(path)
            continue
        with Image.open(path) as image:
            if image.format != "PNG" or image.size != size:
                problems.append(path)
    return problems


def check_text_rules(
    title: str,
    body: str,
    forbidden: Iterable[str],
    required: Iterable[str],
) -> list[str]:
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
