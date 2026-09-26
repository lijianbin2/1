"""CLI entry point for the legacy Codex 55-lesson renderer."""

from __future__ import annotations

import argparse
from pathlib import Path

from legacy_runner import run_legacy
from xianyu_common import enable_utf8_stdout, require_valid_pngs

DEFAULT_OUT = Path("D:/闲鱼/Codex职场高效办公实战，AI自动化赋能日常办公")


def main() -> int:
    enable_utf8_stdout()
    parser = argparse.ArgumentParser(description="生成 Codex 办公课程四张图文")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    run_legacy("render_codex55_legacy.py", args.out)
    require_valid_pngs(args.out, size=(1080, 1080))
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
