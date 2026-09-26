"""所有渲染页都不能出现大片纵向死区。

白卡内、底栏以上的区域如果连续一整行都没有墨迹，就是版式上多出来的一块空洞。
空洞不会让程序报错，只会让图看起来没排完，所以只能靠自动扫描兜住。

用墨迹行扫描而不是人眼看图：早先后加卡片高度时，180px 的内容塞进 460px 的
卡里，反而多出一大片空白。补内容才对，拉高卡片只会把洞做大。
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from legacy_runner import run_legacy

# 白卡内边距，四个渲染器一致。
BORDER = 38
# 底部深色横条高度，扫描范围要在它上面。
FOOTER_H = 86
# 连续空白超过这个高度就算死区，需要回头补内容。
VOID_LIMIT = 170
# 报告用的下限，低于它的空白属于正常行距，不打印。
REPORT_LIMIT = 60

LEGACY_RENDERERS = {
    "cover_v2": "cover_v2_legacy.py",
    "codex55": "render_codex55_legacy.py",
    "workbuddy": "render_workbuddy_legacy.py",
    "winrar": "render_winrar_unified_legacy.py",
}


def ink_bands(
    path: Path,
    *,
    top: int = BORDER,
    bottom: int = 1080 - BORDER - FOOTER_H,
    limit: int = REPORT_LIMIT,
) -> list[tuple[int, int]]:
    """返回图中连续无墨迹的横带，格式为 (起始 y, 高度)。"""
    gray = np.array(Image.open(path).convert("L"))
    inner = gray[top:bottom, BORDER : 1080 - BORDER]
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


class LayoutZoneTests(unittest.TestCase):
    def _scan(self, out: Path, label: str) -> list[str]:
        problems = []
        for page in sorted(out.glob("*.png")):
            for start, height in ink_bands(page):
                if height > VOID_LIMIT:
                    problems.append(
                        f"{label}/{page.name} 在 y={start} 处空了 {height}px"
                    )
        return problems

    def test_legacy_renderers_have_no_large_vertical_void(self):
        problems: list[str] = []
        with tempfile.TemporaryDirectory() as root:
            for label, script in LEGACY_RENDERERS.items():
                out = Path(root) / label
                out.mkdir(parents=True, exist_ok=True)
                run_legacy(script, out)
                problems.extend(self._scan(out, label))
        self.assertEqual(problems, [], "版面出现大片空白：\n" + "\n".join(problems))

    def test_library_renderers_have_no_large_vertical_void(self):
        import render_camera_basics as camera
        import render_promo_music as promo

        problems: list[str] = []
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            for render in (
                camera.render_cover,
                camera.render_catalog,
                camera.render_outcomes,
                camera.render_guide,
            ):
                render(out)
            problems.extend(self._scan(out, "camera"))

            for render in (
                promo.render_cover,
                promo.render_catalog,
                promo.render_outcomes,
                promo.render_guide,
            ):
                render(out)
            problems.extend(self._scan(out, "promo"))
        self.assertEqual(problems, [], "版面出现大片空白：\n" + "\n".join(problems))

    def test_map_renderer_has_no_large_vertical_void(self):
        import render_map_collection as maps
        from PIL import ImageFont
        from unittest.mock import patch

        problems: list[str] = []
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "source"
            (source / "中国各省高清晰巨幅地图").mkdir(parents=True)
            for name in (
                "超高清晰世界地图.jpg",
                "一亿像素中国地图.jpg",
                "中国各省高清晰巨幅地图/中国.jpg",
            ):
                # 用中灰而不是纯白：扫描器按"有没有墨迹"判断，纯白占位图会让
                # 整块地图面板看起来是死区，那是占位图的假象，不是真实版式问题。
                Image.new("RGB", (300, 180), (170, 170, 170)).save(source / name)
            out = Path(root) / "out"
            out.mkdir()
            labels = ("3个文件", "约0.00GB")
            with patch("render_map_collection.get_font", return_value=ImageFont.load_default()):
                for render in (
                    maps.render_cover,
                    maps.render_catalog,
                    maps.render_outcomes,
                    maps.render_guide,
                ):
                    render(source, out, *labels)
            problems.extend(self._scan(out, "map"))
        self.assertEqual(problems, [], "版面出现大片空白：\n" + "\n".join(problems))

    def test_scanner_detects_a_planted_void(self):
        """扫描器本身要能报出空洞，否则上面的"全通过"没有意义。"""
        with tempfile.TemporaryDirectory() as root:
            page = Path(root) / "void.png"
            canvas = Image.new("RGB", (1080, 1080), "white")
            pixels = canvas.load()
            for y in range(400, 600):
                for x in range(38, 1042):
                    pixels[x, y] = (200, 200, 200)
            canvas.save(page)
            bands = ink_bands(page, limit=50)
            self.assertTrue(
                any(height >= 200 for _, height in bands),
                f"扫描器漏掉了人为画出的 200px 空洞：{bands}",
            )


if __name__ == "__main__":
    unittest.main()
