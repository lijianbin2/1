"""Run a legacy rendering script with explicit environment overrides."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def run_legacy(script: str, out: Path, **env: str) -> None:
    """Execute a legacy script only when explicitly called by a CLI wrapper."""
    root = Path(__file__).parent.resolve()
    path = (root / "legacy" / script).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"legacy renderer not found: {path}")

    # runpy 不会把脚本所在目录放进 sys.path，而 legacy 脚本现在会从项目根
    # 导入 xianyu_common。显式补上根目录，这样从任意工作目录调用入口都能导入。
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    keys = ("XIANYU_LEGACY_OUT", *env)
    previous = {key: os.environ.get(key) for key in keys}
    os.environ["XIANYU_LEGACY_OUT"] = str(Path(out).resolve())
    os.environ.update(env)
    try:
        runpy.run_path(str(path), run_name="__main__")
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
