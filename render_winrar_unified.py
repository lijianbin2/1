"""CLI entry point for the legacy WinRAR renderer."""

from __future__ import annotations

import argparse
from pathlib import Path

from legacy_runner import run_legacy
from xianyu_common import enable_utf8_stdout, require_valid_pngs


def main() -> int:
    enable_utf8_stdout()
    parser = argparse.ArgumentParser(description="生成 WinRAR 解压缩工具四张图文")
    parser.add_argument("--version", default="v7.23", help="空字符串隐藏版本号")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("D:/闲鱼/WinRAR v7.23解压缩工具"),
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    run_legacy(
        "render_winrar_unified_legacy.py",
        args.out,
        XIANYU_LEGACY_VERSION=args.version,
    )
    require_valid_pngs(args.out, size=(1080, 1080))
    print(f"generated {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
