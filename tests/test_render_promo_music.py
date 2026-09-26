import re
import tempfile
import unittest
from pathlib import Path

import render_promo_music as promo

from test_xianyu_common import footer_text_bands


SOURCE = Path(promo.__file__).read_text(encoding="utf-8")
HARDCODED_COUNT = re.compile(r"[\"'][^\"'\n]*?(\d+)\s*首")

# verify_source.py 对 M:\WebDAV\夸克\软件\宣传片背景音乐合集… 的实测结果：
# 分类目录名标注数与实际 mp3 数量逐项一致，合计 970 个。
VERIFIED_TOTAL = 970
VERIFIED_CATEGORIES = (37, 67, 69, 88, 111, 111, 487)


def _source_outside_category_table() -> str:
    """排除 CATEGORIES 数据表本身，只检查渲染和文案部分。"""
    start = SOURCE.index("CATEGORIES = [")
    end = SOURCE.index("]", start)
    return SOURCE[:start] + SOURCE[end:]


class PromoMusicTests(unittest.TestCase):
    def test_categories_match_verified_source_scan(self):
        """分类数量必须等于源目录实测值，防止数据表悄悄过期。"""
        counts = tuple(int(count.rstrip("首")) for _, count, _ in promo.CATEGORIES)
        self.assertEqual(counts, VERIFIED_CATEGORIES)
        self.assertEqual(promo.TOTAL_TRACKS, VERIFIED_TOTAL)

    def test_total_is_derived_from_categories(self):
        expected = sum(int(count.rstrip("首")) for _, count, _ in promo.CATEGORIES)
        self.assertEqual(promo.TOTAL_TRACKS, expected)
        self.assertEqual(promo.TOTAL_LABEL, f"{expected}首")
        self.assertEqual(promo.CATEGORY_COUNT, f"{len(promo.CATEGORIES)}大分类")

    def test_no_hardcoded_track_counts_in_source(self):
        """所有"数字+首"都必须由 CATEGORIES 推导，避免图上出现过期数字。"""
        offenders = [
            line.strip()
            for line in _source_outside_category_table().splitlines()
            if HARDCODED_COUNT.search(line)
        ]
        self.assertEqual(offenders, [])

    def test_cover_cards_fit_above_summary_text(self):
        columns = 3
        cards = len(promo.CATEGORIES)
        rows = -(-cards // columns)
        last_row_bottom = promo.CARD_TOP + (rows - 1) * (promo.CARD_H + promo.CARD_GAP) + promo.CARD_H
        self.assertLess(last_row_bottom, promo.SUMMARY_TOP)

    def test_cover_grid_width_fits_board(self):
        columns = 3
        total = promo.CARD_W * columns + promo.CARD_GAP * (columns - 1)
        self.assertLessEqual(total, promo.W - promo.BORDER * 2)

    def test_short_names_cover_every_category(self):
        for name, _, _ in promo.CATEGORIES:
            self.assertIn(name, promo.SHORT_NAMES)
        self.assertEqual(len(promo.SUMMARY_LINE.split("·")), len(promo.CATEGORIES))

    def test_outcomes_layout_keeps_cards_tall_enough_and_above_the_band(self):
        """03 页卡片不能被压扁，也不能和"适合"横条重叠。

        早先卡片高度写死、横条写死在中下部，两者之间空出约 250px 死区；
        改用 stack_layout 时曾误取 sizes[1]（横条高度）当卡片高度，卡片被
        压成 29px 全部叠在一起。这里直接校验几何，渲染前就能发现。
        """
        count = 4
        grid_y, suit_y, card_h = promo.outcomes_layout(count)
        self.assertGreaterEqual(card_h, promo.OUTCOME_CARD_H)
        rows = -(-count // 2)
        grid_bottom = grid_y + rows * card_h + (rows - 1) * promo.OUTCOME_GAP
        self.assertLess(grid_bottom, suit_y, "卡片区不能压到适合横条")
        self.assertLess(
            suit_y + promo.OUTCOME_SUIT_H,
            promo.FOOTER_TOP,
            "适合横条不能压到底栏",
        )

    def test_outcomes_layout_grows_with_card_count(self):
        """卡片变多时整块往下延伸，横条跟着下移而不是压住卡片。"""
        previous_bottom = 0
        for count in (2, 4, 6):
            grid_y, suit_y, card_h = promo.outcomes_layout(count)
            rows = -(-count // 2)
            bottom = grid_y + rows * card_h + (rows - 1) * promo.OUTCOME_GAP
            with self.subTest(count=count):
                self.assertGreater(bottom, previous_bottom)
                self.assertLess(bottom, suit_y)
            previous_bottom = bottom

    def test_outcomes_layout_rejects_bad_count(self):
        for bad in (0, -1, True, 1.5, "4"):
            with self.subTest(count=bad):
                with self.assertRaises(ValueError):
                    promo.outcomes_layout(bad)

    def test_catalog_grid_is_derived_from_the_category_count(self):
        """02 页网格底边必须由分类数推出，放不下就报错。

        7 个分类在两列下是 4 行，底边 872，离底栏 956 还有余量，所以早先一直
        没写守卫。加到第 9 个分类时是 5 行，底边会到 1048，画到画布和底栏外面，
        而渲染仍然退出码 0。
        """
        rows, bottom = promo.catalog_grid(len(promo.CATEGORIES))
        self.assertEqual(rows, -(-len(promo.CATEGORIES) // promo.CAT_COLS))
        self.assertLessEqual(bottom, promo.FOOTER_TOP - promo.CAT_CARD_GAP)

        with self.assertRaises(ValueError):
            promo.catalog_grid(9)
        for bad in (0, -1, True, 1.5, "4"):
            with self.subTest(count=bad):
                with self.assertRaises(ValueError):
                    promo.catalog_grid(bad)

    def test_footer_two_text_lines_do_not_touch(self):
        """底栏两行必须能分开，看清是两行而不是一团。

        早先这里写死 H-BORDER-68/-47，两行只差 21px，而 24px 与 20px 的
        真实墨迹几乎占满行高，实测间距 -4px，两行是叠在一起的。
        相机脚本早先栽在同一个坑上，改成 FOOTER_TOP+12/+48 之后间距 +11px。
        """
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            promo.render_cover(out)
            bands = footer_text_bands(out / "01.png", promo)
        self.assertEqual(
            len(bands),
            2,
            f"底栏应该正好两行文字，实际 {len(bands)} 带：{bands}",
        )
        first, second = bands
        gap = second[0] - (first[0] + first[1])
        self.assertGreater(gap, 4, f"底栏两行间距只有 {gap}px，看起来会连成一片")


if __name__ == "__main__":
    unittest.main()
