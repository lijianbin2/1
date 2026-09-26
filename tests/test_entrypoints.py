import importlib
import os
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

class EntrypointTests(unittest.TestCase):
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
