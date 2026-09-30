"""``titles_reviewed.json`` 里的标题必须能真的发出去。

这份台账是 2026-09-30 审查 ``M:\\WebDAV\\夸克\\教程`` 全部 28 个目录的产物。
标题是账号被封前踩过坑的地方（"公文"、盗版词），也是 ``ydisk_publish.py``
会直接 ``raise`` 的地方（超 30 字），所以规则写进测试，改错了当场红。

词表和字数上限都从 :mod:`audit_titles` 引用，不在这里抄第二份：抄一份就
意味着加词时只改一处，跑出来的"全绿"是假的。

不联网、不碰 M 盘：``dir`` 与磁盘目录名的一致性单独放在会跳过的测试里，
默认跑的部分只依赖仓库内数据。
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from audit_titles import (
    BANNED_ABSOLUTE,
    BANNED_CONFIRMED,
    BANNED_EARN,
    BANNED_GOV,
    BANNED_INFRINGEMENT,
    BANNED_PIRACY,
    BANNED_PROMISE,
    DATA_PATH,
    DOC_PATH,
    SUFFIX_RE,
    TUTORIAL_DIR,
    load,
    titles_of,
    validate,
    validate_currency,
)
from make_desc import MARKER

ROOT = Path(__file__).resolve().parent.parent
DATA = load()
ITEMS = DATA["items"]

# 与 ydisk_publish.py 里那条限制保持一致。
TITLE_MAX = DATA["_max_title_len"]


class ReviewedTitlesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.titles = dict(titles_of(DATA))

    def _assert_clean(self, group: str, words: tuple[str, ...]) -> None:
        bad = [
            f"[{group}] {word} 出现在标题：{title}"
            for title in self.titles.values()
            for word in words
            if word in title
        ]
        self.assertEqual([], bad)

    def test_no_confirmed_banned_words(self) -> None:
        self._assert_clean("确认违规", BANNED_CONFIRMED)

    def test_no_government_words(self) -> None:
        self._assert_clean("政务关联", BANNED_GOV)

    def test_no_piracy_words(self) -> None:
        self._assert_clean("盗版", BANNED_PIRACY)

    def test_no_infringement_words(self) -> None:
        self._assert_clean("侵权", BANNED_INFRINGEMENT)

    def test_no_earning_promises(self) -> None:
        self._assert_clean("收益承诺", BANNED_EARN)

    def test_no_absolute_wording(self) -> None:
        self._assert_clean("绝对化", BANNED_ABSOLUTE)

    def test_no_promise_wording(self) -> None:
        self._assert_clean("效果承诺", BANNED_PROMISE)

    def test_within_publish_limit(self) -> None:
        """超 30 字时 ydisk_publish.py 会直接 raise，不是截断。"""
        for title in self.titles.values():
            with self.subTest(title=title):
                self.assertLessEqual(len(title), TITLE_MAX, f"超 {TITLE_MAX} 字：{title}")
                self.assertTrue(title.endswith(MARKER), f"缺标记：{title}")

    def test_no_format_or_batch_suffix(self) -> None:
        for title in self.titles.values():
            with self.subTest(title=title):
                self.assertIsNone(SUFFIX_RE.search(title), f"含后缀：{title}")

    def test_no_currency_in_title(self) -> None:
        """正文禁价格，标题同理——平台上单独填价格栏。"""
        self.assertEqual(
            [],
            [t for t in self.titles.values() if validate_currency(t)],
        )

    def test_counts_are_measured(self) -> None:
        """标题里的数量必须来自实测，不能抄目录名。"""
        for it in ITEMS:
            with self.subTest(dir=it["dir"]):
                self.assertIn("measured", it, "缺少实测数据")
                for key in ("files", "videos", "subdirs", "size"):
                    self.assertIn(key, it["measured"])

    def test_every_item_has_provenance(self) -> None:
        """每条都要能追回线上 item_id 或注明是新增，方便对账。"""
        for it in ITEMS:
            with self.subTest(dir=it["dir"]):
                self.assertTrue(
                    it.get("online_item_id") or it.get("note"),
                    "既没有 online_item_id 也没有 note，无法追溯",
                )

    def test_no_duplicate_titles(self) -> None:
        seen: dict[str, str] = {}
        for dir_name, title in self.titles.items():
            with self.subTest(title=title):
                self.assertNotIn(title, seen, f"与 {seen.get(title)} 撞标题")
                seen[title] = dir_name

    def test_doc_table_matches_data(self) -> None:
        """TITLES.md 由 ``audit_titles.py doc`` 生成，这里防止有人手改文档。"""
        doc = DOC_PATH.read_text(encoding="utf-8")
        for title in self.titles.values():
            with self.subTest(title=title):
                self.assertIn(title, doc, f"TITLES.md 缺少标题：{title}")

    def test_audit_tool_agrees_with_this_file(self) -> None:
        """测试里的规则和工具里的规则必须是同一份。"""
        self.assertEqual([], validate(DATA))


class TitlesMatchDiskTest(unittest.TestCase):
    """台账的 ``dir`` 必须和 M 盘目录名逐字相等。

    M 盘是 WebDAV 挂载，机器上不一定存在，所以不存在就跳过；
    改了目录名或增删资源时手动跑一次最省事。
    """

    def setUp(self) -> None:
        if not TUTORIAL_DIR.is_dir():
            self.skipTest(f"{TUTORIAL_DIR} 不存在，跳过与磁盘的一致性检查")

    def test_dirs_match_one_to_one(self) -> None:
        on_disk = {p.name for p in TUTORIAL_DIR.iterdir() if p.is_dir()}
        in_data = {it["dir"] for it in ITEMS}
        self.assertEqual(in_data, on_disk, f"多={in_data - on_disk} 少={on_disk - in_data}")


if __name__ == "__main__":
    unittest.main()
