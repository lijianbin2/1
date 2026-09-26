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
    if (
        not all(isinstance(value, int) and not isinstance(value, bool) for value in (w, h, border, radius))
        or min(w, h) <= 0
        or border < 0
        or radius < 0
        or border * 2 >= min(w, h)
        or radius * 2 > min(w, h)
    ):
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
    """验证一组 PNG 文件存在且尺寸正确，返回实际问题列表。

    ``names`` 只接受纯文件名，避免调用方意外把校验范围扩展到目录外。
    损坏或无法解码的图片也作为问题返回，保证批量任务能收集完整报告。
    """
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError("count must be greater than zero")
    if (
        not isinstance(size, tuple)
        or len(size) != 2
        or any(
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
            for value in size
        )
    ):
        raise ValueError("size must contain two positive integers")

    directory = Path(directory)
    filenames = (
        list(names)
        if names is not None
        else [f"{i:02d}.png" for i in range(1, count + 1)]
    )
    problems: list[Path] = []
    seen: set[str] = set()
    for filename in filenames:
        if (
            not isinstance(filename, str)
            or not filename
            or filename in {".", ".."}
            or Path(filename).name != filename
            or Path(filename).is_absolute()
        ):
            problems.append(Path(str(filename)))
            continue
        if filename in seen:
            problems.append(directory / filename)
            continue
        seen.add(filename)
        path = directory / filename
        if not path.is_file():
            problems.append(path)
            continue
        try:
            with Image.open(path) as image:
                if image.format != "PNG" or image.size != size:
                    problems.append(path)
                    continue
                image.load()
        except (OSError, ValueError):
            problems.append(path)
    return problems
