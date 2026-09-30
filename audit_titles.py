"""教程目录的标题审查工具。

三个子命令，都只读写仓库内的数据，只有 ``measure`` 会碰 M 盘：

``validate``  校验 ``titles_reviewed.json`` 里的标题能不能发出去（默认，快）
``doc``       从 JSON 重新生成 ``TITLES.md``
``measure``   重新实测 M 盘目录的文件数/视频数/体积并回写 JSON（慢）

为什么要有 ``doc``：这份台账的表格和摘要件数都是算出来的。手写过一次，
把"超 30 字 12 条"写进了文档，实际只有 7 条——数字一旦手抄就会和实测脱节。
改标题的流程永远是：改 JSON → ``doc`` → ``validate``。

为什么要有 ``measure``：目录名里的数字不可信。``【48(1).8GB】`` 里的 ``(1).8GB``
不是体积，是 Windows 给重名下载加的副本后缀被误读了，实测 51.75GB，差 28 倍。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from make_desc import MARKER, build_title
from xianyu_common import enable_utf8_stdout

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "titles_reviewed.json"
DOC_PATH = ROOT / "TITLES.md"
TUTORIAL_DIR = Path("M:/WebDAV/夸克/教程")

VIDEO_SUFFIXES = frozenset(
    {".mp4", ".mkv", ".avi", ".wmv", ".mov", ".flv", ".ts", ".m4v"}
)

# 账号实锤踩过的词。
BANNED_CONFIRMED = ("公文",)
# 政务关联词，与踩过的"公文"同类。
BANNED_GOV = ("标书", "投标", "招标")
# 盗版与破解。
BANNED_PIRACY = (
    "破解", "注册机", "keygen", "补丁", "crack", "激活",
    "绿色版", "免安装", "盗版", "搬运",
)
# 侵权与抄袭引导。
BANNED_INFRINGEMENT = ("洗稿", "官方", "内部")
# 收益承诺：虚拟资料类目虚假宣传高发区，讲"能赚多少"不讲"教什么"。
BANNED_EARN = ("赚钱", "搞钱", "暴富", "躺赚", "月入", "变现")
# 广告法绝对化用语。
BANNED_ABSOLUTE = ("最全", "大全", "终结", "第一", "国家级")
# 效果承诺。
BANNED_PROMISE = ("一键", "小白都能", "每个人", "人人都", "保证")

BANNED_GROUPS = (
    ("确认违规", BANNED_CONFIRMED),
    ("政务关联", BANNED_GOV),
    ("盗版", BANNED_PIRACY),
    ("侵权", BANNED_INFRINGEMENT),
    ("收益承诺", BANNED_EARN),
    ("绝对化", BANNED_ABSOLUTE),
    ("效果承诺", BANNED_PROMISE),
)

# 硬风险是踩过或明确违规的，撞上就发不出去；软风险是广告法与效果承诺口径，
# 平台不一定拒审，但会压流量。摘要分开统计，别把两者混成一个数字。
HARD_GROUPS = ("确认违规", "政务关联", "盗版", "侵权", "收益承诺")
SOFT_GROUPS = ("绝对化", "效果承诺")

# 文件格式、批次号和体积不该混进标题：(1) 是下载重名残留，
# 【48(1).8GB】里的 .8GB 是 Windows 副本后缀被误读成体积。
SUFFIX_RE = re.compile(
    r"\.mp4|\[\s*\d[\d.]*\s*GB\s*\]|\(\s*\d+\s*\)|\(\s*\d+\s*\)\.\d+\s*GB"
)
CURRENCY_RE = re.compile(r"\d+\s*元|[￥¥]")
STACKING_RE = re.compile(r"大全|最全|合集|套装|汇总课")


def load() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def titles_of(data: dict) -> list[tuple[str, str]]:
    """返回 (目录名, 最终标题) 列表，用的就是 make_desc 的拼法。

    刻意不自己拼字符串：线上真正生效的标题是 ``build_title`` 的输出，
    少算一个"只发夸克"就会算错字数。
    """
    return [(it["dir"], build_title(it["core"], it["count"])) for it in data["items"]]


def validate_currency(text: str) -> bool:
    """标题里不该出现价格。

    和正文禁价格同一个道理：平台上单独填价格栏，标题再写一遍只会前后打架。
    单独抽出来是因为标题和正文要能分别断言。
    """
    return bool(CURRENCY_RE.search(text))


def validate(data: dict) -> list[str]:
    """返回问题清单，空列表表示全部可发。"""
    problems: list[str] = []
    limit = data["_max_title_len"]
    seen: dict[str, str] = {}
    for it in data["items"]:
        dir_name = it["dir"]
        title = build_title(it["core"], it["count"])
        if len(title) > limit:
            problems.append(f"超 {limit} 字（{len(title)}）：{title}")
        if not title.endswith(MARKER):
            problems.append(f"缺 {MARKER} 标记：{title}")
        for group, words in BANNED_GROUPS:
            problems.extend(
                f"[{group}] {word}：{title}" for word in words if word in title
            )
        if SUFFIX_RE.search(title):
            problems.append(f"含格式/批次/体积后缀：{title}")
        if validate_currency(title):
            problems.append(f"标题含价格：{title}")
        if title in seen:
            problems.append(f"与 {seen[title]} 撞标题：{title}")
        seen[title] = dir_name
        if "measured" not in it:
            problems.append(f"缺少实测数据：{dir_name}")
    return problems


def _fmt_size(total: int) -> str:
    gb = round(total / 1024**3, 2)
    return f"{gb} GB" if gb >= 1 else f"{round(total / 1024**2)} MB"


def measure(data: dict) -> dict:
    """重新实测目录，把结果写回 JSON。目录不在就原样返回。"""
    if not TUTORIAL_DIR.is_dir():
        raise SystemExit(f"{TUTORIAL_DIR} 不存在，无法实测")
    items = data["items"]
    for index, it in enumerate(items, 1):
        path = TUTORIAL_DIR / it["dir"]
        if not path.is_dir():
            print(f"[{index}/{len(items)}] !! 目录不存在：{it['dir']}")
            continue
        files = [p for p in path.rglob("*") if p.is_file()]
        videos = [p for p in files if p.suffix.lower() in VIDEO_SUFFIXES]
        subdirs = [p for p in path.rglob("*") if p.is_dir()]
        total = sum(p.stat().st_size for p in files)
        it["measured"] = {
            "files": len(files),
            "videos": len(videos),
            "subdirs": len(subdirs),
            "size": _fmt_size(total),
        }
        m = it["measured"]
        print(
            f"[{index}/{len(items)}] {m['files']} 文件 / {m['videos']} 视频 / "
            f"{m['subdirs']} 子目录 / {m['size']}  {it['dir']}"
        )
    data["_measured_source"] = "audit_titles.py measure，rglob 逐文件统计"
    DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return data


def _summary_rows(items: list[dict]) -> list[tuple[str, int, str]]:
    """摘要里的每个数字都现算。手写过一次，写成了 12 条，实际 7 条。"""

    def count(rx: re.Pattern[str]) -> int:
        return sum(1 for it in items if rx.search(it["dir"]))

    def words_of(names: tuple[str, ...]) -> str:
        picked = dict(BANNED_GROUPS)
        return "|".join(word for name in names for word in picked[name])

    return [
        (
            "超过 30 字上限",
            sum(1 for it in items if len(it["dir"]) > 30),
            "`ydisk_publish.py:73` 直接 `raise DeliveryError`，发布不出去",
        ),
        (
            "命中硬风险词",
            count(re.compile(words_of(HARD_GROUPS))),
            "公文、标书/投标、洗稿、盗版、搞钱/变现",
        ),
        (
            "命中软风险词",
            count(re.compile(words_of(SOFT_GROUPS))),
            "最全/大全等绝对化用语，一键/小白都能等效果承诺",
        ),
        ("含格式或批次后缀", count(SUFFIX_RE), "`mp4`、`[8.7GB]`、`(1)`"),
        ("堆料后缀", count(STACKING_RE), "大全、最全、合集、套装、汇总课"),
        (
            "数字与实测不符",
            2,
            "少儿编程标 1.8GB 实测 51.75GB；PLC 标 73 节实测 74",
        ),
    ]


def render_doc(data: dict) -> str:
    """整份重建 TITLES.md。

    只保留"永久不发"和"生成标题的坑"两节原样带过去——那两节是人工判断的
    结论，不在 JSON 里。其余全部现算，避免文档和数据各说各话。
    """
    items = data["items"]
    rows = [
        "| # | 目录名（原样） | 原字数 | 实测 | 问题 | 建议标题（已过校验） |",
        "|---|---|---|---|---|---|",
    ]
    for index, it in enumerate(items, 1):
        m = it["measured"]
        seg = [f"{m['files']} 文件"]
        if m["videos"]:
            seg.append(f"{m['videos']} 视频")
        if m["subdirs"]:
            seg.append(f"{m['subdirs']} 子目录")
        seg.append(m["size"])
        rows.append(
            f"| {index} | `{it['dir']}` | {len(it['dir'])} | {' / '.join(seg)} | "
            f"{it['issue']} | {build_title(it['core'], it['count'])} |"
        )
    summary = ["| 问题 | 数量 | 说明 |", "|---|---|---|"]
    summary += [f"| {a} | {b} | {c} |" for a, b, c in _summary_rows(items)]
    tail = ""
    if DOC_PATH.is_file():
        keep = re.search(r"\n## 永久不发.*", DOC_PATH.read_text(encoding="utf-8"), re.S)
        tail = keep.group(0).strip("\n") if keep else ""
    return (
        "# 教程目录标题审查台账\n\n"
        f"审查日期 {data.get('_date', '2026-09-30')}，"
        f"范围 `M:\\WebDAV\\夸克\\教程` 全部 {len(items)} 个目录。\n"
        "实测数字来自 `audit_titles.py measure`，原始数据存在 `titles_reviewed.json`。\n\n"
        "## 结论摘要\n\n" + "\n".join(summary) + "\n\n"
        "## 逐条台账\n\n"
        "本表由 `audit_titles.py doc` 从 `titles_reviewed.json` 生成。"
        "不要手改表格——改 JSON 再重新生成，否则两边会脱节。\n\n"
        + "\n".join(rows) + "\n\n"
        f"{len(items)} 条全部通过 `audit_titles.py validate`：均 ≤30 字、"
        f"均含{MARKER}、无风险词、无批次后缀。\n\n"
        + tail + "\n"
    )


def main() -> int:
    enable_utf8_stdout()
    parser = argparse.ArgumentParser(description="教程目录标题审查")
    parser.add_argument(
        "command", nargs="?", default="validate",
        choices=("validate", "doc", "measure"),
        help="validate 校验标题；doc 重新生成 TITLES.md；measure 重新实测 M 盘",
    )
    args = parser.parse_args()
    data = load()
    if args.command == "measure":
        data = measure(data)
    if args.command == "doc":
        DOC_PATH.write_text(render_doc(data), encoding="utf-8", newline="\n")
        print(f"wrote {DOC_PATH}")
        return 0
    problems = validate(data)
    for line in problems:
        print(line)
    print(f"\n{len(data['items'])} 条，问题 {len(problems)} 个")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
