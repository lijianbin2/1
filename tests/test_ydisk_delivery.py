import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ydisk_delivery import (
    QUARK_URL_RE,
    Credentials,
    DeliveryError,
    ShareInfo,
    append_archive,
    build_payload,
    find_rule_by_item,
    resolve_item_id,
    rule_is_healthy,
)


def _share(**overrides) -> ShareInfo:
    values = {
        "title": "WorkBuddy智能体实战，打造个人AI效率系统 37集视频课 只发夸克",
        "link": "https://pan.quark.cn/s/0123456789ab",
        "passcode": "ZZZZ",
    }
    values.update(overrides)
    return ShareInfo(**values)


class ShareInfoTests(unittest.TestCase):
    def test_accepts_well_formed_share(self):
        _share().validate()

    def test_rejects_blank_title(self):
        with self.assertRaises(DeliveryError):
            _share(title="   ").validate()

    def test_rejects_non_quark_link(self):
        for bad in (
            "https://pan.baidu.com/s/abc",
            "pan.quark.cn/s/0123456789ab",
            "https://pan.quark.cn/s/0123456789ab?pwd=ZZZZ",
            "javascript:alert(1)",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(DeliveryError):
                    _share(link=bad).validate()

    def test_passcode_must_be_four_alnum(self):
        for bad in ("abc", "abcde", "t z", "t-2p", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(DeliveryError):
                    _share(passcode=bad).validate()

    def test_url_pattern_ignores_surrounding_space(self):
        _share(link="  https://pan.quark.cn/s/0123456789ab  ").validate()
        self.assertTrue(QUARK_URL_RE.match("https://pan.quark.cn/s/abc123"))


class CredentialsTests(unittest.TestCase):
    def test_missing_env_names_are_all_reported(self):
        env = {"YDISK_BASE_URL": "https://example.test"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(DeliveryError) as ctx:
                Credentials.from_env()
        message = str(ctx.exception)
        self.assertIn("YDISK_USER", message)
        self.assertIn("YDISK_PASSWORD", message)
        self.assertNotIn("YDISK_BASE_URL", message)

    def test_trailing_slash_is_stripped(self):
        env = {
            "YDISK_BASE_URL": "https://example.test/",
            "YDISK_USER": "admin",
            "YDISK_PASSWORD": "pw",
        }
        with patch.dict(os.environ, env, clear=True):
            creds = Credentials.from_env()
        self.assertEqual(creds.base_url, "https://example.test")


class ResolveItemIdTests(unittest.TestCase):
    ITEMS = [
        {"item_id": "1001", "item_title": "剪映高级感封面预设"},
        {"item_id": "1002", "item_title": "  宣传片背景音乐合集1072首  "},
        {"item_id": "1003", "item_title": None},
    ]

    def test_exact_match_ignores_padding(self):
        self.assertEqual(
            resolve_item_id(self.ITEMS, "宣传片背景音乐合集1072首"), "1002"
        )

    def test_missing_title_is_an_error(self):
        with self.assertRaises(DeliveryError) as ctx:
            resolve_item_id(self.ITEMS, "不存在的商品")
        self.assertIn("找不到", str(ctx.exception))

    def test_duplicate_title_refuses_to_guess(self):
        items = self.ITEMS + [{"item_id": "1004", "item_title": "剪映高级感封面预设"}]
        with self.assertRaises(DeliveryError) as ctx:
            resolve_item_id(items, "剪映高级感封面预设")
        self.assertIn("多个", str(ctx.exception))

    def test_none_title_does_not_crash(self):
        with self.assertRaises(DeliveryError):
            resolve_item_id(self.ITEMS, "None")


class BuildPayloadTests(unittest.TestCase):
    def test_shape_matches_the_live_rule_contract(self):
        payload = build_payload(_share(), "1001", "123097626", 2)
        self.assertEqual(payload["item_id"], "1001")
        self.assertEqual(payload["cookie_id"], "123097626")
        self.assertEqual(payload["trigger_type"], "order_paid")
        self.assertTrue(payload["enabled"])
        self.assertEqual(payload["name"], f"自动发货-{_share().title}")
        action = payload["actions"][0]
        self.assertEqual(action["action_type"], "send_template")
        self.assertEqual(action["delivery_template_id"], 2)
        self.assertEqual(action["delivery_count"], 1)
        self.assertEqual(
            action["custom_variables"],
            {
                "title": _share().title,
                "link": _share().link,
                "code": _share().passcode,
            },
        )

    def test_title_with_pipe_does_not_break_variables(self):
        share = _share(title="少儿编程课程集合 | Scratch3.0全套214节 +")
        payload = build_payload(share, "1001", "1", 2)
        self.assertEqual(
            payload["actions"][0]["custom_variables"]["title"], share.title
        )


def _rule(**action_overrides) -> dict:
    action = {
        "action_type": "send_template",
        "enabled": True,
        "delivery_template_id": 2,
        "custom_variables": {
            "title": _share().title,
            "link": _share().link,
            "code": _share().passcode,
        },
    }
    action.update(action_overrides)
    return {
        "id": 7,
        "item_id": "1001",
        "trigger_type": "order_paid",
        "enabled": True,
        "actions": [action],
    }


class RuleHealthTests(unittest.TestCase):
    def test_matching_rule_has_no_problems(self):
        self.assertEqual(rule_is_healthy(_rule(), _share(), 2), [])

    def test_detects_wrong_link(self):
        rule = _rule()
        rule["actions"][0]["custom_variables"]["link"] = "https://pan.quark.cn/s/baaaaabbbbbb"
        self.assertIn("link-mismatch", rule_is_healthy(rule, _share(), 2))

    def test_detects_wrong_passcode(self):
        rule = _rule()
        rule["actions"][0]["custom_variables"]["code"] = "nqt5"
        self.assertIn("code-mismatch", rule_is_healthy(rule, _share(), 2))

    def test_detects_wrong_title(self):
        rule = _rule()
        rule["actions"][0]["custom_variables"]["title"] = "别的商品"
        self.assertIn("title-mismatch", rule_is_healthy(rule, _share(), 2))

    def test_detects_disabled_rule_and_action(self):
        self.assertIn(
            "rule-disabled", rule_is_healthy({**_rule(), "enabled": False}, _share(), 2)
        )
        self.assertIn(
            "action-disabled", rule_is_healthy(_rule(enabled=False), _share(), 2)
        )

    def test_detects_wrong_trigger_and_template(self):
        self.assertIn(
            "trigger=x", rule_is_healthy({**_rule(), "trigger_type": "x"}, _share(), 2)
        )
        self.assertIn(
            "template=9", rule_is_healthy(_rule(delivery_template_id=9), _share(), 2)
        )

    def test_missing_actions_short_circuits(self):
        self.assertEqual(
            rule_is_healthy({**_rule(), "actions": []}, _share(), 2), ["actions=0"]
        )

    def test_extra_action_is_flagged(self):
        rule = _rule()
        rule["actions"].append(dict(rule["actions"][0]))
        self.assertIn("actions=2", rule_is_healthy(rule, _share(), 2))

    def test_missing_custom_variables_is_flagged(self):
        rule = _rule(custom_variables=None)
        problems = rule_is_healthy(rule, _share(), 2)
        self.assertIn("title-mismatch", problems)
        self.assertIn("link-mismatch", problems)
        self.assertIn("code-mismatch", problems)


class FindRuleTests(unittest.TestCase):
    RULES = [{"id": 1, "item_id": "1001"}, {"id": 2, "item_id": 1001}]

    def test_matches_string_and_int_item_ids(self):
        self.assertEqual(find_rule_by_item(self.RULES, "1001")["id"], 1)
        self.assertEqual(find_rule_by_item(self.RULES, 1001)["id"], 1)

    def test_returns_none_when_absent(self):
        self.assertIsNone(find_rule_by_item(self.RULES, "9999"))


class ArchiveTests(unittest.TestCase):
    def test_appends_title_code_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "quark-links.txt"
            append_archive(str(path), _share())
            append_archive(str(path), _share(title="第二个商品"))
            lines = path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], f"{_share().title}|ZZZZ|{_share().link}")
        self.assertTrue(lines[1].startswith("第二个商品|"))


if __name__ == "__main__":
    unittest.main()
