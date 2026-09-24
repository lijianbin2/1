"""生成并校验闲鱼商品文案。

模块只负责纯文本生成和文件写入，不依赖 PIL，也不会在导入时访问 D 盘。
"""

from __future__ import annotations

import re
from pathlib import Path

MARKER = "只发夸克"
DESC_NAME = "desc.txt"
COPY_NAME = "闲鱼发布文案_直接复制.txt"
QUARK_LABELS = ("文件夹名", "链接", "提取码")
REQUIRED = (MARKER, *QUARK_LABELS)
FORBIDDEN = ("百度", "价格", "价钱", "实物", "快递", "物流", "试看", "私聊")
VIRTUAL_NOTICE = "【说明】虚拟资料，只发夸克网盘，拍后发网盘链接。"
_CURRENCY_RE = re.compile(r"(?:\d+(?:\.\d+)?\s*元|[￥¥]\s*\d+)")


def _forbidden_hits(text: str, word: str) -> list[str]:
    """返回命中项，供调用方统一生成违规代码。"""
    return [word] if word in text else []


def check_copy(title: str, body: str) -> list[str]:
    """检查标题和正文是否违反发布规则。

    价格使用数字+“元”或货币符号匹配，避免把“元素”等普通词语误判为价格。
    """
    bad: list[str] = []
    for index, word in enumerate(FORBIDDEN):
        if _forbidden_hits(title, word):
            bad.append(f"forbidden[{index}]-in-title")
        if _forbidden_hits(body, word):
            bad.append(f"forbidden[{index}]-in-body")

    for index, word in enumerate(REQUIRED):
        if word not in title and word not in body:
            bad.append(f"required[{index}]-missing")

    if _CURRENCY_RE.search(title):
        bad.append("currency-in-title")
    if _CURRENCY_RE.search(body):
        bad.append("currency-in-body")
    return bad


def build_title(core: str, count_str: str) -> str:
    """生成不含价格的标准标题。"""
    return f"{core.strip()} {count_str.strip()} {MARKER}"


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
    if not link.startswith("https://pan.quark.cn/s/"):
        raise ValueError("link 必须是夸克分享链接")
    labels = ("文件夹名", "链接", "提取码")
    return "\n".join(f"{label}：{value}" for label, value in zip(labels, values))


def write_project(out_dir: str | Path, title: str, body: str, quark_block: str) -> list[str]:
    """校验后写入两份完全一致的 UTF-8 文案。

    校验失败时不创建目录、不写入文件，避免失败任务留下半成品。
    """
    body = body.strip()
    full_body = f"{title.strip()}\n\n{body}\n\n{quark_block.strip()}"
    bad = check_copy(title.strip(), full_body)
    if bad:
        print(f"check failed violations={bad}")
        return bad

    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    full = full_body + "\n"
    for filename in (DESC_NAME, COPY_NAME):
        (p / filename).write_text(full, encoding="utf-8", newline="\n")
    print(f"wrote {p} violations=[]")
    return []
