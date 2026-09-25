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
PUBLIC_REQUIRED = (MARKER,)
FORBIDDEN = ("百度", "价格", "价钱", "实物", "快递", "物流", "试看", "私聊")
VIRTUAL_NOTICE = "【说明】虚拟资料，只发夸克网盘，拍后发网盘链接。"
_CURRENCY_RE = re.compile(r"(?:\d+(?:\.\d+)?\s*元|[￥¥]\s*\d+)")
_URL_RE = re.compile(r"(?:https?://|pan\.quark\.cn)", re.IGNORECASE)
_DELIVERY_FIELD_RE = re.compile(r"(?:文件夹名|分享\s*ID|提取码)\s*[:：]", re.IGNORECASE)


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
    labels = ("文件夹名", "链接", "提取码")
    return "\n".join(f"{label}：{value}" for label, value in zip(labels, values))


def write_project(out_dir: str | Path, title: str, body: str, quark_block: str) -> list[str]:
    """校验后写入两份完全一致的 UTF-8 文案。

    校验失败时不创建目录、不写入文件，避免失败任务留下半成品。
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
