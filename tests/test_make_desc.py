import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from make_desc import (
    build_quark,
    build_title,
    check_copy,
    check_public_copy,
    copy_to_clipboard,
    main,
    write_public_copy,
    write_project,
)


class MakeDescTests(unittest.TestCase):
    def test_check_copy_rejects_currency_and_accepts_valid_copy(self):
        quark = build_quark("示例项目", "https://pan.quark.cn/s/abc123", "abcd")
        body = "只发夸克网盘\n" + quark
        self.assertEqual(check_copy("示例项目 10集 只发夸克", body), [])
        self.assertIn("currency-in-title", check_copy("示例项目 10元", body))

    def test_write_project_keeps_public_copy_separate_from_delivery_details(self):
        quark = build_quark("示例项目", "https://pan.quark.cn/s/abc123", "abcd")
        body = "只发夸克网盘"
        with tempfile.TemporaryDirectory() as directory:
            result = write_project(directory, "示例项目 10集 只发夸克", body, quark)
            self.assertEqual(result, [])
            full = (Path(directory) / "desc.txt").read_text(encoding="utf-8")
            public = (Path(directory) / "闲鱼发布文案_直接复制.txt").read_text(encoding="utf-8")
            self.assertIn("提取码：abcd", full)
            self.assertIn("示例项目 10集 只发夸克", public)
            self.assertNotIn("提取码：", public)
            self.assertNotIn("https://pan.quark.cn", public)
            self.assertNotIn("分享ID", public)

    def test_check_public_copy_rejects_share_details(self):
        title = "示例项目 10集 只发夸克"
        body = "只发夸克网盘，拍后提供链接 https://pan.quark.cn/s/abc123 提取码：abcd"
        violations = check_public_copy(title, body)
        self.assertIn("url-in-body", violations)
        self.assertIn("delivery-field-in-body", violations)

    def test_build_title_rejects_empty_values(self):
        with self.assertRaises(ValueError):
            build_title("", "10集")

    def test_build_quark_rejects_invalid_code(self):
        with self.assertRaises(ValueError):
            build_quark("示例项目", "https://pan.quark.cn/s/abc123", "123")

    def test_write_project_rejects_empty_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            result = write_project(directory, "", "正文", "分享块")
            self.assertEqual(result, ["empty-field"])
            self.assertFalse((Path(directory) / "desc.txt").exists())
            self.assertFalse((Path(directory) / "闲鱼发布文案_直接复制.txt").exists())

    def test_write_public_copy_works_before_share_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            result = write_public_copy(directory, "示例项目 10集 只发夸克", "只发夸克网盘")
            self.assertEqual(result, [])
            copy = Path(directory) / "闲鱼发布文案_直接复制.txt"
            self.assertIn("示例项目 10集 只发夸克", copy.read_text(encoding="utf-8"))
            self.assertFalse((Path(directory) / "desc.txt").exists())

    def test_write_public_copy_rejects_share_details(self):
        with tempfile.TemporaryDirectory() as directory:
            result = write_public_copy(
                directory, "示例项目 只发夸克", "链接 https://pan.quark.cn/s/abc123 提取码：abcd"
            )
            self.assertIn("url-in-body", result)
            self.assertFalse((Path(directory) / "闲鱼发布文案_直接复制.txt").exists())

    def test_copy_to_clipboard_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            copy_to_clipboard("   ")

    def test_cli_writes_public_copy_without_share_details(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = [
                "make_desc.py",
                "--out", directory,
                "--core", "示例项目",
                "--count", "10集",
                "--intro", "一句话介绍",
                "--module", "内容一",
                "--module", "内容二",
                "--audience", "摄影新手",
            ]
            with patch("sys.argv", argv):
                self.assertEqual(main(), 0)
            public = (Path(directory) / "闲鱼发布文案_直接复制.txt").read_text(encoding="utf-8")
            self.assertIn("示例项目 10集 只发夸克", public)
            self.assertNotIn("提取码", public)
            self.assertFalse((Path(directory) / "desc.txt").exists())

    def test_cli_writes_full_package_and_copies_share_block(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = [
                "make_desc.py",
                "--out", directory,
                "--core", "示例项目",
                "--count", "10集",
                "--intro", "一句话介绍",
                "--module", "内容一",
                "--audience", "摄影新手",
                "--folder", "示例项目",
                "--link", "https://pan.quark.cn/s/abc123",
                "--code", "abcd",
                "--copy",
            ]
            with patch("make_desc.copy_to_clipboard", return_value=True) as copier:
                with patch("sys.argv", argv):
                    self.assertEqual(main(), 0)
            copied = copier.call_args[0][0]
            self.assertIn("提取码：abcd", copied)
            self.assertEqual(copied.count("\n"), 2)
            self.assertTrue((Path(directory) / "desc.txt").exists())

    def test_cli_requires_all_share_fields_together(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = [
                "make_desc.py",
                "--out", directory,
                "--core", "示例项目",
                "--count", "10集",
                "--intro", "一句话介绍",
                "--module", "内容一",
                "--audience", "摄影新手",
                "--link", "https://pan.quark.cn/s/abc123",
            ]
            with patch("sys.argv", argv):
                with self.assertRaises(SystemExit):
                    main()


if __name__ == "__main__":
    unittest.main()
