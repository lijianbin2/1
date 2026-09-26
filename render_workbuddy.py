"""CLI entry point for the legacy WorkBuddy renderer."""

from __future__ import annotations

import argparse
from pathlib import Path

from legacy_runner import run_legacy

DEFAULT_OUT = Path("D:/闲鱼/WorkBuddy智能体实战，打造个人AI效率系统")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 WorkBuddy 课程四张图文")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    run_legacy("render_workbuddy_legacy.py", args.out)
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
