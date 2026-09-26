import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from make_desc import (
    FORBIDDEN,
    build_body,
    build_quark,
    build_title,
    check_copy,
    check_public_copy,
    copy_to_clipboard,
    main,
    write_public_copy,
    write_project,
)


class BuildBodyTests(unittest.TestCase):
    """``build_body`` 的三条约定：人群只加一次尾句、分段不许带换行、标题不重复。"""

    def test_audience_gets_prefix_and_tail_exactly_once(self):
        """裸人群补上"适合"前缀和尾句。"""
        body = build_body("示例 10集", "一句话", ["内容一"], "摄影新手")
        self.assertIn("适合摄影新手，适合有具体需求的用户。", body)

    def test_audience_sentence_is_not_repeated(self):
        """传进来的已经是一整句时，不能再补一遍同样的尾句。

        早先无条件拼接"适合有具体需求的用户"，传入
        "适合有具体需求的用户"就会得到
        "适合有具体需求的用户，适合有具体需求的用户。"，正文里出现重复子句。
        """
        body = build_body("示例 10集", "一句话", ["内容一"], "适合有具体需求的用户")
        self.assertIn("适合有具体需求的用户。", body)
        self.assertNotIn("用户，适合有具体需求的用户", body)
        self.assertEqual(body.count("有具体需求的用户"), 1)

    def test_audience_already_carrying_the_prefix_is_left_alone(self):
        body = build_body("示例 10集", "一句话", ["内容一"], "适合摄影新手")
        self.assertIn("适合摄影新手，", body)
        self.assertNotIn("适合适合", body)

    def test_newlines_in_segments_are_rejected(self):
        """三段都靠空行分段，塞进换行会打乱正文结构。

        换行还会让一行伪装成新的明细条目：``内容简介：`` 下面的换行能让
        verify_source 的 ``_LISTED_LINE`` 误判成一条独立明细。
        """
        for label, args in (
            ("intro", ("一句话\n偷塞一行", ["内容一"], "摄影新手")),
            ("module", ("一句话", ["内容一\n偷塞一行"], "摄影新手")),
            ("audience", ("一句话", ["内容一"], "摄影\n新手")),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    build_body("示例 10集", *args)

    def test_body_does_not_repeat_the_title(self):
        title = "示例 10集 只发夸克"
        body = build_body(title, "一句话", ["内容一"], "摄影新手")
        self.assertNotIn(title, body)

    def test_empty_segments_are_rejected(self):
        for args in (
            (" ", ["内容一"], "摄影新手"),
            ("一句话", [], "摄影新手"),
            ("一句话", ["内容一"], "  "),
        ):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    build_body("示例 10集", *args)


class MakeDescTests(unittest.TestCase):
    def test_forbidden_words_match_the_documented_list(self):
        """WORKFLOW.md 承诺拦住的词，代码里必须真的在拦。

        文档写了"自动发货"但 FORBIDDEN 漏了它，正文就能混过校验，
        买家在闲鱼看到实物/自动发货承诺就是货不对板。
        """
        self.assertIn("自动发货", FORBIDDEN)
        self.assertIn("百度", FORBIDDEN)
        for word in ("自动发货", "实物快递", "拍下自动发货"):
            with self.subTest(word=word):
                violations = check_public_copy(
                    "示例项目 10集 只发夸克", f"只发夸克网盘\n{word}"
                )
                # 必须是 forbidden 真的命中，不能靠别的规则顺带报错蒙混过关
                self.assertTrue(
                    any(
                        "forbidden" in code and code.endswith("-in-body")
                        for code in violations
                    ),
                    f"正文里的“{word}”没有被 forbidden 规则拦下：{violations}",
                )

    def test_forbidden_covers_physical_fulfilment_promises(self):
        """虚拟资料写"包邮""现货""秒发"同样是承诺实物发货，必须拦。"""
        for word in ("包邮", "现货", "秒发", "全国包邮", "大量现货"):
            with self.subTest(word=word):
                violations = check_public_copy(
                    "示例项目 10集 只发夸克", f"只发夸克网盘\n{word}"
                )
                self.assertTrue(
                    any(
                        "forbidden" in code and code.endswith("-in-body")
                        for code in violations
                    ),
                    f"正文里的“{word}”没有被 forbidden 规则拦下：{violations}",
                )

    def test_forbidden_still_allows_neutral_shipping_wording(self):
        """"发货指南""这类中性说法不是承诺，不能被新加的词误伤。"""
        for phrase in ("发货方式：无需邮寄", "拍后发网盘链接，无需邮寄"):
            with self.subTest(phrase=phrase):
                self.assertEqual(
                    check_public_copy(
                        "示例项目 10集 只发夸克", f"只发夸克网盘\n{phrase}"
                    ),
                    [],
                    f"中性表述“{phrase}”被误判了",
                )

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
