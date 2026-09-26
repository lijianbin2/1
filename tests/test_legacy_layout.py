"""legacy 脚本的版式回归测试。

这些脚本是手写坐标绘制，最容易出的问题是区块互相压字。这里不重跑渲染，
而是直接量坐标和真实墨迹间距，把踩过的坑固定成断言。
"""

import re
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from xianyu_common import get_font, text_extent

LEGACY = Path(__file__).resolve().parent.parent / "legacy"

# 底栏双行文字的三个 legacy 脚本：04 页都用两行"只发夸克网盘"。
FOOTER_FILES = (
    "render_codex55_legacy.py",
    "render_workbuddy_legacy.py",
    "render_winrar_unified_legacy.py",
)


def _draw() -> ImageDraw.ImageDraw:
    return ImageDraw.Draw(Image.new("RGB", (1080, 1080), "white"))


def _guide_section(name: str) -> str:
    """截出 04 引导页的代码段。

    02/03 页的底栏是单行，用 H-BORDER-68 没问题，所以只检查 04 页，
    否则会误伤那些仍然正确的写法。
    """
    source = (LEGACY / name).read_text(encoding="utf-8")
    start = re.search(r"^#.*04 guide.*$", source, re.IGNORECASE | re.MULTILINE)
    assert start is not None, f"{name} 缺少 04 页标记"
    end = re.search(r'^im\.save\(\s*out\s*/\s*"04\.png"', source[start.end() :], re.MULTILINE)
    assert end is not None, f"{name} 缺少 04.png 保存语句"
    section = source[start.end() : start.end() + end.start()]
    # 注释里会引用旧写法说明来由，负向检查只针对真实代码
    return "\n".join(line for line in section.splitlines() if not line.lstrip().startswith("#"))


class FooterSpacingTests(unittest.TestCase):
    def test_two_line_footer_uses_bar_top_relative_offsets(self):
        """底栏两行必须按 BAR_TOP 相对定位，不再按 H-BORDER-68/-38 硬写。

        H-BORDER-68 与 H-BORDER-38 相差 30px，而 24px 与 18px 两行文字的
        真实墨迹几乎占满各自高度，实测两行只差 3px，看起来连成一片。
        """
        for name in FOOTER_FILES:
            with self.subTest(name=name):
                guide = _guide_section(name)
                self.assertNotIn("H-BORDER-68", guide.replace(" ", ""))
                self.assertIn("BAR_TOP+12", guide.replace(" ", ""))
                self.assertIn("BAR_TOP+48", guide.replace(" ", ""))

    def test_two_line_footer_ink_does_not_touch(self):
        """按新坐标渲染，两行墨迹之间要有可见间距。"""
        draw = _draw()
        bar_top = 1080 - 38 - 86
        first = text_extent(draw, "只发夸克网盘", get_font(24, True), bar_top + 12)
        second = text_extent(draw, "不发其他盘 不发实物", get_font(18), bar_top + 48)
        self.assertGreater(
            second[0] - first[1],
            6,
            "两行墨迹几乎贴在一起，底栏会看成一团",
        )

    def test_two_line_footer_stays_inside_the_bar(self):
        """第二行也不能顶出底栏下沿。"""
        draw = _draw()
        bar_top = 1080 - 38 - 86
        _, bottom = text_extent(draw, "不发其他盘 不发实物", get_font(18), bar_top + 48)
        self.assertLessEqual(bottom, 1080 - 38)


class CodexGuideLayoutTests(unittest.TestCase):
    def test_guide_page_uses_adaptive_stacking(self):
        """04 页曾用 yy=BORDER+120 手写坐标，导致副标题压住第一张卡片。"""
        source = (LEGACY / "render_codex55_legacy.py").read_text(encoding="utf-8")
        self.assertIn("stack_layout", source)
        self.assertNotRegex(source, r"yy\s*=\s*BORDER\+120")

    def test_warning_box_is_tall_enough_for_its_text(self):
        """提醒框早先只有 70px 高，却按 86px 布局，标题和正文叠字。"""
        source = (LEGACY / "render_codex55_legacy.py").read_text(encoding="utf-8")
        match = re.search(r"^WARN_H=(\d+)", source, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(int(match.group(1)), 86)

    def test_step_arrow_stays_inside_the_card(self):
        """箭头早先画在 W-BORDER-60，溢出到卡片右缘外面。"""
        source = (LEGACY / "render_codex55_legacy.py").read_text(encoding="utf-8")
        arrow = re.search(r'draw\.text\(\((W-BORDER[^,]+),\s*yy\+\d+\),\s*"→"', source)
        self.assertIsNotNone(arrow, "应使用卡片内侧的箭头坐标")
        self.assertNotIn("W-BORDER-60,", arrow.group(1))


class WinrarHeightConstantsTests(unittest.TestCase):
    """winrar 里三块高度必须各自有名，含义不同就不能共用一个常量。

    横条高、页内信息条高、04 页"提醒"框高都恰好是 86 或 60，早先都用裸
    字面量或同一个 `FOOTER` 名字。改一个不动另一个，会以为改了其实没改到。
    """

    def setUp(self):
        self.source = (LEGACY / "render_winrar_unified_legacy.py").read_text(
            encoding="utf-8"
        )

    def test_distinct_heights_have_distinct_names(self):
        # 自己拼消息，别用 assertRegex：它失败时会把整个脚本源码打进报告，
        # 几千行噪音里真正的错只有一行。
        found = {
            name: bool(re.search(rf"(?m)^{name}\s*=\s*\d+", self.source))
            for name in ("NOTE_H", "BAR_H", "WARN_H")
        }
        missing = [name for name, ok in found.items() if not ok]
        self.assertEqual(
            missing, [], f"这些常量没有各自的定义：{missing}；应写成 `NAME = 数字`"
        )

    def test_no_bare_86_left_in_code(self):
        """除常量定义处，代码里不该再有裸 86。

        86 这个数值在 winrar 里出现三次，含义各不相同。留成字面量的话，
        调横条高度会顺手把提醒框也改了，渲染出来才发现不对。
        """
        allowed = re.compile(r"^(NOTE_H|BAR_H|WARN_H)\s*=\s*\d+\s*$")
        offenders = [
            line
            for line in self.source.splitlines()
            if not line.lstrip().startswith("#")
            and re.search(r"(?<![\w.])86(?![\w.])", line)
            and not allowed.match(line.strip())
        ]
        self.assertEqual(
            offenders, [], f"这些行里还有裸 86，应改用常量：{offenders}"
        )

    def test_bar_top_is_derived_from_bar_h(self):
        collapsed = self.source.replace(" ", "")
        self.assertIn(
            "BAR_TOP=H-BORDER-BAR_H",
            collapsed.splitlines(),
            "BAR_TOP 应由 BAR_H 推导，不要退回裸字面量",
        )


class CodexCoverLayoutTests(unittest.TestCase):
    """封面特色块的版式回归。

    早先特色块的 y 和高度都是手写常量：内容在 540px 就结束，底部标语在
    920px，中间空出约 380px 死区。修法不是把卡片拉高（试过，卡片长到
    460px 而内容只有 180px，底部又空一片），而是补上实质内容再让
    stack_layout 居中。这里锁住两个几何不变量。
    """

    @staticmethod
    def _load(module_name: str):
        import importlib
        import os
        import tempfile

        tmp = tempfile.TemporaryDirectory()
        old = os.environ.get("XIANYU_LEGACY_OUT")
        os.environ["XIANYU_LEGACY_OUT"] = tmp.name
        sys.path.insert(0, str(LEGACY))
        try:
            module = importlib.import_module(module_name)
        finally:
            os.environ["XIANYU_LEGACY_OUT"] = old or ""
            sys.path.remove(str(LEGACY))
        return module, tmp

    def setUp(self):
        self.module, self._tmp = self._load("render_codex55_legacy")

    def tearDown(self):
        self._tmp.cleanup()

    def test_feature_block_sits_between_divider_and_bottom_tag(self):
        """特色卡必须落在分隔线下方、底栏上方，中间不能留大洞。"""
        top, card_h = self.module.features_layout(3)
        bottom = top + card_h
        self.assertGreaterEqual(top, 330, "特色卡不能压到标题分隔线上方")
        self.assertLessEqual(bottom, self.module.FOOTER_TOP - 20, "不能压到底栏")
        # 上下留白都要有，但都不该超过 170px，否则又变成死区
        self.assertLessEqual(top - 300, 170, "分隔线到特色卡之间空得太多")
        self.assertLessEqual(
            self.module.FOOTER_TOP - 36 - bottom, 170, "特色卡到底栏之间空得太多"
        )

    def test_card_is_tall_enough_for_its_content(self):
        """卡片高度必须容得下图标、标题、副标题和细节三行。"""
        _, card_h = self.module.features_layout(3)
        self.assertGreaterEqual(
            card_h,
            self.module.FEATURE_CONTENT_H,
            "卡片比内容还矮，卡内文字会溢出边框",
        )

    def test_features_layout_rejects_bad_count(self):
        for bad in (0, -1, True, 1.5, "3", None):
            with self.subTest(count=bad):
                with self.assertRaises(ValueError):
                    self.module.features_layout(bad)


class WorkBuddyCoverLayoutTests(CodexCoverLayoutTests):
    """workbuddy 封面和 codex55 是同一套版式，同样锁住几何不变量。"""

    def setUp(self):
        self.module, self._tmp = self._load("render_workbuddy_legacy")


if __name__ == "__main__":
    unittest.main()
