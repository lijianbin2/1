import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageFont

import render_map_collection as maps_module
from render_map_collection import (
    W,
    H,
    guide_layout,
    image_fit,
    image_panel,
    render_catalog,
    render_cover,
    render_guide,
    render_outcomes,
    stats_labels,
)
from verify_source import SourceStats
from test_xianyu_common import footer_text_bands


class RenderMapCollectionTests(unittest.TestCase):
    def test_image_helpers_resize_and_paste(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            Image.new("RGB", (200, 120), "white").save(source)
            fitted = image_fit(source, (100, 80))
            self.assertEqual(fitted.size, (100, 80))

            base = Image.new("RGB", (200, 200), "white")
            image_panel(base, fitted, (20, 30, 120, 130), radius=8)
            self.assertEqual(base.getpixel((20, 30)), (255, 255, 255))
            with self.assertRaises(ValueError):
                image_panel(base, fitted, (20, 30, 10, 130))

    def test_all_renderers_create_four_square_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            (root / "中国各省高清晰巨幅地图").mkdir(parents=True)
            for name in ("超高清晰世界地图.jpg", "一亿像素中国地图.jpg", "中国各省高清晰巨幅地图/中国.jpg"):
                Image.new("RGB", (300, 180), "white").save(root / name)

            out = Path(directory) / "out"
            out.mkdir()
            labels = ("3个文件", "约0.00GB")
            with patch("render_map_collection.get_font", return_value=ImageFont.load_default()):
                render_cover(root, out, *labels)
                render_catalog(root, out, *labels)
                render_outcomes(root, out, *labels)
                render_guide(root, out, *labels)

            self.assertEqual((W, H), (1080, 1080))
            for number in range(1, 5):
                with Image.open(out / f"{number:02d}.png") as image:
                    self.assertEqual(image.size, (W, H))

    def test_stats_labels_come_from_measured_source(self):
        """数量和体积必须由实测统计推导，不能手打。"""
        stats = SourceStats(root=Path("any"), total_files=468, total_bytes=int(7.24 * 1024**3))
        self.assertEqual(stats_labels(stats), ("468个文件", "约7.24GB"))

    def test_catalog_cards_fill_the_gap_above_the_footer(self):
        """02 页四张卡必须撑到接近底栏，不能在下方留大片空白。

        早先卡片只有 120px 高、两行字，两行排完停在 750px，底栏在 956px，
        中间空出约 200px。这里直接量卡片区几何，不用逐像素扫描。
        """
        import render_map_collection as maps

        rows = 2
        grid_bottom = (
            maps.CAT_CARD_TOP
            + rows * maps.CAT_CARD_H
            + (rows - 1) * maps.CAT_CARD_GAP
        )
        # 卡片区底部离底栏的间距在合理呼吸范围内（不超过 90px）
        self.assertLessEqual(
            maps.FOOTER_TOP - grid_bottom,
            90,
            "02 页分类区到底栏之间空得太多",
        )
        # 卡片本身要容得下序号、标题、描述、分割线和细节两行
        self.assertGreaterEqual(maps.CAT_CARD_H, 180)

    def test_catalog_detail_text_fits_inside_its_card(self):
        """细节说明不能溢出卡片底边，用真实墨迹范围判定。"""
        import render_map_collection as maps
        from xianyu_common import get_font, text_extent

        from PIL import ImageDraw

        draw = ImageDraw.Draw(Image.new("RGB", (W, H), "white"))
        card_h = maps.CAT_CARD_H
        card_top = maps.CAT_CARD_TOP
        detail = "一亿像素原图，放大到印刷级也不糊"
        detail_font = get_font(17)
        top = card_top + 65 + 30 + 16
        _, bottom = text_extent(draw, detail, detail_font, top)
        self.assertLessEqual(bottom, card_top + card_h - 14)
        self.assertEqual(maps.FOOTER_TOP, H - 38 - 86)

    def test_footer_two_text_lines_do_not_touch(self):
        """底栏两行必须能分开，看清是两行而不是一团。

        早先这里写死 H-BORDER-68/-47，两行只差 21px，而 24px 与 20px 的
        真实墨迹几乎占满行高，实测间距 -4px，两行是叠在一起的。
        相机脚本早先栽在同一个坑上，改成 FOOTER_TOP+12/+48 之后间距 +11px。
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            (root / "中国各省高清晰巨幅地图").mkdir(parents=True)
            for name in ("超高清晰世界地图.jpg", "一亿像素中国地图.jpg", "中国各省高清晰巨幅地图/中国.jpg"):
                Image.new("RGB", (300, 180), "white").save(root / name)
            out = Path(directory) / "out"
            out.mkdir()
            labels = ("468个文件", "约7.24GB")
            # 这里不能把 get_font 换成 load_default：像素判定要量真实字形的
            # 墨迹范围，换成点阵默认字形后测的就不是实际发布的图了。
            render_cover(root, out, *labels)
            bands = footer_text_bands(out / "01.png", maps_module)

        self.assertEqual(
            len(bands),
            2,
            f"底栏应该正好两行文字，实际 {len(bands)} 带：{bands}",
        )
        first, second = bands
        gap = second[0] - (first[0] + first[1])
        self.assertGreater(gap, 4, f"底栏两行间距只有 {gap}px，看起来会连成一片")

    def test_guide_tip_block_follows_the_step_count(self):
        """04 页提示框必须跟着步骤数走，放不下就报错，不能压在底栏上。

        早先这里把卡片起始位置、每步增量和提示框位置各自写死（190 / +132 /
        750），三者之间没有约束。实测加到第 5 步时，第 5 张卡（718-830）直接
        压在提示框上，而脚本仍然退出码 0、图片照常生成。
        """
        import render_map_collection as maps

        # 4 步是当前版式：四张卡互不重叠，提示框留在底栏之上
        step_tops, warn_top, warn_bottom = guide_layout(4)
        self.assertEqual(len(step_tops), 4)
        for upper, lower in zip(step_tops, step_tops[1:]):
            self.assertGreaterEqual(
                lower - (upper + maps.GUIDE_STEP_H), maps.GUIDE_STEP_GAP,
                "相邻步骤卡压在一起了",
            )
        self.assertEqual(warn_top, step_tops[-1] + maps.GUIDE_STEP_H + maps.GUIDE_WARN_GAP)
        self.assertLessEqual(warn_bottom, maps.FOOTER_TOP)

        # 5 步在 1080 高的版面上放不下（第 5 张卡就到 830，提示框要到 1044），
        # 早先正是这个情况被静默画成重叠。现在必须报错。
        with self.assertRaises(ValueError):
            guide_layout(5)
        with self.assertRaises(ValueError):
            guide_layout(0)

    def test_guide_layout_constants_stay_in_one_place(self):
        """04 页不许再把版式数字写死在绘制代码里。"""
        import render_map_collection as maps

        source = (Path(maps.__file__)).read_text(encoding="utf-8")
        for literal in ("750", "912"):
            self.assertNotIn(
                f", {literal}]", source,
                f"04 页又出现写死的坐标 {literal}，版式数字应走 guide_layout",
            )
