"""
单元测试，使用 unittest.mock 模拟 HTTP 请求，不真实调用飞书 API。
用法：
    cd feishu-bot-action
    pip install requests pytest
    pytest tests/ -v
"""
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# 将 src/ 加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.sign import gen_sign
from bot.card_builder import build_simple_card, build_template_card, build_text_message
from bot.webhook import send_message
from bitable.bitable import append_row, update_row


# ─── core/sign.py ────────────────────────────────────────────────────────────

class TestSign(unittest.TestCase):
    def test_returns_timestamp_and_signature(self):
        ts, sig = gen_sign("test_key", timestamp=1700000000)
        self.assertEqual(ts, 1700000000)
        self.assertIsInstance(sig, str)
        self.assertGreater(len(sig), 0)

    def test_same_input_same_output(self):
        ts1, sig1 = gen_sign("key", timestamp=12345)
        ts2, sig2 = gen_sign("key", timestamp=12345)
        self.assertEqual(sig1, sig2)

    def test_different_key_different_sig(self):
        _, sig1 = gen_sign("key_a", timestamp=12345)
        _, sig2 = gen_sign("key_b", timestamp=12345)
        self.assertNotEqual(sig1, sig2)

    def test_auto_timestamp(self):
        ts, sig = gen_sign("key")
        self.assertIsNotNone(ts)
        self.assertIsInstance(sig, str)


# ─── bot/card_builder.py ─────────────────────────────────────────────────────

class TestCardBuilder(unittest.TestCase):
    def test_text_message_structure(self):
        msg = build_text_message("hello")
        self.assertEqual(msg["msg_type"], "text")
        self.assertEqual(msg["content"]["text"], "hello")

    def test_simple_card_structure(self):
        card = build_simple_card(title="标题", content="正文")
        self.assertEqual(card["msg_type"], "interactive")
        self.assertIn("card", card)
        header = card["card"]["header"]
        self.assertEqual(header["title"]["content"], "标题")
        self.assertEqual(header["template"], "blue")

    def test_simple_card_custom_color(self):
        card = build_simple_card("t", "c", color="green")
        self.assertEqual(card["card"]["header"]["template"], "green")

    def test_template_card_structure(self):
        card = build_template_card(
            template_id="AAqke123",
            template_variable={"title": "test"},
        )
        self.assertEqual(card["msg_type"], "interactive")
        data = card["card"]["data"]
        self.assertEqual(data["template_id"], "AAqke123")
        self.assertEqual(data["template_variable"]["title"], "test")


# ─── bot/webhook.py ──────────────────────────────────────────────────────────

class TestSendMessage(unittest.TestCase):
    def _mock_post(self, return_value=None):
        """返回一个 patch context manager，模拟 webhook_post。"""
        return patch(
            "bot.webhook.webhook_post",
            return_value=return_value or {"StatusCode": 0},
        )

    def test_send_text(self):
        with self._mock_post() as mock_post:
            send_message("https://fake.url", "text", "hello")
            payload = mock_post.call_args[0][1]
            self.assertEqual(payload["msg_type"], "text")
            self.assertEqual(payload["content"]["text"], "hello")

    def test_send_interactive_simple_json(self):
        content = json.dumps({"title": "标题", "content": "正文"})
        with self._mock_post() as mock_post:
            send_message("https://fake.url", "interactive", content)
            payload = mock_post.call_args[0][1]
            self.assertEqual(payload["msg_type"], "interactive")

    def test_send_interactive_template(self):
        content = json.dumps({
            "template_id": "AAqke123",
            "template_variable": {"key": "val"},
        })
        with self._mock_post() as mock_post:
            send_message("https://fake.url", "interactive", content)
            payload = mock_post.call_args[0][1]
            self.assertEqual(payload["card"]["type"], "template")

    def test_send_interactive_fallback_plain_text(self):
        """纯字符串（非 JSON）降级为 simple card。"""
        with self._mock_post() as mock_post:
            send_message("https://fake.url", "interactive", "这是纯文本内容")
            payload = mock_post.call_args[0][1]
            self.assertEqual(payload["msg_type"], "interactive")

    def test_sign_injected_when_key_provided(self):
        with self._mock_post() as mock_post:
            send_message("https://fake.url", "text", "hi", sign_key="secret")
            payload = mock_post.call_args[0][1]
            self.assertIn("timestamp", payload)
            self.assertIn("sign", payload)

    def test_no_sign_when_key_empty(self):
        with self._mock_post() as mock_post:
            send_message("https://fake.url", "text", "hi", sign_key="")
            payload = mock_post.call_args[0][1]
            self.assertNotIn("sign", payload)

    def test_invalid_msg_type_raises(self):
        with self.assertRaises(ValueError):
            send_message("https://fake.url", "unknown_type", "hi")


# ─── bitable/bitable.py ──────────────────────────────────────────────────────

class TestBitable(unittest.TestCase):
    def _mock_auth(self):
        return patch("bitable.bitable.get_tenant_access_token", return_value="fake_token")

    def _mock_api_post(self, record_id="rec_abc123"):
        return patch(
            "bitable.bitable.api_post",
            return_value={"code": 0, "data": {"record": {"record_id": record_id}}},
        )

    def _mock_api_patch(self, record_id="rec_abc123"):
        return patch(
            "bitable.bitable.api_patch",
            return_value={"code": 0, "data": {"record": {"record_id": record_id}}},
        )

    def test_append_row_returns_record_id(self):
        with self._mock_auth(), self._mock_api_post("rec_new_123") as mock_post:
            rid = append_row("app_id", "secret", "app_token", "tbl_id", {"列A": "值1"})
            self.assertEqual(rid, "rec_new_123")
            # 验证请求体中有 fields
            payload = mock_post.call_args[0][2]
            self.assertEqual(payload["fields"]["列A"], "值1")

    def test_append_row_api_path(self):
        with self._mock_auth(), self._mock_api_post() as mock_post:
            append_row("id", "sec", "MY_TOKEN", "MY_TABLE", {})
            path = mock_post.call_args[0][0]
            self.assertIn("MY_TOKEN", path)
            self.assertIn("MY_TABLE", path)

    def test_update_row_returns_record_id(self):
        with self._mock_auth(), self._mock_api_patch("rec_upd_456") as mock_patch:
            rid = update_row("id", "sec", "tok", "tbl", "rec_upd_456", {"状态": "完成"})
            self.assertEqual(rid, "rec_upd_456")
            payload = mock_patch.call_args[0][2]
            self.assertEqual(payload["fields"]["状态"], "完成")


if __name__ == "__main__":
    unittest.main(verbosity=2)
