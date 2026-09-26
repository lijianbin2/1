"""Shared helpers for Xianyu image-text rendering scripts."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont

FONT_REGULAR = r"C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = r"C:/Windows/Fonts/msyhbd.ttc"


def enable_utf8_stdout() -> None:
    """把标准输出切到 UTF-8，避免中文路径和提示在控制台显示成乱码。

    Windows 控制台默认按本地代码页解码 Python 的输出，而这里的路径和提示
    都含中文，不切换就会打印成乱码，用户看不到图到底存到了哪里。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                # 已被重定向到不支持编码设置的对象时，保持原状即可
                pass


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


def chip_positions(
    draw,
    labels: Iterable[str],
    *,
    font,
    left: float,
    right: float,
    pad: float = 28,
    gap: float = 14,
    label: str = "标签行",
) -> list[tuple[str, float, float]]:
    """算一行圆角标签的坐标，放不下就抛错。

    早先各处是手写 `sx += w + gap` 一路排下去，越界了也不报错，图照常生成，
    只是最后一个标签被画到卡片外面。winrar 03 页的换行守卫更糟：溢出时只把
    `sx` 重置回起点，不改 y，新标签就压在同一个位置，两块圆角框叠在一起。
    两者都是"渲染成功但成品是错的"，所以这里在坐标阶段就拒绝。
    """
    if right <= left:
        raise ValueError("chip row must have positive width")

    positions: list[tuple[str, float, float]] = []
    x = left
    for text in labels:
        width = draw.textlength(text, font=font) + pad
        if x + width > right:
            raise ValueError(
                f"{label}放不下：{text!r} 需要到 {x + width:.0f}，右边界是 {right:.0f}；"
                "请减少标签、缩短文案或加大容器"
            )
        positions.append((text, x, width))
        x += width + gap
    return positions


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


def wrap_text_fit(
    text: str,
    font,
    max_w: float,
    max_lines: int,
    draw,
    *,
    label: str = "",
) -> list[str]:
    """换行并断言不超过 ``max_lines`` 行，超出直接报错。

    直接写 ``wrap_text(...)[:2]`` 会在文案变长时静默丢掉末行：图还是能
    渲染成功，只是少了半句话，既不会报错也没人能从成品里看出来。实测
    地图合集 03 页的前两张卡片已经正好占满 2 行，稍微改几个字就会触发。
    所以截断在这里显式化，放不下就抛错，让文案改动在渲染阶段暴露。
    """
    if not isinstance(max_lines, int) or isinstance(max_lines, bool) or max_lines < 1:
        raise ValueError("max_lines must be greater than zero")
    lines = wrap_text(text, font, max_w, draw)
    if len(lines) > max_lines:
        where = f"{label} " if label else ""
        raise ValueError(
            f"{where}文案超出 {max_lines} 行（实际 {len(lines)} 行），"
            f"请缩短文案或调整字号：{text!r}"
        )
    return lines


def stack_blocks(
    heights: Iterable[float],
    top: float,
    bottom: float,
    *,
    grow: Iterable[int] = (),
    min_gap: float = 20,
    max_gap: float = 48,
    max_grow: float | None = None,
) -> list[int]:
    """同 :func:`stack_layout`，只返回每个区块的起始 y。"""
    tops, _ = stack_layout(
        heights,
        top,
        bottom,
        grow=grow,
        min_gap=min_gap,
        max_gap=max_gap,
        max_grow=max_grow,
    )
    return tops


def stack_layout(
    heights: Iterable[float],
    top: float,
    bottom: float,
    *,
    grow: Iterable[int] = (),
    min_gap: float = 20,
    max_gap: float = 48,
    max_grow: float | None = None,
) -> tuple[list[int], list[float]]:
    """把若干纵向区块排布在 ``[top, bottom]`` 内，返回每个区块的起始 y。

    ``grow`` 里的下标对应可伸缩区块，会按比例吸收剩余空间（``max_grow``
    可限制单个区块的增长上限），避免内容偏少时在底部留下大片空白。
    伸缩后仍有剩余时再均分到首尾做居中。调整文案行数不需要改写死坐标。
    总高度超出可用区域时直接报错，避免静默溢出画布。

    返回 ``(起始 y 列表, 实际高度列表)``，需要按伸缩后的高度绘制内容时用
    :func:`stack_layout`，只需要起始位置时用 :func:`stack_blocks`。
    """
    sizes = [float(value) for value in heights]
    if not sizes:
        return [], []
    if any(value <= 0 for value in sizes):
        raise ValueError("block heights must be greater than zero")
    if min_gap < 0 or max_gap < min_gap:
        raise ValueError("gap bounds are invalid")
    if bottom <= top:
        raise ValueError("bottom must be greater than top")

    growable = {int(index) for index in grow}
    if any(index < 0 or index >= len(sizes) for index in growable):
        raise ValueError("grow index out of range")
    if max_grow is not None and max_grow <= 0:
        raise ValueError("max_grow must be greater than zero")

    if growable:
        slack = bottom - top - sum(sizes) - min_gap * (len(sizes) - 1)
        if slack > 0:
            share = slack / len(growable)
            if max_grow is not None:
                share = min(share, max_grow)
            for index in growable:
                sizes[index] += share

    slack = bottom - top - sum(sizes)
    count = len(sizes) - 1
    gap = min(max_gap, max(min_gap, slack // count)) if count else 0
    used = sum(sizes) + gap * count
    leftover = bottom - top - used
    y = top + (leftover // 2 if leftover > 0 else 0)

    tops: list[int] = []
    for size in sizes:
        tops.append(int(y))
        y += size + gap
    if tops[-1] + sizes[-1] > bottom:
        raise ValueError("区块总高度超出可用区域，版式无法容纳")
    return tops, sizes


def assert_no_overlap(blocks: Iterable[tuple[float, float]], label: str) -> None:
    """断言若干纵向区间互不重叠，label 用于失败时定位。"""
    ordered = sorted((float(top), float(bottom)) for top, bottom in blocks)
    for (prev_top, prev_bottom), (top, bottom) in zip(ordered, ordered[1:]):
        if top < prev_bottom:
            raise ValueError(f"{label} 区块重叠：{prev_bottom} > {top}")


def text_extent(draw, text: str, font, y: float) -> tuple[float, float]:
    """返回文本以 ``y`` 为基线起点时实际占据的纵向区间。

    ``draw.text`` 的 y 是文字顶部锚点，真实墨迹范围由 ``textbbox`` 决定，
    并不等于 ``y + 字号``：msyh 30px 实测占据 ``y+6`` 到 ``y+36``。凭锚点估算
    间距会低估文字底部，把字压到下一块内容上，所以版式校验一律用这个函数量
    真实范围。
    """
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return y + top, y + bottom


def assert_text_above(
    draw, text: str, font, y: float, limit: float, label: str
) -> None:
    """断言文本不会碰到 ``limit`` 以下的下一个内容块。"""
    _, bottom = text_extent(draw, text, font, y)
    if bottom > limit:
        raise ValueError(f"{label} 文字底部 {bottom:.0f} 超出可用范围 {limit:.0f}")


def fit_font(
    draw,
    text: str,
    max_w: float,
    size: int,
    *,
    bold: bool = False,
    min_size: int = 14,
    step: int = 2,
) -> tuple[Any, float]:
    """返回能把 ``text`` 塞进 ``max_w`` 的最大字体，放不下就报错。

    手写 "while 太宽就缩小" 容易漏掉下限：缩到最小仍放不下时会静默溢出，
    文字直接压出卡片。这里缩到 ``min_size`` 仍不满足就直接抛错，让版式
    问题在渲染时暴露，而不是靠目视发现。

    缩小要按步长走到 ``min_size`` 为止，不能再往下掉一档：``size`` 和
    ``min_size`` 相差不到 ``step`` 时（比如 21 和 20），照直减就会交出
    19px，等于给了调用方一个它没要求的字号。报错信息里的字号用实际测量
    的那个，而不是名义上的 ``min_size``，否则排查时会被误导。
    """
    current = size
    font = get_font(current, bold)
    width = draw.textlength(text, font=font)
    while width > max_w and current > min_size:
        current = max(current - step, min_size)
        font = get_font(current, bold)
        width = draw.textlength(text, font=font)
    if width > max_w:
        raise ValueError(
            f"文字放不下：{text!r} 在 {current}px 下仍需 {width:.0f}px，"
            f"可用宽度只有 {max_w:.0f}px"
        )
    return font, width


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

    ``names`` 为空列表同样报错。``count`` 拒绝小于 1，``names`` 却不设下限
    的话，传个空列表就会校验零个文件然后报告"通过"——比不校验还危险，
    因为调用方会以为产物已经验过了。
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
    if names is None:
        filenames = [f"{i:02d}.png" for i in range(1, count + 1)]
    else:
        filenames = list(names)
        if not filenames:
            raise ValueError("names must not be empty")
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


def require_valid_pngs(
    directory: str | Path,
    *,
    count: int = 4,
    size: tuple[int, int] = (1080, 1080),
    names: Iterable[str] | None = None,
    label: str = "图片",
) -> None:
    """校验产物并在有问题时抛错，成功时打印一行结果。

    所有公开渲染入口都应该在结束时调用它，这样"生成成功"和"产物可用"
    是同一件事，不依赖调用方记得再手动校验一次。
    """
    materialized = None if names is None else list(names)
    problems = validate_png_files(directory, count=count, size=size, names=materialized)
    if problems:
        raise RuntimeError(f"{label}校验失败：" + ", ".join(str(path) for path in problems))
    print(f"validated {label} files={count if materialized is None else len(materialized)}")
