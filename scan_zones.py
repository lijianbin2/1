"""纵向死区扫描：白卡内、底栏以上不能出现大片空白横带。

空洞不会让程序报错，只会让图看起来没排完，所以要靠自动扫描兜住。
早先后加卡片高度时，180px 的内容塞进 460px 的卡里，反而多出一大片空白——
补内容才对，拉高卡片只会把洞做大。

本模块同时是库和命令行工具，几何常量一律从渲染器读，不在这里抄一份
1080/38/86。``tests/test_layout_zones.py`` 直接复用这里的实现，两边不会走偏。
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from xianyu_common import enable_utf8_stdout

ROOT = Path(__file__).resolve().parent

# 连续空白超过这个高度就算死区，需要回头补内容。
VOID_LIMIT = 170
# 报告用的下限，低于它的空白属于正常行距，不打印。
REPORT_LIMIT = 60
# 底栏横条上方还要留一点余量，别把横条上沿算进死区。
ABOVE_FOOTER = 20

# 有白卡底栏、可以扫描的入口。
ENTRYPOINTS = (
    "render_camera_basics.py",
    "render_codex55.py",
    "render_map_collection.py",
    "render_promo_music.py",
    "render_winrar_unified.py",
    "render_workbuddy.py",
)

# 明确说明为什么不扫，比悄悄漏掉强。
SKIPPED = {
    "cover_v2.py": "整幅渐变全出血封面，没有白卡也没有底栏，"
    "逐行问有没有墨必然每行都有，扫描恒为 0px，属于空跑。",
}


def geometry(source: Any) -> tuple[int, int, int, int]:
    """从渲染器取 (宽, 高, 边框, 底栏上沿)，不抄常量。

    ``source`` 可以是模块，也可以是 ``legacy_runner.run_legacy`` 返回的
    全局命名空间字典。winrar 的底栏常量叫 ``BAR_TOP``，这里做一次兜底。
    """
    get = (
        source.get
        if isinstance(source, dict)
        else lambda key, default=None: getattr(source, key, default)
    )
    footer_top = get("FOOTER_TOP")
    if footer_top is None:
        footer_top = get("BAR_TOP")
    return get("W"), get("H"), get("BORDER"), footer_top


def ink_bands(
    path: Path,
    *,
    top: int,
    bottom: int,
    left: int,
    right: int,
    limit: int = REPORT_LIMIT,
) -> list[tuple[int, int]]:
    """返回图中连续无墨迹的横带，格式为 (起始 y, 高度)。

    扫描区域必须由调用方显式给出，且不能超出画布：悄悄截断后报没有空洞，
    比直接报错危险得多。负坐标和上下颠倒的区域同样要拒——numpy 的负索引
    会让切片悄悄变成空数组，照样报"没有空洞"，等于把检查关掉了。
    """
    if min(top, left) < 0:
        raise ValueError(f"{path} 扫描区域起点不能为负：y={top} x={left}")
    if bottom <= top or right <= left:
        raise ValueError(
            f"{path} 扫描区域上下颠倒：y=[{top},{bottom}) x=[{left},{right})"
        )
    gray = np.array(Image.open(path).convert("L"))
    if gray.shape[0] < bottom or gray.shape[1] < right:
        raise ValueError(
            f"{path} 尺寸 {gray.shape[1]}x{gray.shape[0]} 容不下扫描区域 "
            f"y=[{top},{bottom}) x=[{left},{right})"
        )
    inner = gray[top:bottom, left:right]
    has_ink = (inner < 240).any(axis=1)
    bands: list[tuple[int, int]] = []
    start: int | None = None
    for offset, inked in enumerate(has_ink):
        if inked:
            if start is not None:
                bands.append((start + top, offset - start))
                start = None
        elif start is None:
            start = offset
    if start is not None:
        bands.append((start + top, len(has_ink) - start))
    return [band for band in bands if band[1] >= limit]


def scan_page(page: Path, geo: tuple[int, int, int, int]) -> list[str]:
    """扫描单页，返回超过死区阈值的说明文字。"""
    width, _, border, footer_top = geo
    found = [
        (start, height)
        for start, height in ink_bands(
            page,
            top=border,
            bottom=footer_top - ABOVE_FOOTER,
            left=border,
            right=width - border,
        )
        if height > VOID_LIMIT
    ]
    return [f"{page.name} 在 y={start} 处空了 {height}px" for start, height in found]


def main() -> int:
    enable_utf8_stdout()
    import legacy_runner
    import render_camera_basics as camera
    import render_codex55 as codex55
    import render_map_collection as maps
    import render_promo_music as promo
    import render_winrar_unified as winrar
    import render_workbuddy as workbuddy

    # legacy 三个入口的几何常量在 legacy 脚本里，只能从 run_legacy 的返回值取
    legacy_of = {
        "render_codex55.py": "render_codex55_legacy.py",
        "render_winrar_unified.py": "render_winrar_unified_legacy.py",
        "render_workbuddy.py": "render_workbuddy_legacy.py",
    }
    modules = {
        "render_camera_basics.py": camera,
        "render_codex55.py": codex55,
        "render_map_collection.py": maps,
        "render_promo_music.py": promo,
        "render_winrar_unified.py": winrar,
        "render_workbuddy.py": workbuddy,
    }

    def render(entry: str, out: Path) -> Any:
        """渲染一个入口，返回它的几何来源（模块或 legacy 命名空间）。"""
        out.mkdir(parents=True, exist_ok=True)
        if entry in legacy_of:
            return legacy_runner.run_legacy(legacy_of[entry], out)
        # 库渲染器走 CLI 入口，和用户实际发布的路径保持一致
        # 脚本路径必须绝对：用相对文件名时从项目根以外运行会直接报
        # "can't open file ... exit status 2"，扫描器就成了只能在特定目录下
        # 跑一次的脚本。
        subprocess.run(
            [sys.executable, str(ROOT / entry), "--out", str(out)],
            check=True,
            capture_output=True,
        )
        return modules[entry]

    problems: list[str] = []
    with tempfile.TemporaryDirectory() as root:
        for entry in ENTRYPOINTS:
            out = Path(root) / entry.removesuffix(".py")
            geo = geometry(render(entry, out))
            print(f"--- {entry} ---")
            for page in sorted(out.glob("*.png")):
                issues = scan_page(page, geo)
                problems.extend(f"{entry}/{issue}" for issue in issues)
                print(f"  {page.name} {issues or 'ok'}")

    for entry, reason in SKIPPED.items():
        print(f"--- {entry} 跳过 --- {reason}")

    if problems:
        print("\n发现死区：\n" + "\n".join(problems))
        return 1
    print(f"\n没有超过 {VOID_LIMIT}px 的死区")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
