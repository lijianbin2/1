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

# 计数单位取自目录名的标注习惯（见 _DECLARED_IN_NAME）。
# 文案里的计数声明必须用同一套单位，否则"468张矢量图"这种错数会一路
# 放行——校验器只认"个文件"和"首"，其余单位等于没测。
#
# "个"故意不进 _COUNT_CLAIM：正文里"41个视频""12个章节"里的"个"数的是
# 章节而不是文件，拿它跟文件总数比必然误报。个文件 由 _TOTAL_FILES 单独管。
_COUNT_UNITS = ("首", "张", "套", "集", "期")
_UNIT_ALT = "|".join(_COUNT_UNITS)
_DECLARED_IN_NAME = re.compile(rf"[-—_](\d+)\s*(?:个|{_UNIT_ALT})\s*$")
_TOTAL_FILES = re.compile(r"(\d+)\s*个文件")
_COUNT_CLAIM = re.compile(rf"(\d+)\s*({_UNIT_ALT})")
_SIZE = re.compile(r"(\d+(?:\.\d+)?)\s*(TB|GB|MB)", re.IGNORECASE)
_SUM_CLAIM = re.compile(rf"共\s*(\d+)\s*(?:{_UNIT_ALT})")
_LISTED_LINE = re.compile(r"^\s*(?:\d+\s*[.、)）]\s*)?[\d一二三四五六七八九十]+\s*[.、)）]\s*")
_DETAIL_HEADING = "内容简介"
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
        # 只有真正的子目录才算"一级分类"。直接躺在源目录根下的散文件
        # （课程合集很常见：一个 mp4 一节课，没有分类文件夹）如果也当成
        # 分类，就会每个文件报一行"一级分类"，而且文件名里带"-5张"这种
        # 标注会被 _declared_count 读成目录名声明，凭空判出一处不一致，
        # 让整个核验以退出码 1 失败。这类散文件只计入总数和扩展名分布。
        parts = path.relative_to(root).parts
        if len(parts) == 1:
            continue
        top = parts[0]
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


def _detail_indices(lines: list[str]) -> set[int]:
    """返回明细行的下标。

    早先只认"1. ""2. "这种编号前缀，但 ``make_desc.build_body`` 生成的正文
    里明细是 ``--module`` 原样拼进去的，实际发布时常常不编号。宣传片音乐
    那份文案就是 ``内容简介：`` 下面直接写七行"汽车宣传片 37首"…，编号
    一条都没有，于是这七行全部落进正文检查，每行的分类数量都被拿去和
    970 首的**总数**比一遍，报出七条 body-count-mismatch。数量本身全是对的，
    校验器却把发布挡下来了。

    所以先按结构认：``内容简介`` 标题下面那一整块连续非空行就是明细，
    编不编号都算。找不到标题时才退回按编号前缀认，这样"1. 900张"这种
    整份文案里唯一的数量声明仍然能被 item-sum 校验接住。
    """
    for index, line in enumerate(lines):
        head = re.split(r"[：:]", line, maxsplit=1)[0].strip()
        if head != _DETAIL_HEADING:
            continue
        block: set[int] = set()
        for offset, candidate in enumerate(lines[index + 1:], start=index + 1):
            if not candidate.strip():
                break
            block.add(offset)
        if block:
            return block
        break
    return {index for index, line in enumerate(lines) if _LISTED_LINE.match(line)}


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

    for match in _SUM_CLAIM.finditer(text):
        claimed = int(match.group(1))
        if claimed != stats.total_files:
            violations.append(
                f"sum-claim-mismatch: 文案{match.group(0).strip()} 实际{stats.total_files}"
            )

    lines = [line for line in text.splitlines() if line.strip()]
    detail = _detail_indices(lines)
    detail_lines = [lines[index] for index in sorted(detail)]
    items = [
        int(count)
        for line in detail_lines
        for count, _unit in _COUNT_CLAIM.findall(_SUM_CLAIM.sub("", line))
    ]
    # 明细是总数的一份划分，累加必须等于总数——只有一条时同样要校。
    # 早先写成 len(items) > 1，理由是怕单条明细被当成总数重复报，但明细行
    # 已经被排除在正文检查之外，"1. 900张"这种整份文案里唯一的数量声明
    # 就此完全没人管：对 468 个文件的素材目录实测返回空违规列表。
    if items:
        listed = sum(items)
        if listed != stats.total_files:
            violations.append(f"item-sum-mismatch: 明细合计{listed} 实际{stats.total_files}")

    body = "\n".join(
        line for index, line in enumerate(lines) if index and index not in detail
    )
    for raw, unit in _COUNT_CLAIM.findall(_SUM_CLAIM.sub("", lines[0] if lines else "")):
        if int(raw) != stats.total_files:
            violations.append(
                f"title-count-mismatch: 标题{raw}{unit} 实际{stats.total_files}"
            )
    for raw, unit in _COUNT_CLAIM.findall(_SUM_CLAIM.sub("", body)):
        if int(raw) != stats.total_files:
            violations.append(
                f"body-count-mismatch: 正文{raw}{unit} 实际{stats.total_files}"
            )

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
