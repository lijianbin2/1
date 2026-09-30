"""Publish a prepared listing to Xianyu through the Ydisks instance.

Ydisks owns the browser session for the bound Xianyu account, so it can post
the listing itself. Driving the site with Playwright from here needed a
persistent Chrome profile and manual category fixes every run; the Ydisks
publish endpoint takes the same fields and keeps category and account pinned.

The share link never goes into this payload. The listing body is checked
against the same rule the Playwright filler used: no Quark URL, no passcode,
no price, no shipping promise.

Credentials come from the environment only, reusing ``ydisk_delivery``.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from xianyu_common import enable_utf8_stdout
from ydisk_delivery import Credentials, DeliveryError, YdiskClient

PUBLISH_PATH = "/api/v1/items/publish"
TIMEOUT = 120

# Reused verbatim from the Playwright form filler: a listing body must never
# carry the delivery link, the passcode, a price, or a shipping promise.
FORBIDDEN_BODY_PATTERNS = (
    (re.compile(r"quark\.cn", re.I), "url-in-body"),
    (re.compile(r"pan\.quark", re.I), "url-in-body"),
    (re.compile(r"提取码[:：]\s*\S{4}"), "delivery-field-in-body"),
    (re.compile(r"\d+\s*元"), "price-in-body"),
    (re.compile(r"包邮|现货|秒发|自动发货"), "shipping-promise-in-body"),
)


def check_body(body: str) -> list[str]:
    """Return the rule ids the listing body breaks."""
    problems = [
        label for pattern, label in FORBIDDEN_BODY_PATTERNS if pattern.search(body)
    ]
    if not body.strip():
        problems.append("empty-body")
    return problems


def load_body(path: Path) -> tuple[str, str]:
    """Read the copy file as (title, description) with the title kept inline.

    Xianyu has no separate title field: the listing title *is* the first line
    of the description. Splitting them and posting the title on its own makes
    the platform promote the second line (the subtitle) to the title instead,
    which is how two listings ended up titled "从零搭建个人AI效率系统…".
    So the description keeps the title as its first line and ``title`` is only
    a local copy for the delivery rule, which does need them apart.
    """
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise DeliveryError(f"文案文件为空：{path}")
    lines = text.splitlines()
    title = lines[0].strip()
    body = "\n".join(lines[1:]).strip()
    if not title:
        raise DeliveryError(f"文案第一行（标题）为空：{path}")
    if len(title) > 30:
        raise DeliveryError(f"标题超过 30 字（{len(title)}）：{title}")
    return title, text.strip()


def load_images(folder: Path, names: list[str]) -> list[Path]:
    if not names:
        raise DeliveryError("至少要指定一张主图")
    if len(names) > 3:
        raise DeliveryError(f"主图最多 3 张，收到 {len(names)} 张")
    images = []
    for name in names:
        path = folder / name
        if not path.is_file():
            raise DeliveryError(f"图片不存在：{path}")
        images.append(path)
    return images


def encode_multipart(
    fields: dict[str, str], images: list[Path]
) -> tuple[bytes, str]:
    """Build the multipart body for the publish endpoint.

    The Ydisks frontend posts FormData, so the same shape is reproduced by
    hand -- stdlib has no multipart encoder and the images need real filenames
    and content types rather than base64 blobs.
    """
    boundary = f"----xianyu{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
        )
        chunks.append(f"{value}\r\n".encode("utf-8"))
    for path in images:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="images"; filename="{path.name}"\r\n'.encode()
        )
        chunks.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def publish(
    client: YdiskClient,
    *,
    cookie_id: str,
    title: str,
    body: str,
    price: str,
    images: list[Path],
    category_id: str,
    category_name: str,
    channel_category_id: str,
    quantity: int = 1,
) -> dict[str, Any]:
    fields = {
        "cookie_id": cookie_id,
        "title": title,
        "description": body,
        "price": price,
        "original_price": "",
        "quantity": str(quantity),
        # Virtual goods: no postage field is accepted, and picking 包邮
        # instead is what makes a listing read as a physical product.
        "postage_mode": "none",
        "postage": "",
        "category_id": category_id,
        "category_name": category_name,
        "channel_category_id": channel_category_id,
    }
    payload, content_type = encode_multipart(fields, images)
    url = f"{client.base_url}{PUBLISH_PATH}"
    request = urllib.request.Request(url, data=payload, method="POST")
    request.add_header("Content-Type", content_type)
    request.add_header("Accept", "application/json")
    request.add_header("User-Agent", client.user_agent)
    for cookie in client.cookies():
        request.add_header("Cookie", cookie)
    try:
        with client.opener.open(request, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        raise DeliveryError(f"发布返回 HTTP {exc.code}：{detail}") from exc
    except urllib.error.URLError as exc:
        raise DeliveryError(f"发布网络失败：{exc.reason}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DeliveryError(f"发布返回的不是 JSON：{raw[:300]!r}") from exc


def main() -> int:
    enable_utf8_stdout()
    parser = argparse.ArgumentParser(description="通过 ydisk 发布闲鱼图文商品")
    parser.add_argument("--desc", required=True, type=Path, help="文案文件，第一行为标题")
    parser.add_argument("--images", required=True, help="主图文件名，逗号分隔，最多 3 张")
    parser.add_argument("--image-dir", required=True, type=Path, help="图片所在目录")
    parser.add_argument("--price", required=True, help="售价，单位元")
    parser.add_argument("--cookie-id", default="123097626", help="绑定的闲鱼账号 cookie id")
    parser.add_argument("--category-id", default="50023914", help="闲鱼类目 id")
    parser.add_argument("--category-name", default="电子资料", help="闲鱼类目名")
    parser.add_argument("--channel-category-id", default="202036301", help="闲鱼渠道类目 id")
    parser.add_argument("--dry-run", action="store_true", help="只校验文案与图片，不提交")
    args = parser.parse_args()

    try:
        price_value = float(args.price)
    except ValueError:
        raise DeliveryError(f"价格不是数字：{args.price!r}") from None
    if price_value <= 0:
        raise DeliveryError("价格必须大于 0")
    price = f"{price_value:g}"

    title, description = load_body(args.desc)
    # 校验整段文案：标题也是会被平台显示的文字，链接或价格藏在首行同样违规
    problems = check_body(description)
    if problems:
        raise DeliveryError("正文触发了拦截规则：" + "、".join(problems))
    images = load_images(
        args.image_dir, [n.strip() for n in args.images.split(",") if n.strip()]
    )

    print(f"标题：{title}")
    print(f"类目：{args.category_name}（{args.category_id}）")
    print(f"价格：{price} 元　发货：无需邮寄　数量：1")
    print(f"主图：{'、'.join(p.name for p in images)}")
    print(f"正文：{len(description)} 字（含标题首行），拦截规则 0 命中")
    if args.dry_run:
        print("dry-run：未提交")
        return 0

    client = YdiskClient(Credentials.from_env())
    client.login()
    result = publish(
        client,
        cookie_id=args.cookie_id,
        title=title,
        body=description,
        price=price,
        images=images,
        category_id=args.category_id,
        category_name=args.category_name,
        channel_category_id=args.channel_category_id,
    )
    print(json.dumps(result, ensure_ascii=False))
    if not result.get("success"):
        raise DeliveryError(f"ydisk 返回未成功：{result.get('message')}")
    # The endpoint answers with the item fields at the top level; there is no
    # data envelope, so reading result["data"] here hid a success behind a
    # hard failure.
    item_id = result.get("item_id") or (result.get("data") or {}).get("item_id")
    if not item_id:
        raise DeliveryError("发布结果里没有 item_id，请到 ydisk 界面确认是否已上架")
    print(f"发布成功 item_id={item_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DeliveryError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc
