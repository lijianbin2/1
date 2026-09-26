import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from legacy_runner import run_legacy


CLI_ENTRYPOINTS = (
    "cover_v2",
    "render_camera_basics",
    "render_codex55",
    "render_map_collection",
    "render_promo_music",
    "render_winrar_unified",
    "render_workbuddy",
)

LIBRARY_MODULES = (
    "make_desc",
    "verify_source",
    "xianyu_common",
)

# 根目录下不是出图入口的模块：文案生成、素材核验、几何工具和扫描器本身。
# 判定方向是"除了这些，其余根目录模块都必须是入口"——新增出图脚本忘了登记，
# 就会在这里失败，而不是安静地绕过产物校验和死区扫描。
TOOLING_MODULES = frozenset(
    {
        "legacy_runner",
        "make_desc",
        "scan_zones",
        "verify_source",
        "xianyu_common",
    }
)


def _root_entrypoints() -> set[str]:
    root = Path(__file__).resolve().parent.parent
    return {
        path.stem
        for path in root.glob("*.py")
        if not path.name.startswith(".")
    } - TOOLING_MODULES


class EntrypointTests(unittest.TestCase):
    def test_every_root_module_is_a_registered_entrypoint(self):
        """根目录里每个出图脚本都必须登记在 CLI_ENTRYPOINTS 里。

        这份清单早先是手写的，新增脚本漏登记时没有任何东西会拦：实测放一个
        什么都不校验的 render_zzz_probe.py 进根目录，产物校验测试和死区扫描
        测试全绿。少一次 require_valid_pngs、少一轮版式扫描，都是事后才看得出来。
        """
        self.assertEqual(_root_entrypoints(), set(CLI_ENTRYPOINTS))

    def test_every_entrypoint_is_covered_by_the_zone_scanner(self):
        """每个入口都要么参与死区扫描，要么在 SKIPPED 里写明跳过原因。

        两份清单都手写：加了一个新入口却只登记进 CLI_ENTRYPOINTS，它就既不会被
        扫描，也不会有人注意到它被漏掉了。
        """
        from scan_zones import ENTRYPOINTS, SKIPPED

        scanned = {name.removesuffix(".py") for name in ENTRYPOINTS}
        skipped = {name.removesuffix(".py") for name in SKIPPED}
        self.assertEqual(
            scanned | skipped,
            set(CLI_ENTRYPOINTS),
            "入口未被死区扫描覆盖，也没有写明跳过原因",
        )
        self.assertEqual(
            scanned & skipped, set(), "同一个入口不能既扫描又跳过"
        )

    def test_importing_entrypoints_has_no_output_side_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"XIANYU_LEGACY_OUT": directory}):
                for name in CLI_ENTRYPOINTS + LIBRARY_MODULES:
                    with self.subTest(name=name):
                        importlib.import_module(name)
                for name in CLI_ENTRYPOINTS:
                    with self.subTest(name=name):
                        module = importlib.import_module(name)
                        self.assertTrue(callable(getattr(module, "main", None)))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_legacy_runner_restores_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            with patch.dict(
                os.environ,
                {"XIANYU_LEGACY_OUT": "original", "XIANYU_LEGACY_VERSION": "old"},
            ):
                with self.assertRaises(FileNotFoundError):
                    run_legacy("missing.py", out, XIANYU_LEGACY_VERSION="new")
                self.assertEqual(os.environ["XIANYU_LEGACY_OUT"], "original")
                self.assertEqual(os.environ["XIANYU_LEGACY_VERSION"], "old")

    def test_legacy_entrypoints_fail_when_images_are_missing(self):
        """渲染没产出图片时入口必须报错，不能照常打印 generated。"""
        for name in ("cover_v2", "render_codex55", "render_winrar_unified", "render_workbuddy"):
            with self.subTest(name=name):
                module = importlib.import_module(name)
                with tempfile.TemporaryDirectory() as directory:
                    out = Path(directory) / "out"
                    with patch.object(module, "run_legacy"), patch(
                        "sys.argv",
                        [name, "--out", str(out)],
                    ):
                        with self.assertRaises(RuntimeError) as caught:
                            module.main()
                    self.assertIn("校验失败", str(caught.exception))

    def test_all_entrypoints_validate_their_output(self):
        """七个入口都要走强制校验，否则"生成成功"不等于"产物可用"。"""
        for name in CLI_ENTRYPOINTS:
            with self.subTest(name=name):
                source = Path(importlib.import_module(name).__file__).read_text(encoding="utf-8")
                self.assertIn("require_valid_pngs", source)

    def test_legacy_can_import_common_from_any_working_directory(self):
        """legacy 脚本会从项目根导入 xianyu_common，不能依赖调用方的 cwd。"""
        project_root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            with patch.dict(os.environ, {"XIANYU_LEGACY_OUT": str(out)}):
                cwd = os.getcwd()
                try:
                    os.chdir(directory)
                    run_legacy("render_codex55_legacy.py", out)
                finally:
                    os.chdir(cwd)
            self.assertTrue((out / "01.png").is_file())
            self.assertIn(str(project_root), sys.path)
