import tempfile
import unittest
from pathlib import Path

from verify_source import check_claims, format_report, scan_source


class VerifySourceTests(unittest.TestCase):
    def _make_source(self, root: Path, counts: dict[str, int]) -> None:
        for name, count in counts.items():
            folder = root / name
            folder.mkdir(parents=True, exist_ok=True)
            for index in range(count):
                (folder / f"track{index:03d}.mp3").write_bytes(b"0" * 1024)

    def test_scan_source_counts_files_and_detects_declared_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-5首": 4})
            stats = scan_source(root)
            self.assertEqual(stats.total_files, 7)
            self.assertEqual(stats.extensions, {".mp3": 7})
            self.assertEqual([f.declared for f in stats.folders], [3, 5])
            self.assertEqual([f.name for f in stats.declared_mismatches], ["02、校园-5首"])
            report = format_report(stats)
            self.assertIn("文件总数：7", report)
            self.assertIn("不一致", report)

    def test_check_claims_accepts_matching_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            copy = (
                "示例 7首 只发夸克\n\n"
                "本套共7首背景音乐。\n\n"
                "内容简介：\n"
                "1. 汽车宣传片背景音乐：3首\n"
                "2. 校园宣传片背景音乐：4首\n"
            )
            self.assertEqual(check_claims(copy, stats), [])

    def test_check_claims_reports_each_kind_of_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            copy = (
                "示例 99首 只发夸克\n\n"
                "本套共99首背景音乐，约0.01GB。\n\n"
                "内容简介：\n"
                "1. 汽车宣传片背景音乐：3首\n"
                "2. 校园宣传片背景音乐：4首\n"
            )
            codes = check_claims(copy, stats)
            self.assertTrue(any(c.startswith("title-count-mismatch") for c in codes))
            self.assertTrue(any(c.startswith("sum-claim-mismatch") for c in codes))
            self.assertTrue(any(c.startswith("total-size-mismatch") for c in codes))

    def test_check_claims_detects_item_sum_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            copy = (
                "示例 7首 只发夸克\n\n"
                "本套共7首背景音乐。\n\n"
                "内容简介：\n"
                "1. 汽车宣传片背景音乐：3首\n"
                "2. 校园宣传片背景音乐：9首\n"
            )
            self.assertTrue(
                any(c.startswith("item-sum-mismatch") for c in check_claims(copy, stats))
            )

    def test_single_listed_line_wrong_count_is_caught(self):
        """整份文案只有一条明细时，错数也必须报出来。

        明细行会被排除在正文检查之外，唯一的数量声明落在明细里时，正文和
        标题两道检查都够不着它。早先的累加校验还要求明细多于一条，于是
        "1. 900张"（素材实际 7 个文件）返回空违规列表，是校验器最该拦下的
        那种错数却完全放行。
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            wrong = "示例 素材合集\n\n内容简介：\n1. 全部素材：900首\n"
            self.assertTrue(
                any(c.startswith("item-sum-mismatch") for c in check_claims(wrong, stats)),
                msg=f"单条明细错数未被拦截：{check_claims(wrong, stats)}",
            )
            right = "示例 素材合集\n\n内容简介：\n1. 全部素材：7首\n"
            self.assertEqual(check_claims(right, stats), [])

    def test_listed_line_without_any_count_is_not_flagged(self):
        """明细里没有数量声明时不能凭空报违规。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            copy = "示例 素材合集\n\n内容简介：\n1. 中国地图、世界地图、各省区域图\n"
            self.assertEqual(check_claims(copy, stats), [])

    def test_scan_source_rejects_missing_directory(self):
        with self.assertRaises(NotADirectoryError):
            scan_source(Path("no-such-source-dir"))

    def test_loose_files_at_source_root_are_not_top_level_categories(self):
        """课程合集常常一个 mp4 一节课、没有分类文件夹。

        这些散文件如果也算"一级分类"，报告里会每个文件多出一行；更要命的是
        文件名里带"-5首"这种标注时会被 _declared_count 读成目录名声明，凭空
        判出一处不一致，让核验以退出码 1 失败——而素材其实完全正常。
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "001、基础入门.mp4").write_bytes(b"0")
            (root / "002、进阶技巧.mp4").write_bytes(b"0")
            stats = scan_source(root)
            self.assertEqual(stats.total_files, 2)
            self.assertEqual(stats.extensions, {".mp4": 2})
            self.assertEqual(stats.folders, [])
            self.assertEqual(stats.declared_mismatches, [])

    def test_loose_file_named_like_a_counted_folder_does_not_fail_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "素材包-5张").write_bytes(b"0")
            stats = scan_source(root)
            self.assertEqual(stats.declared_mismatches, [])
            self.assertNotIn("不一致", format_report(stats))

    def test_root_level_files_still_count_toward_subfolder_totals(self):
        """散文件不参与分类，但总数和体积必须照算，不能被顺手漏掉。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3})
            (root / "封面.jpg").write_bytes(b"0" * 2048)
            stats = scan_source(root)
            self.assertEqual(stats.total_files, 4)
            self.assertEqual([f.files for f in stats.folders], [3])
            self.assertEqual(stats.extensions, {".mp3": 3, ".jpg": 1})

    def test_check_claims_catches_every_project_count_unit(self):
        """目录名和正文用同一套单位，漏一个单位就等于少测一种错数。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            for unit in ("首", "张", "套", "集", "期"):
                with self.subTest(unit=unit):
                    codes = check_claims(f"示例 468{unit} 素材合集\n", stats)
                    self.assertTrue(
                        any(c.startswith("title-count-mismatch") for c in codes),
                        msg=f"{unit} 未被拦截：{codes}",
                    )

    def test_check_claims_generalizes_sum_claim_to_all_units(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            for unit in ("首", "张", "套", "集", "期"):
                with self.subTest(unit=unit):
                    codes = check_claims(f"示例 素材合集\n\n本套共468{unit}，含多类。\n", stats)
                    self.assertTrue(
                        any(c.startswith("sum-claim-mismatch") for c in codes),
                        msg=f"共N{unit} 未被拦截：{codes}",
                    )

    def test_check_claims_ignores_bare_ge_counted_in_chapters(self):
        """“个”排除在外：章节数不是文件数，拿去比对必然误报。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            copy = "示例 摄影教程\n\n共41个视频，分为12个章节。\n"
            self.assertEqual(check_claims(copy, stats), [])

    def test_unnumbered_detail_lines_are_not_compared_against_the_total(self):
        """明细不写"1. "编号时，分类数量不能拿去和总数比。

        实测宣传片音乐那份文案：``内容简介：`` 下面直接是七行
        "汽车宣传片 37首"…"大气企业宣传片 487首"，一条编号都没有。早先只按
        编号前缀认明细，这七行全落进正文检查，每个分类数量都被拿去和 970 首
        的总数比一遍，报出七条 body-count-mismatch——数量全对，发布却被
        校验器挡下来。
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            copy = (
                "示例 7首 只发夸克\n\n"
                "本套共7首背景音乐。\n\n"
                "内容简介：\n"
                "汽车宣传片 3首\n"
                "校园宣传片 4首\n\n"
                "适合剪辑新手。\n"
            )
            self.assertEqual(check_claims(copy, stats), [])

    def test_unnumbered_detail_wrong_count_is_still_caught(self):
        """按结构认出明细之后，错数依然要能拦住（合计不等于总数）。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            copy = (
                "示例 7首 只发夸克\n\n"
                "本套共7首背景音乐。\n\n"
                "内容简介：\n"
                "汽车宣传片 3首\n"
                "校园宣传片 9首\n\n"
                "适合剪辑新手。\n"
            )
            self.assertTrue(
                any(c.startswith("item-sum-mismatch") for c in check_claims(copy, stats)),
                msg=f"不编号明细的错数未被拦截：{check_claims(copy, stats)}",
            )

    def test_detail_block_is_scoped_to_its_own_heading(self):
        """内容简介块外的行仍按正文校验，不能被明细规则一起吞掉。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_source(root, {"01、汽车-3首": 3, "02、校园-4首": 4})
            stats = scan_source(root)
            copy = (
                "示例 7首 只发夸克\n\n"
                "另外还有99首加赠。\n\n"
                "内容简介：\n"
                "汽车宣传片 3首\n"
                "校园宣传片 4首\n"
            )
            self.assertTrue(
                any(c.startswith("body-count-mismatch") for c in check_claims(copy, stats)),
                msg=f"明细块外的错数未被拦截：{check_claims(copy, stats)}",
            )


if __name__ == "__main__":
    unittest.main()
