"""Run a legacy rendering script with explicit environment overrides."""

from __future__ import annotations

import os
import runpy
from pathlib import Path


def run_legacy(script: str, out: Path, **env: str) -> None:
    """Execute a legacy script only when explicitly called by a CLI wrapper."""
    path = (Path(__file__).parent / "legacy" / script).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"legacy renderer not found: {path}")

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
