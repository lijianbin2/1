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
