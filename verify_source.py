"""核验源素材统计，并检查文案中的数量、体积声明。

工作流要求"先统计再生成"，但商品图和文案里的数量过去都是手写的，
容易出现目录名、实际文件数和文案三处对不上的情况。本模块把这些数字
变成可复算的：扫描源目录得到真实统计，再逐条比对文案里的声明。
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_DECLARED_IN_NAME = re.compile(r"[-—_](\d+)\s*(?:首|个|张|套|集|期)\s*$")
_TOTAL_FILES = re.compile(r"(\d+)\s*个文件")
_SIZE = re.compile(r"(\d+(?:\.\d+)?)\s*(TB|GB|MB)", re.IGNORECASE)
_SUM_CLAIM = re.compile(r"共\s*(\d+)\s*首")
_ITEM_COUNT = re.compile(r"(\d+)\s*首")
_DETAIL_LINE = re.compile(r"^\s*\d+\s*[.、)）]\s*")
_LISTED_LINE = re.compile(r"^\s*(?:\d+\s*[.、)）]\s*)?[\d一二三四五六七八九十]+\s*[.、)）]\s*")
_SIZE_UNITS = {"TB": 1024**4, "GB": 1024**3, "MB": 1024**2}


@dataclass
class FolderStat:
    """单个一级分类目录的统计。"""

    name: str
    files: int
    declared: int | None = None


@dataclass
class SourceStats:
    """源目录的完整统计结果。"""

    root: Path
    total_files: int = 0
    total_bytes: int = 0
    folders: list[FolderStat] = field(default_factory=list)
    extensions: dict[str, int] = field(default_factory=dict)

    @property
    def size_gb(self) -> float:
        return self.total_bytes / _SIZE_UNITS["GB"]

    @property
    def declared_mismatches(self) -> list[FolderStat]:
        """目录名标注数量与实际文件数不一致的分类。"""
        return [f for f in self.folders if f.declared is not None and f.declared != f.files]


def _declared_count(name: str) -> int | None:
    match = _DECLARED_IN_NAME.search(name.strip())
    return int(match.group(1)) if match else None


def scan_source(root: str | Path) -> SourceStats:
    """递归统计源目录的文件数量、体积、扩展名和一级分类数量。"""
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(f"源素材目录不存在：{root}")

    stats = SourceStats(root=root)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        size = path.stat().st_size
        stats.total_files += 1
        stats.total_bytes += size
        ext = path.suffix.lower() or "<无扩展名>"
        stats.extensions[ext] = stats.extensions.get(ext, 0) + 1
        top = path.relative_to(root).parts[0]
        folder = next((f for f in stats.folders if f.name == top), None)
        if folder is None:
            folder = FolderStat(name=top, files=0, declared=_declared_count(top))
            stats.folders.append(folder)
        folder.files += 1

    stats.folders.sort(key=lambda f: f.name)
    return stats


def _size_tolerance(displayed: str, unit: str) -> float:
    """允许文案体积存在末位四舍五入误差。"""
    actual_unit = _SIZE_UNITS[unit.upper()]
    digits = len(displayed.rsplit(".", 1)[1]) if "." in displayed else 0
    step = 0.5 * 10 ** (-digits) * actual_unit
    return max(step, actual_unit * 0.005)


def check_claims(text: str, stats: SourceStats) -> list[str]:
    """比对文案中的数量与体积声明，返回违规代码列表。"""
    violations: list[str] = []

    for raw in _TOTAL_FILES.findall(text):
        if int(raw) != stats.total_files:
            violations.append(f"total-files-mismatch: 文案{raw} 实际{stats.total_files}")

    for displayed, unit in _SIZE.findall(text):
        claimed = float(displayed) * _SIZE_UNITS[unit.upper()]
        if abs(claimed - stats.total_bytes) > _size_tolerance(displayed, unit):
            violations.append(
                f"total-size-mismatch: 文案{displayed}{unit.upper()} 实际{stats.size_gb:.2f}GB"
            )

    for raw in _SUM_CLAIM.findall(text):
        if int(raw) != stats.total_files:
            violations.append(f"sum-claim-mismatch: 文案共{raw}首 实际{stats.total_files}")

    lines = [line for line in text.splitlines() if line.strip()]
    detail_lines = [line for line in lines if _LISTED_LINE.match(line)]
    items = [
        int(n)
        for line in detail_lines
        for n in _ITEM_COUNT.findall(_SUM_CLAIM.sub("", line))
    ]
    if len(items) > 1:
        listed = sum(items)
        if listed != stats.total_files:
            violations.append(f"item-sum-mismatch: 明细合计{listed} 实际{stats.total_files}")

    body = "\n".join(
        line for line in lines[1:] if not _LISTED_LINE.match(line)
    )
    for raw in _ITEM_COUNT.findall(_SUM_CLAIM.sub("", lines[0] if lines else "")):
        if int(raw) != stats.total_files:
            violations.append(f"title-count-mismatch: 标题{raw}首 实际{stats.total_files}")
    for raw in _ITEM_COUNT.findall(_SUM_CLAIM.sub("", body)):
        if int(raw) != stats.total_files:
            violations.append(f"body-count-mismatch: 正文{raw}首 实际{stats.total_files}")

    return violations


def format_report(stats: SourceStats) -> str:
    """生成可直接粘贴的统计摘要。"""
    lines = [
        f"源目录：{stats.root}",
        f"文件总数：{stats.total_files}",
        f"总体积：{stats.size_gb:.2f}GB",
        "",
        "一级分类：",
    ]
    for folder in stats.folders:
        declared = f"（目录名标注 {folder.declared}）" if folder.declared is not None else ""
        flag = "  <== 不一致" if folder in stats.declared_mismatches else ""
        lines.append(f"  {folder.name}: {folder.files} 个{declared}{flag}")
    lines.append("")
    lines.append("扩展名分布：")
    for ext, count in sorted(stats.extensions.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {ext}: {count}")
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="核验源素材统计并检查文案数量声明")
    parser.add_argument("--root", type=Path, required=True, help="源素材目录")
    parser.add_argument("--copy", type=Path, help="要检查的文案文件（可选）")
    args = parser.parse_args()

    stats = scan_source(args.root)
    print(format_report(stats))

    problems = [f"folder-count-mismatch: {f.name} 标注{f.declared} 实际{f.files}"
                for f in stats.declared_mismatches]
    if args.copy:
        copy_text = args.copy.read_text(encoding="utf-8")
        problems.extend(check_claims(copy_text, stats))

    if problems:
        print("\n发现问题：")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("\n核验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
