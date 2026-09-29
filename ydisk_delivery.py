"""Configure Ydisks auto-delivery for a published Xianyu item.

The publish flow ends with a rule on the Ydisks side: when the buyer pays,
the shared delivery template renders the Quark link and passcode into a chat
message. This module owns that last step so it is repeatable instead of a
one-off request against a remembered payload.

Credentials come from the environment only (``YDISK_BASE_URL``,
``YDISK_USER``, ``YDISK_PASSWORD``). Nothing here is written to disk, and the
share link never reaches the Xianyu listing -- it goes to the Ydisks rule and
to the caller's own archive, and nowhere else.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from xianyu_common import enable_utf8_stdout

# The WAF in front of the Ydisks instance rejects the stdlib default agent
# with a bare 4xx, which reads like a credential problem when it is not.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

QUARK_URL_RE = re.compile(r"^https://pan\.quark\.cn/s/[0-9a-zA-Z]+$")
TIMEOUT = 40


class DeliveryError(RuntimeError):
    """Raised when the Ydisks side refuses or cannot be verified."""


@dataclass(frozen=True)
class Credentials:
    base_url: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "Credentials":
        missing = [
            name
            for name in ("YDISK_BASE_URL", "YDISK_USER", "YDISK_PASSWORD")
            if not os.environ.get(name)
        ]
        if missing:
            raise DeliveryError(
                "缺少环境变量：" + "、".join(missing) + "（凭据只从环境变量读取，不落盘）"
            )
        return cls(
            base_url=os.environ["YDISK_BASE_URL"].rstrip("/"),
            user=os.environ["YDISK_USER"],
            password=os.environ["YDISK_PASSWORD"],
        )


@dataclass(frozen=True)
class ShareInfo:
    """The three fields the delivery template interpolates."""

    title: str
    link: str
    passcode: str

    def validate(self) -> None:
        if not self.title.strip():
            raise DeliveryError("title 不能为空")
        if not QUARK_URL_RE.match(self.link.strip()):
            raise DeliveryError(f"link 不是合法的夸克分享地址：{self.link!r}")
        if not re.fullmatch(r"[0-9A-Za-z]{4}", self.passcode.strip()):
            raise DeliveryError(f"passcode 必须是 4 位：{self.passcode!r}")


class YdiskClient:
    """Thin authenticated wrapper over the Ydisks HTTP API."""

    def __init__(self, creds: Credentials) -> None:
        self._creds = creds
        self._jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._jar)
        )

    @property
    def base_url(self) -> str:
        return self._creds.base_url

    @property
    def user_agent(self) -> str:
        return USER_AGENT

    @property
    def opener(self) -> urllib.request.OpenerDirector:
        """The cookie-aware opener, for callers that post their own body."""
        return self._opener

    def cookies(self) -> list[str]:
        """Cookie header values for reuse on hand-built requests."""
        return [f"{c.name}={c.value}" for c in self._jar]

    def _request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> Any:
        url = f"{self._creds.base_url}{path}"
        body = None
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            url, data=body, headers=headers, method=method
        )
        try:
            with self._opener.open(request, timeout=TIMEOUT) as response:
                raw = response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise DeliveryError(
                f"{method} {path} 返回 HTTP {exc.code}：{detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise DeliveryError(f"{method} {path} 网络失败：{exc.reason}") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DeliveryError(
                f"{method} {path} 返回的不是 JSON：{raw[:200]!r}"
            ) from exc

    def login(self) -> None:
        self._request(
            "POST",
            "/api/v1/session/login",
            {"username": self._creds.user, "password": self._creds.password},
        )

    def list_items(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/items")

    def list_rules(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/v1/automation-rules")

    def create_rule(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/automation-rules", payload)


def resolve_item_id(items: list[dict[str, Any]], title: str) -> str:
    """Map a listing title to its Xianyu item id.

    Exact match only. Guessing between near-identical titles is how a rule ends
    up bound to the wrong listing, and that failure stays invisible until a
    buyer is sent someone else's link.
    """
    wanted = title.strip()
    hits = [i for i in items if (i.get("item_title") or "").strip() == wanted]
    if not hits:
        raise DeliveryError(
            f"ydisk 上找不到标题为「{wanted}」的商品，请先同步账号商品"
        )
    if len(hits) > 1:
        ids = "、".join(str(h.get("item_id")) for h in hits)
        raise DeliveryError(f"标题「{wanted}」匹配到多个商品（{ids}），请用 --item-id 指定")
    return str(hits[0]["item_id"])


def find_rule_by_item(
    rules: list[dict[str, Any]], item_id: str
) -> dict[str, Any] | None:
    for rule in rules:
        if str(rule.get("item_id")) == str(item_id):
            return rule
    return None


def build_payload(
    share: ShareInfo,
    item_id: str,
    cookie_id: str,
    template_id: int,
) -> dict[str, Any]:
    """Assemble the auto-delivery rule payload.

    ``custom_variables`` is what the delivery template interpolates, so the
    title must match the listing title exactly -- it is the first line the
    buyer reads.
    """
    return {
        "cookie_id": cookie_id,
        "item_id": item_id,
        "name": f"自动发货-{share.title}",
        "trigger_type": "order_paid",
        "enabled": True,
        "priority": 1,
        "config_json": "{}",
        "actions": [
            {
                "action_type": "send_template",
                "card_id": 0,
                "delivery_count": 1,
                "message_template": "",
                "delay_seconds": 0,
                "config_json": "",
                "enabled": True,
                "sort_order": 1,
                "delivery_template_id": template_id,
                "template_bindings": [],
                "custom_variables": {
                    "title": share.title,
                    "link": share.link,
                    "code": share.passcode,
                },
            }
        ],
    }


def rule_is_healthy(
    rule: dict[str, Any], share: ShareInfo, template_id: int
) -> list[str]:
    """Return the list of mismatches between a live rule and what we expect."""
    problems: list[str] = []
    if rule.get("trigger_type") != "order_paid":
        problems.append(f"trigger={rule.get('trigger_type')}")
    if not rule.get("enabled"):
        problems.append("rule-disabled")
    actions = rule.get("actions") or []
    if len(actions) != 1:
        problems.append(f"actions={len(actions)}")
        return problems
    action = actions[0]
    if action.get("action_type") != "send_template":
        problems.append(f"action={action.get('action_type')}")
    if not action.get("enabled"):
        problems.append("action-disabled")
    if action.get("delivery_template_id") != template_id:
        problems.append(f"template={action.get('delivery_template_id')}")
    variables = action.get("custom_variables") or {}
    for key, expected in (
        ("title", share.title),
        ("link", share.link),
        ("code", share.passcode),
    ):
        if (variables.get(key) or "").strip() != expected:
            problems.append(f"{key}-mismatch")
    return problems


def append_archive(path: str, share: ShareInfo) -> None:
    """Append ``title|code|link`` to the caller's private archive.

    The archive holds live share links, so it stays outside the repository and
    the path is always supplied by whoever runs this.
    """
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"{share.title}|{share.passcode}|{share.link}\n")


def main() -> int:
    enable_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="在 ydisk 上为已发布商品配置付款自动发货"
    )
    parser.add_argument("--title", required=True, help="闲鱼商品标题，需与 ydisk 上的标题完全一致")
    parser.add_argument("--link", required=True, help="夸克分享链接")
    parser.add_argument("--code", required=True, help="四位提取码")
    parser.add_argument("--item-id", help="闲鱼商品 ID，省略时按标题精确匹配")
    parser.add_argument("--cookie-id", default="123097626", help="绑定的闲鱼账号 cookie id")
    parser.add_argument("--template-id", type=int, default=2, help="发货模板 id")
    parser.add_argument("--archive", help="归档文件路径，追加 title|code|link")
    parser.add_argument("--dry-run", action="store_true", help="只校验和展示，不写入")
    args = parser.parse_args()

    share = ShareInfo(args.title, args.link.strip(), args.code.strip())
    share.validate()

    client = YdiskClient(Credentials.from_env())
    client.login()
    items = client.list_items()
    item_id = args.item_id or resolve_item_id(items, share.title)
    print(f"商品：{share.title}")
    print(f"item_id：{item_id}")

    rules = client.list_rules()
    existing = find_rule_by_item(rules, item_id)
    if existing is not None:
        problems = rule_is_healthy(existing, share, args.template_id)
        if not problems:
            print(f"已存在且校验通过（rule id={existing.get('id')}），无需改动")
            return 0
        raise DeliveryError(
            f"rule id={existing.get('id')} 已存在但与预期不符：{'、'.join(problems)}。"
            "请先在 ydisk 界面删除该规则再重跑，避免重复发货。"
        )

    if args.dry_run:
        print("dry-run：校验通过，未写入")
        return 0

    created = client.create_rule(
        build_payload(share, item_id, args.cookie_id, args.template_id)
    )
    rule_id = created.get("id") if isinstance(created, dict) else None

    # Read back rather than trusting the POST: a 200 only means the request was
    # accepted, not that the template variables survived the round trip.
    verified = find_rule_by_item(client.list_rules(), item_id)
    if verified is None:
        raise DeliveryError("规则创建后回读不到，请到 ydisk 界面确认是否重复创建")
    problems = rule_is_healthy(verified, share, args.template_id)
    if problems:
        raise DeliveryError(
            f"规则 id={verified.get('id')} 回读校验失败：{'、'.join(problems)}"
        )

    if args.archive:
        append_archive(args.archive, share)
        print(f"已归档：{args.archive}")
    print(f"配置完成：rule id={rule_id or verified.get('id')}，触发=订单付款，动作=发送模板")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DeliveryError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc
