"""生成并校验闲鱼商品文案。

模块只负责纯文本生成和文件写入，不依赖 PIL，也不会在导入时访问 D 盘。
既可以当库用，也可以直接 ``python make_desc.py ...`` 跑完整流程。
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

MARKER = "只发夸克"
DESC_NAME = "desc.txt"
COPY_NAME = "闲鱼发布文案_直接复制.txt"
QUARK_LABELS = ("文件夹名", "链接", "提取码")
REQUIRED = (MARKER, *QUARK_LABELS)
PUBLIC_REQUIRED = (MARKER,)
# 虚拟资料在闲鱼挂闲鱼发布页，遇到实物/自动发货类承诺容易引出货不对板纠纷，
# 一律拦在正文之外。价格也不写：平台上单独填价格栏，正文再写会前后打架。
FORBIDDEN = (
    "百度",
    "价格",
    "价钱",
    "实物",
    "快递",
    "物流",
    "试看",
    "私聊",
    "自动发货",
)
VIRTUAL_NOTICE = "【说明】虚拟资料，只发夸克网盘，拍后发网盘链接。"
_CURRENCY_RE = re.compile(r"(?:\d+(?:\.\d+)?\s*元|[￥¥]\s*\d+)")
_URL_RE = re.compile(r"(?:https?://|pan\.quark\.cn)", re.IGNORECASE)
_DELIVERY_FIELD_RE = re.compile(r"(?:文件夹名|分享\s*ID|提取码)\s*[:：]", re.IGNORECASE)


def copy_to_clipboard(text: str) -> bool:
    """把文本放进系统剪贴板，交付分享信息时避免手动分段复制。

    成功返回 ``True``；没有可用的剪贴板命令时返回 ``False``，由调用方
    决定是否退回手动复制，而不是静默假装已经复制成功。
    """
    text = text.strip()
    if not text:
        raise ValueError("复制内容不能为空")
    if sys.platform != "win32":
        return False
    try:
        completed = subprocess.run(
            ["clip"],
            input=text.encode("utf-16-le"),
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return completed.returncode == 0


def _forbidden_hits(text: str, word: str) -> list[str]:
    """返回命中项，供调用方统一生成违规代码。"""
    return [word] if word in text else []


def _check_rules(
    title: str,
    body: str,
    *,
    required: tuple[str, ...],
    forbidden: tuple[str, ...],
    reject_urls: bool = False,
) -> list[str]:
    """执行共享的标题和正文检查。"""
    bad: list[str] = []
    for index, word in enumerate(forbidden):
        if _forbidden_hits(title, word):
            bad.append(f"forbidden[{index}]-in-title")
        if _forbidden_hits(body, word):
            bad.append(f"forbidden[{index}]-in-body")

    for index, word in enumerate(required):
        if word not in title and word not in body:
            bad.append(f"required[{index}]-missing")

    if _CURRENCY_RE.search(title):
        bad.append("currency-in-title")
    if _CURRENCY_RE.search(body):
        bad.append("currency-in-body")
    if reject_urls:
        if _URL_RE.search(title):
            bad.append("url-in-title")
        if _URL_RE.search(body):
            bad.append("url-in-body")
        if _DELIVERY_FIELD_RE.search(title):
            bad.append("delivery-field-in-title")
        if _DELIVERY_FIELD_RE.search(body):
            bad.append("delivery-field-in-body")
    return bad


def check_copy(title: str, body: str) -> list[str]:
    """检查完整交付包（标题、正文和分享块）。

    价格使用数字+“元”或货币符号匹配，避免把“元素”等普通词语误判为价格。
    """
    return _check_rules(
        title,
        body,
        required=REQUIRED,
        forbidden=FORBIDDEN,
    )


def check_public_copy(title: str, body: str) -> list[str]:
    """检查可直接粘贴到闲鱼的正文，拒绝 URL 和分享字段。"""
    return _check_rules(
        title,
        body,
        required=PUBLIC_REQUIRED,
        forbidden=FORBIDDEN,
        reject_urls=True,
    )


def build_title(core: str, count_str: str) -> str:
    """生成不含价格的标准标题。"""
    core = core.strip()
    count_str = count_str.strip()
    if not core or not count_str:
        raise ValueError("core 和 count_str 均不能为空")
    return f"{core} {count_str} {MARKER}"


def build_body(
    title: str,
    intro: str,
    modules: list[str] | tuple[str, ...],
    audience: str,
) -> str:
    """组装标题之后的正文。

    ``title`` 保留在函数签名中是为了兼容旧调用，但返回值不重复包含标题；
    ``write_project`` 会在最前面统一写入标题。
    """
    if not title.strip():
        raise ValueError("title 不能为空")
    if not intro.strip():
        raise ValueError("intro 不能为空")
    normalized_modules = [item.strip() for item in modules if item.strip()]
    if not normalized_modules:
        raise ValueError("modules 至少需要一项")
    audience = audience.strip()
    if not audience:
        raise ValueError("audience 不能为空")
    if not audience.startswith("适合"):
        audience = f"适合{audience}"
    return "\n\n".join(
        [
            intro.strip(),
            "内容简介：\n" + "\n".join(normalized_modules),
            audience + "，适合有具体需求的用户。",
            VIRTUAL_NOTICE,
        ]
    )


def build_quark(folder: str, link: str, code: str) -> str:
    """生成严格三行、全角冒号的夸克分享块。"""
    values = (folder.strip(), link.strip(), code.strip())
    if not all(values):
        raise ValueError("folder、link、code 均不能为空")
    if any("\n" in value or "\r" in value for value in values):
        raise ValueError("folder、link、code 不能包含换行")
    if not re.fullmatch(r"https://pan\.quark\.cn/s/[A-Za-z0-9_-]+", link):
        raise ValueError("link 必须是夸克分享链接")
    if not re.fullmatch(r"[A-Za-z0-9]{4}", code):
        raise ValueError("code 必须是四位字母或数字")
    return "\n".join(f"{label}：{value}" for label, value in zip(QUARK_LABELS, values))


def write_project(out_dir: str | Path, title: str, body: str, quark_block: str) -> list[str]:
    """校验后写入完整交付包和不含分享信息的公开正文。

    ``desc.txt`` 保存完整交付包，``闲鱼发布文案_直接复制.txt`` 只保存可直接
    粘贴到闲鱼的标题和正文。校验失败时不创建目录、不写入文件，避免失败
    任务留下半成品。
    """
    title = title.strip()
    body = body.strip()
    quark_block = quark_block.strip()
    if not title or not body or not quark_block:
        print("check failed violations=empty-field")
        return ["empty-field"]
    public_body = f"{title}\n\n{body}"
    full_body = f"{public_body}\n\n{quark_block}"
    bad = check_public_copy(title, public_body)
    bad.extend(
        violation
        for violation in check_copy(title, full_body)
        if violation not in bad
    )
    if bad:
        print(f"check failed violations={bad}")
        return bad

    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / DESC_NAME).write_text(full_body + "\n", encoding="utf-8", newline="\n")
    (p / COPY_NAME).write_text(public_body + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {p} violations=[]")
    return []


def write_public_copy(out_dir: str | Path, title: str, body: str) -> list[str]:
    """只写入可直接粘贴到闲鱼的公开正文。

    分享链接还没创建时用它先生成公开正文；``desc.txt`` 等拿到真实分享信息
    后再用 :func:`write_project` 补齐。
    """
    title = title.strip()
    body = body.strip()
    if not title or not body:
        print("check failed violations=empty-field")
        return ["empty-field"]
    public_body = f"{title}\n\n{body}"
    bad = check_public_copy(title, public_body)
    if bad:
        print(f"check failed violations={bad}")
        return bad

    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / COPY_NAME).write_text(public_body + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {p / COPY_NAME} violations=[]")
    return []


def main() -> int:
    """命令行入口：一条命令产出公开正文，需要时补齐完整交付包。"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="生成闲鱼正文和夸克分享块")
    parser.add_argument("--out", type=Path, required=True, help="输出目录")
    parser.add_argument("--core", required=True, help="项目名称，用于标题")
    parser.add_argument("--count", required=True, help="数量描述，例如 10集")
    parser.add_argument("--intro", required=True, help="一句话介绍")
    parser.add_argument("--module", action="append", default=[], help="内容明细，可重复")
    parser.add_argument("--audience", required=True, help="适合人群")
    parser.add_argument("--folder", help="夸克文件夹名（标题）")
    parser.add_argument("--link", help="夸克分享链接")
    parser.add_argument("--code", help="四位提取码")
    parser.add_argument(
        "--copy",
        action="store_true",
        help="把文件夹名、链接和提取码三行复制到剪贴板",
    )
    args = parser.parse_args()

    title = build_title(args.core, args.count)
    body = build_body(title, args.intro, args.module, args.audience)

    share = (args.folder, args.link, args.code)
    if any(share):
        if not all(share):
            parser.error("--folder、--link、--code 必须同时提供")
        quark_block = build_quark(*share)
        violations = write_project(args.out, title, body, quark_block)
    else:
        quark_block = ""
        violations = write_public_copy(args.out, title, body)
    if violations:
        return 1

    if args.copy:
        if not quark_block:
            parser.error("--copy 需要同时提供 --folder、--link、--code")
        if copy_to_clipboard(quark_block):
            print("clipboard=ok")
        else:
            print("clipboard=failed，请手动复制下面的分享信息")
            print(quark_block)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
