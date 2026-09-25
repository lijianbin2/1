import tempfile
import unittest
from pathlib import Path

from make_desc import build_quark, check_copy, write_project


class MakeDescTests(unittest.TestCase):
    def test_check_copy_rejects_currency_and_accepts_valid_copy(self):
        quark = build_quark("示例项目", "https://pan.quark.cn/s/abc123", "abcd")
        body = "只发夸克网盘\n" + quark
        self.assertEqual(check_copy("示例项目 10集 只发夸克", body), [])
        self.assertIn("currency-in-title", check_copy("示例项目 10元", body))

    def test_write_project_writes_matching_utf8_files(self):
        quark = build_quark("示例项目", "https://pan.quark.cn/s/abc123", "abcd")
        body = "只发夸克网盘\n" + quark
        with tempfile.TemporaryDirectory() as directory:
            result = write_project(directory, "示例项目 10集 只发夸克", body, quark)
            self.assertEqual(result, [])
            first = (Path(directory) / "desc.txt").read_bytes()
            second = (Path(directory) / "闲鱼发布文案_直接复制.txt").read_bytes()
            self.assertEqual(first, second)
            self.assertIn("提取码：abcd", first.decode("utf-8"))

    def test_write_project_rejects_empty_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            result = write_project(directory, "", "正文", "分享块")
            self.assertEqual(result, ["empty-field"])
            self.assertFalse((Path(directory) / "desc.txt").exists())
            self.assertFalse((Path(directory) / "闲鱼发布文案_直接复制.txt").exists())


if __name__ == "__main__":
    unittest.main()
