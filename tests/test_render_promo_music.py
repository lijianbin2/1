import re
import unittest
from pathlib import Path

import render_promo_music as promo


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


if __name__ == "__main__":
    unittest.main()
