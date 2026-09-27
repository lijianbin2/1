import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageFont

import render_jianying_templates as jianying
from render_jianying_templates import (
    CATEGORY_RULES,
    DEFAULT_ROOT,
    H,
    W,
    catalog_grid,
    categorize,
    category_table,
    cover_grid,
    guide_layout,
    outcomes_layout,
    render_catalog,
    render_cover,
    render_guide,
    render_outcomes,
    stats_labels,
)
from test_xianyu_common import footer_text_bands
from verify_source import SourceStats, scan_source


def _sample_table() -> list[tuple[str, int, tuple[int, int, int]]]:
    """造一份和实测同形的分类表，用于不依赖源目录的版式测试。"""
    return [
        (name, 5, jianying.COLORS[index])
        for index, (name, _tone, _kw) in enumerate(CATEGORY_RULES)
    ]


def _render_all(out: Path, table=None) -> None:
    table = table if table is not None else _sample_table()
    labels = ("41个模板", "约3.74GB")
    with patch("render_jianying_templates.get_font", return_value=ImageFont.load_default()):
        render_cover(out, table, *labels)
        render_catalog(out, table, *labels)
        render_outcomes(out, table, *labels)
        render_guide(out, table, *labels)


class CategoryRuleTests(unittest.TestCase):
    def test_classify_matches_the_real_source_directory(self):
        """分类数量必须等于源目录实测值，否则图上写的就是假数。

        CATEGORY_RULES 是有序规则，命中即归类不再往下看：文件名同时含两组
        关键词时归到先命中的那一组。调换顺序会让实测数量变样，所以这里用
        实跑源目录把数字钉住，而不是把期望值当成设计意图。
        """
        stats = scan_source(DEFAULT_ROOT)
        table = category_table(DEFAULT_ROOT)
        measured = {name: count for name, count, _color in table}

        self.assertEqual(
            measured,
            {
                "企业历程回顾": 8,
                "表彰励志年会": 6,
                "照片墙相册": 5,
                "卡点快闪电商": 5,
                "企业文化介绍": 7,
                "科技风高级感": 3,
                "片头与通用宣传": 7,
            },
        )
        self.assertEqual(sum(measured.values()), stats.total_files)

    def test_every_source_file_lands_in_exactly_one_category(self):
        """认不出分类的文件必须直接报错，不允许静默丢掉。"""
        paths = sorted(p for p in DEFAULT_ROOT.rglob("*") if p.is_file())
        self.assertEqual(len(paths), 41)
        for path in paths:
            with self.subTest(name=path.name):
                self.assertIn(categorize(path.name), {n for n, _t, _k in CATEGORY_RULES})
        with self.assertRaises(ValueError):
            categorize("99-无法归类的东西.zip")

    def test_source_stats_feed_the_labels(self):
        """数量和体积都从实测统计来，不手打。"""
        self.assertEqual(
            stats_labels(SourceStats(root=Path("x"), total_files=41, total_bytes=int(3.74 * 1024**3))),
            ("41个模板", "约3.74GB"),
        )

    def test_no_hardcoded_category_counts(self):
        """图上的分类明细只能来自 category_table，源码里不许写死数字。"""
        source = Path(jianying.__file__).read_text(encoding="utf-8")
        offenders = [
            line.strip()
            for line in source.splitlines()
            if re.search(r'\d+\s*个(?:模板|分类|片头|相册|快闪)', line)
        ]
        self.assertEqual(offenders, [], f"分类数量写死在源码里：{offenders}")


class LayoutTests(unittest.TestCase):
    def test_cover_grid_fits_seven_cards_above_the_summary(self):
        rows, bottom = cover_grid(7)
        self.assertEqual(rows, 3)
        self.assertLess(bottom, jianying.SUMMARY_TOP)
        with self.assertRaises(ValueError):
            cover_grid(0)
        with self.assertRaises(ValueError):
            cover_grid(10)

    def test_catalog_grid_is_derived_from_the_category_count(self):
        """02 页行数由分类数推出，7 张排 4 行，8 张就放不下。"""
        rows, bottom = catalog_grid(7)
        self.assertEqual(rows, -(-7 // jianying.CAT_COLS))
        self.assertLessEqual(bottom, jianying.FOOTER_TOP - jianying.CAT_CARD_GAP)
        with self.assertRaises(ValueError):
            catalog_grid(9)
        with self.assertRaises(ValueError):
            catalog_grid(0)

    def test_outcomes_layout_matches_the_four_points(self):
        grid_y, suit_y, card_h = outcomes_layout(4)
        self.assertGreaterEqual(card_h, jianying.OUT_CARD_H)
        self.assertGreaterEqual(suit_y - grid_y, 2 * card_h + jianying.OUT_GAP)
        self.assertLessEqual(suit_y + jianying.OUT_SUIT_H, jianying.FOOTER_TOP)
        with self.assertRaises(ValueError):
            outcomes_layout(0)
        with self.assertRaises(ValueError):
            outcomes_layout(9)

    def test_outcomes_page_whitespace_stays_within_the_void_limit(self):
        """03 页上下的留白要留在死区门槛内。

        四张卡加一条"适合谁"横条撑不满 1080 高，stack_layout 把余量均分到
        上下：实测卡片区上方约 100px、横条到底栏约 116px。和宣传片配乐页
        用的是同一组常量（190/82/24/190），留白形态一致，刻意保持不变。
        这里把上限钉住，日后改版式时先看这里再决定要不要填内容。
        """
        from scan_zones import VOID_LIMIT

        grid_y, suit_y, _card_h = outcomes_layout(4)
        self.assertLessEqual(grid_y - (jianying.BORDER + 140), VOID_LIMIT)
        self.assertLessEqual(jianying.FOOTER_TOP - (suit_y + jianying.OUT_SUIT_H), VOID_LIMIT)

    def test_guide_layout_keeps_steps_off_the_warning_box(self):
        tops, step_h, warn_top, warn_bottom = guide_layout(4)
        self.assertEqual(len(tops), 4)
        for upper, lower in zip(tops, tops[1:]):
            self.assertGreaterEqual(lower - (upper + step_h), jianying.STEP_GAP)
        self.assertGreaterEqual(warn_top - (tops[-1] + step_h), jianying.STEP_GAP)
        self.assertLessEqual(warn_bottom, jianying.FOOTER_TOP)
        with self.assertRaises(ValueError):
            guide_layout(0)
        with self.assertRaises(ValueError):
            guide_layout(6)


class RenderTests(unittest.TestCase):
    def test_all_renderers_create_four_square_images(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            out.mkdir()
            _render_all(out)
            for number in range(1, 5):
                with Image.open(out / f"{number:02d}.png") as image:
                    self.assertEqual(image.size, (W, H))

    def test_footer_two_text_lines_do_not_touch(self):
        """底栏两行必须分得开，间距 4px 以上。"""
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            out.mkdir()
            # 这里必须用真实字体：换成点阵默认字形量的就不是发布的图了。
            render_cover(out, _sample_table(), "41个模板", "约3.74GB")
            bands = footer_text_bands(out / "01.png", jianying)
        self.assertEqual(len(bands), 2, f"底栏应该正好两行文字，实际 {bands}")
        first, second = bands
        gap = second[0] - (first[0] + first[1])
        self.assertGreater(gap, 4, f"底栏两行间距只有 {gap}px，会连成一片")

    def test_entrypoint_rejects_a_table_that_drops_files(self):
        """有文件认不出分类时入口必须报错，不能带着残缺的表出图。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            for name in ("1-历程.zip", "2-表彰.zip", "3-认不出来的题材.zip"):
                (root / name).write_bytes(b"x")
            out = Path(directory) / "out"
            with patch("sys.argv", ["render_jianying_templates", "--root", str(root), "--out", str(out)]):
                with self.assertRaises(ValueError):
                    jianying.main()


if __name__ == "__main__":
    unittest.main()
