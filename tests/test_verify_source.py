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

    def test_scan_source_rejects_missing_directory(self):
        with self.assertRaises(NotADirectoryError):
            scan_source(Path("no-such-source-dir"))


if __name__ == "__main__":
    unittest.main()
