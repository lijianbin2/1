"""CLI entry point for the legacy two-cover renderer."""

from __future__ import annotations

import argparse
from pathlib import Path

from legacy_runner import run_legacy
from xianyu_common import enable_utf8_stdout, require_valid_pngs

DEFAULT_OUT = Path("D:/闲鱼/WorkBuddy智能体实战，打造个人AI效率系统")


def main() -> int:
    enable_utf8_stdout()
    parser = argparse.ArgumentParser(description="生成 WorkBuddy 两版封面")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    run_legacy("cover_v2_legacy.py", args.out)
    require_valid_pngs(
        args.out,
        size=(1080, 1080),
        names=("cover_A.png", "cover_B.png"),
        label="封面",
    )
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
