"""所有渲染页都不能出现大片纵向死区。

白卡内、底栏以上的区域如果连续一整行都没有墨迹，就是版式上多出来的一块空洞。
空洞不会让程序报错，只会让图看起来没排完，所以只能靠自动扫描兜住。

用墨迹行扫描而不是人眼看图：早先后加卡片高度时，180px 的内容塞进 460px 的
卡里，反而多出一大片空白。补内容才对，拉高卡片只会把洞做大。

扫描实现放在 ``scan_zones.py``，测试直接 import 同一份代码，避免工具和测试
各写一套判定、跑到不同结论。
"""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from legacy_runner import run_legacy
from scan_zones import ABOVE_FOOTER, geometry, ink_bands, scan_page


class LayoutZoneTests(unittest.TestCase):
    def _scan(self, out: Path, label: str, geo: tuple[int, int, int, int]) -> list[str]:
        problems: list[str] = []
        for page in sorted(out.glob("*.png")):
            problems.extend(f"{label}/{issue}" for issue in scan_page(page, geo))
        return problems

    def test_legacy_renderers_have_no_large_vertical_void(self):
        """codex55 / workbuddy / winrar 三个脚本。

        cover_v2 不参与：它是整幅渐变的全出血封面，没有白卡也没有底栏，
        逐行问"有没有墨"必然每行都有，扫描会恒为 0px，属于空跑。
        """
        problems: list[str] = []
        with tempfile.TemporaryDirectory() as root:
            for label, script in (
                ("codex55", "render_codex55_legacy.py"),
                ("workbuddy", "render_workbuddy_legacy.py"),
                ("winrar", "render_winrar_unified_legacy.py"),
            ):
                out = Path(root) / label
                out.mkdir(parents=True, exist_ok=True)
                namespace = run_legacy(script, out)
                problems.extend(self._scan(out, label, geometry(namespace)))

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
            problems.extend(self._scan(out, "camera", geometry(camera)))

            for render in (
                promo.render_cover,
                promo.render_catalog,
                promo.render_outcomes,
                promo.render_guide,
            ):
                render(out)
            problems.extend(self._scan(out, "promo", geometry(promo)))
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
            problems.extend(self._scan(out, "map", geometry(maps)))
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
            bands = ink_bands(page, top=38, bottom=956 - ABOVE_FOOTER, left=38, right=1042, limit=50)
            self.assertTrue(
                any(height >= 200 for _, height in bands),
                f"扫描器漏掉了人为画出的 200px 空洞：{bands}",
            )

    def test_scanner_rejects_a_region_larger_than_the_page(self):
        """扫描区域超出画布必须报错，不能悄悄截断后报"没有空洞"。"""
        with tempfile.TemporaryDirectory() as root:
            page = Path(root) / "small.png"
            Image.new("RGB", (400, 400), "white").save(page)
            with self.assertRaises(ValueError):
                ink_bands(page, top=38, bottom=900, left=38, right=1042)


if __name__ == "__main__":
    unittest.main()
