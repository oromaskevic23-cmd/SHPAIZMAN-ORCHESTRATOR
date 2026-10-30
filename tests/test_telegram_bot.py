"""No-network authorization and read-only Telegram boundary tests."""
import unittest
from unittest.mock import Mock

from shpaizman.telegram_bot import (
    TelegramAPI, TelegramError, handle_update, parse_allowed_chat_ids,
    parse_private_message, response_for_command,
)


class StubFactory:
    def __init__(self):
        self.calls = []
    def dashboard(self):
        self.calls.append("dashboard")
        return {"pipeline": [{"stage": "LEAD", "n": 2}], "verified_received_revenue_minor": 0}
    def verification(self):
        self.calls.append("verification")
        return {"status": "INTERNAL_LEDGER_CHAIN_VALID_ONLY", "events": 2}


def message(chat_id=12345678, sender=None, chat_type="private", text="/status"):
    return {"update_id": 17, "message": {
        "chat": {"id": chat_id, "type": chat_type},
        "from": {"id": sender if sender is not None else chat_id, "is_bot": False},
        "text": text,
    }}


class BotSafetyTests(unittest.TestCase):
    def test_allowlist_is_mandatory_and_numeric(self):
        for s in ("", "0", "-100123", "123,", "123,hi", "123 456"):
            with self.subTest(value=s), self.assertRaises(ValueError):
                parse_allowed_chat_ids(s)
        self.assertEqual(parse_allowed_chat_ids("12345678, 12345679"), frozenset({12345678,12345679}))

    def test_private_authorized_only(self):
        allowed = frozenset({12345678})
        self.assertEqual(parse_private_message(message(), allowed), (12345678, "/status"))
        self.assertIsNone(parse_private_message(message(chat_id=55555), allowed))
        self.assertIsNone(parse_private_message(message(chat_type="group"), allowed))
        self.assertIsNone(parse_private_message(message(sender=2222), allowed))
        self.assertIsNone(parse_private_message(message(text="/status@random_bot"), allowed))
        self.assertIsNone(parse_private_message({"callback_query": {"data": "/status"}}, allowed))

    def test_no_remote_execution_or_payment_command(self):
        api = Mock()
        factory = StubFactory()
        self.assertFalse(handle_update(api, factory, message(text="/shell del /S C:\\"), frozenset({12345678})))
        self.assertFalse(handle_update(api, factory, message(text="/pay"), frozenset({12345678})))
        self.assertEqual(api.call.call_count, 0)
        self.assertEqual(factory.calls, [])

    def test_unauthorized_chat_is_silent(self):
        api = Mock()
        factory = StubFactory()
        self.assertFalse(handle_update(api, factory, message(chat_id=9999), frozenset({12345678})))
        api.call.assert_not_called()
        self.assertFalse(factory.calls)

    def test_dashboard_and_local_integrity_are_not_real_revenue(self):
        factory = StubFactory()
        text = response_for_command("/status", factory)
        self.assertIn("Orders: 2", text)
        self.assertIn("NOT VERIFIED", text)
        self.assertNotIn("payment confirmed", text.lower())
        self.assertIn("INTERNAL_LEDGER_CHAIN_VALID_ONLY", response_for_command("/verify", factory))
        self.assertEqual(factory.calls, ["dashboard", "verification"])

    def test_token_format_and_api_method_allowlist(self):
        token = "123456789:" + "A" * 30
        api = TelegramAPI(token, opener=Mock())
        with self.assertRaisesRegex(TelegramError, "METHOD_NOT_ALLOWED"):
            api.call("deleteWebhook")
        with self.assertRaises(ValueError):
            TelegramAPI("invalid")

    def test_transport_errors_do_not_leak_token(self):
        token = "123456789:" + "A" * 30
        def fail(req, timeout):
            from urllib.error import URLError
            raise URLError(req.full_url)
        api = TelegramAPI(token, opener=fail)
        with self.assertRaises(TelegramError) as err:
            api.call("getMe")
        self.assertNotIn(token, str(err.exception))

    def test_readonly_send_replies_only_for_authorized_private_chat(self):
        api, factory = Mock(), StubFactory()
        self.assertTrue(handle_update(api, factory, message(text="/ping"), frozenset({12345678})))
        sent = api.call.call_args.args
        self.assertEqual(sent[0], "sendMessage")
        self.assertEqual(sent[1]["chat_id"], 12345678)
        self.assertEqual(factory.calls, [])


if __name__ == "__main__":
    unittest.main()
