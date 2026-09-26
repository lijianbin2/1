import re
import unittest
from pathlib import Path

LEGACY = Path(__file__).resolve().parent.parent / "legacy"

DECLARATIONS = ("LESSONS =", "MODULES =", "PACKAGE_MB =", "LESSON_", "SIZE_")
LESSON_COUNT = re.compile(r"(\d+)\s*(?:集|课时|节)")
VIDEO_COUNT = re.compile(r"(\d+)\s*个\S*视频")
PACKAGE_SIZE = re.compile(r"(\d+(?:\.\d+)?)\s*MB")

LESSON_FILES = (
    "cover_v2_legacy.py",
    "render_codex55_legacy.py",
    "render_workbuddy_legacy.py",
)
SIZE_FILES = ("render_winrar_unified_legacy.py",)


def _offenders(name: str, pattern) -> list:
    """返回除常量声明行外仍写死数量的源码行。"""
    source = (LEGACY / name).read_text(encoding="utf-8")
    return [
        line.strip()
        for line in source.splitlines()
        if not any(marker in line for marker in DECLARATIONS)
        and not line.lstrip().startswith("#")
        and pattern.search(line)
    ]


class LegacyConstantTests(unittest.TestCase):
    def test_lesson_counts_only_declared_once(self):
        for name in LESSON_FILES:
            with self.subTest(name=name):
                self.assertEqual(_offenders(name, LESSON_COUNT), [])

    def test_video_counts_only_declared_once(self):
        """"N个实战视频"也是数量声明，不能绕过 LESSONS 写死。"""
        for name in LESSON_FILES:
            with self.subTest(name=name):
                self.assertEqual(_offenders(name, VIDEO_COUNT), [])

    def test_package_size_only_declared_once(self):
        for name in SIZE_FILES:
            with self.subTest(name=name):
                self.assertEqual(_offenders(name, PACKAGE_SIZE), [])

    def test_counts_are_overridable_by_environment(self):
        """数量必须能从环境变量覆盖，换课不用改代码。"""
        pairs = (
            ("render_workbuddy_legacy.py", "XIANYU_WORKBUDDY_LESSONS"),
            ("render_codex55_legacy.py", "XIANYU_CODEX_LESSONS"),
            ("render_winrar_unified_legacy.py", "XIANYU_WINRAR_MB"),
        )
        for name, variable in pairs:
            with self.subTest(name=name):
                self.assertIn(variable, (LEGACY / name).read_text(encoding="utf-8"))

    def test_workbuddy_count_matches_real_source(self):
        """37 集必须与源目录实测的 37 个视频一致。"""
        source = (LEGACY / "render_workbuddy_legacy.py").read_text(encoding="utf-8")
        match = re.search(r'XIANYU_WORKBUDDY_LESSONS",\s*"(\d+)"', source)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), 37)

    def test_codex_module_ranges_chain_to_lesson_count(self):
        """模块区间必须从 1 首尾相接排到 LESSONS，不能停在写死的旧数字。"""
        for name, variable in (
            ("render_codex55_legacy.py", "XIANYU_CODEX_LESSONS"),
            ("render_workbuddy_legacy.py", "XIANYU_WORKBUDDY_LESSONS"),
        ):
            with self.subTest(name=name):
                self._assert_ranges_chain(name, variable)

    def _assert_ranges_chain(self, name: str, variable: str) -> None:
        source = (LEGACY / name).read_text(encoding="utf-8")
        lessons = int(re.search(variable + r'",\s*"(\d+)"', source).group(1))
        # 末个模块写成 f"42-{LESSONS}"，结束值要从常量解析而不是当字面量
        ranges = [
            (int(start), lessons if end == "{LESSONS}" else int(end))
            for start, end in re.findall(r"""['"](\d+)-(\d+|\{LESSONS\})['"]""", source)
        ]
        self.assertTrue(ranges, "应能从 modules 里解析出课时区间")
        self.assertEqual(ranges[0][0], 1, "课程目录必须从第 1 课时开始")
        for (_, prev_end), (next_start, _) in zip(ranges, ranges[1:]):
            self.assertEqual(
                next_start,
                prev_end + 1,
                f"{name} 课时区间不连续：{prev_end} 之后应是 {prev_end + 1}，实际 {next_start}",
            )
        self.assertEqual(
            ranges[-1][1],
            lessons,
            f"{name} 目录止于 {ranges[-1][1]}，与声明的 {lessons} 课时不符",
        )

    def test_step_counts_are_derived_from_lists(self):
        """"N步"必须来自 len(points)，否则增删条目后副标题与实际不符。"""
        for name in ("render_codex55_legacy.py", "render_workbuddy_legacy.py"):
            with self.subTest(name=name):
                source = (LEGACY / name).read_text(encoding="utf-8")
                self.assertIn("步", source, f"{name} 应有步骤数文案")
                self.assertIn(
                    "len(points)}步",
                    source,
                    f"{name} 的步数应写成 len(points)}}步",
                )
                for literal in re.findall(r"[一-鿿，](\d+)步", source):
                    self.assertNotIn(
                        f"，{literal}步",
                        source,
                        f"{name} 的 {literal}步 是手打的，应改用 len(points)",
                    )


if __name__ == "__main__":
    unittest.main()
