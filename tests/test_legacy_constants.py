import re
import unittest
from pathlib import Path

LEGACY = Path(__file__).resolve().parent.parent / "legacy"

DECLARATIONS = ("LESSONS =", "MODULES =", "PACKAGE_MB =", "LESSON_", "SIZE_")
LESSON_COUNT = re.compile(r"(\d+)\s*(?:集|课时|节)")
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


if __name__ == "__main__":
    unittest.main()
