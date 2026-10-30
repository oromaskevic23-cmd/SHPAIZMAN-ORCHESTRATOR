"""Read-only, locally operated Telegram interface for SHPAIZMAN Service Factory.

No remote shell, customer records, agent execution, approvals, payments, or
messages to customers. Standard library only; secrets never enter Git history.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib import error, request

from .business import SERVICES, BusinessDenied, ServiceFactory
from .business_cli import local_root

API_BASE = "https://api.telegram.org/bot"
PRIVATE_COMMANDS = frozenset({"/start", "/help", "/ping", "/status", "/services", "/verify"})


class TelegramError(RuntimeError):
    """Sanitized error (never includes the Bot API URL or credentials)."""


def parse_allowed_chat_ids(raw: str) -> frozenset[int]:
    """Explicit positive numeric private-chat ID allowlist; no permissive fallback."""
    if not raw or not raw.strip():
        raise ValueError("SHPAIZMAN_TELEGRAM_CHAT_IDS_REQUIRED")
    parts = raw.split(",")
    if any(not re.fullmatch(r"[1-9][0-9]{0,19}", part.strip()) for part in parts):
        raise ValueError("INVALID_CHAT_ID_ALLOWLIST")
    return frozenset(int(part.strip()) for part in parts)


class TelegramAPI:
    def __init__(self, token: str, *, opener=None):
        if not token or not re.fullmatch(r"[0-9]{6,15}:[A-Za-z0-9_-]{20,}", token):
            raise ValueError("BOT_TOKEN_MISSING_OR_INVALID_FORMAT")
        self._token = token
        self._opener = opener or request.urlopen

    def call(self, method: str, payload: dict | None = None, *, timeout: int = 30):
        if method not in {"getMe", "getWebhookInfo", "getUpdates", "sendMessage"}:
            raise TelegramError("METHOD_NOT_ALLOWED")
        data = json.dumps(payload or {}, separators=(",", ":")).encode("utf-8")
        req = request.Request(
            API_BASE + self._token + "/" + method,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener(req, timeout=timeout) as response:
                body = response.read(1_000_001)
            if len(body) > 1_000_000:
                raise TelegramError("RESPONSE_TOO_LARGE")
            obj = json.loads(body)
            if not isinstance(obj, dict) or obj.get("ok") is not True:
                raise TelegramError("BOT_API_REJECTED_REQUEST")
            return obj.get("result")
        except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError):
            # urllib errors may embed /bot<TOKEN>/... in their text: never log them.
            raise TelegramError("BOT_API_UNAVAILABLE_OR_INVALID_CREDENTIALS") from None


def assert_polling_available(api: TelegramAPI) -> None:
    info = api.call("getWebhookInfo")
    if not isinstance(info, dict) or info.get("url"):
        raise TelegramError("WEBHOOK_PRESENT_OR_STATUS_UNKNOWN__DO_NOT_OVERWRITE")


def parse_private_message(update: object, allowed: frozenset[int]) -> tuple[int, str] | None:
    if not isinstance(update, dict):
        return None
    msg = update.get("message")
    if not isinstance(msg, dict):
        return None
    chat, user = msg.get("chat"), msg.get("from")
    if not isinstance(chat, dict) or not isinstance(user, dict):
        return None
    chat_id, user_id = chat.get("id"), user.get("id")
    if chat.get("type") != "private" or type(chat_id) is not int or type(user_id) is not int:
        return None
    if chat_id != user_id or chat_id not in allowed or user.get("is_bot") is True:
        return None
    command = msg.get("text")
    if not isinstance(command, str):
        return None
    command = command.strip().split(maxsplit=1)[0].lower() if command.strip() else ""
    # Commands addressed to an unknown @bot username are intentionally ignored.
    if "@" in command:
        return None
    return (chat_id, command)


def response_for_command(command: str, factory: ServiceFactory) -> str | None:
    if command == "/ping":
        return "SHPAIZMAN: bot process is responding. This is not a Windows or NCA health check."
    if command in {"/start", "/help"}:
        return (
            "SHPAIZMAN — read-only operator channel\n"
            "/ping — bot responsiveness\n"
            "/status — local Service Factory dashboard\n"
            "/services — available IT service packages\n"
            "/verify — local audit-chain integrity\n"
            "No remote execution, approvals, payments, or customer-data access."
        )
    if command == "/services":
        return "IT service catalog (offers, not sales):\n" + "\n".join(
            f"• {item['name']} [{code}]" for code, item in SERVICES.items()
        )
    if command == "/status":
        status = factory.dashboard()
        stages = status["pipeline"]
        total = sum(int(row["n"]) for row in stages)
        by_stage = ", ".join(f"{row['stage']}={row['n']}" for row in stages) or "none"
        return (
            "SHPAIZMAN — local Service Factory\n"
            f"Orders: {total}\nStages: {by_stage}\n"
            "Verified received revenue: NOT CONNECTED / NOT VERIFIED\n"
            "Provider accounts: NOT VERIFIED\n"
            "Agent execution: NOT VERIFIED\n"
            "Telegram: read-only; no owner approval through chat"
        )
    if command == "/verify":
        result = factory.verification()
        return (
            "Local audit replay: " + str(result["status"]) + "\n"
            f"Events: {result['events']}\n"
            "External verification, cash settlement and Windows operations: NOT VERIFIED"
        )
    return None


def handle_update(api: TelegramAPI, factory: ServiceFactory, update: object,
                  allowed: frozenset[int]) -> bool:
    parsed = parse_private_message(update, allowed)
    if not parsed:
        return False
    chat_id, command = parsed
    if command not in PRIVATE_COMMANDS:
        return False
    try:
        reply = response_for_command(command, factory)
    except (BusinessDenied, OSError, ValueError, KeyError):
        reply = "BLOCKED: local verification unavailable. No action was executed."
    if reply:
        api.call("sendMessage", {"chat_id": chat_id, "text": reply, "disable_notification": True}, timeout=15)
        return True
    return False


def discover_private_chat_ids(api: TelegramAPI) -> int:
    """Local one-time inspection; never sends messages or grants authority."""
    assert_polling_available(api)
    updates = api.call("getUpdates", {"timeout": 3, "limit": 100, "allowed_updates": ["message"]}, timeout=12)
    found: set[int] = set()
    for u in updates if isinstance(updates, list) else []:
        msg = u.get("message", {}) if isinstance(u, dict) else {}
        chat = msg.get("chat", {}) if isinstance(msg, dict) else {}
        sender = msg.get("from", {}) if isinstance(msg, dict) else {}
        if (isinstance(chat, dict) and isinstance(sender, dict)
                and chat.get("type") == "private" and type(chat.get("id")) is int
                and chat["id"] == sender.get("id") and msg.get("text") == "/start"):
            found.add(chat["id"])
    if found:
        print("Candidate private Telegram IDs for /start messages (verify the owner):")
        for chat_id in sorted(found):
            print(chat_id)
    else:
        print("NO_CHAT_ID_FOUND: send /start to the bot in Telegram, then retry.")
    return 0


def run(api: TelegramAPI, factory: ServiceFactory, allowed: frozenset[int]) -> int:
    assert_polling_available(api)
    who = api.call("getMe")
    if not isinstance(who, dict) or who.get("is_bot") is not True:
        raise TelegramError("BOT_AUTHENTICATION_NOT_CONFIRMED")
    print("SHPAIZMAN Telegram poller started (authorized private chats only; read-only).", flush=True)
    offset: int | None = None
    while True:
        payload = {"timeout": 20, "limit": 50, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset
        try:
            updates = api.call("getUpdates", payload, timeout=30)
            if not isinstance(updates, list):
                raise TelegramError("INVALID_UPDATE_RESPONSE")
            for update in updates:
                if not isinstance(update, dict) or type(update.get("update_id")) is not int:
                    continue
                offset = max(offset or 0, update["update_id"] + 1)
                handle_update(api, factory, update, allowed)
        except TelegramError:
            # Never log exception details; Telegram errors may contain sensitive URLs.
            print("Bot API request failed (details suppressed); retrying.", file=sys.stderr, flush=True)
            time.sleep(5)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="SHPAIZMAN private read-only Telegram control panel")
    parser.add_argument("--data-dir", type=Path, default=local_root())
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Validate bot token/webhook without launching")
    modes.add_argument("--discover-chat-ids", action="store_true", help="Locally display IDs that sent /start")
    args = parser.parse_args(argv)
    try:
        api = TelegramAPI(os.environ.get("SHPAIZMAN_TELEGRAM_BOT_TOKEN", ""))
        if args.check:
            assert_polling_available(api)
            result = api.call("getMe")
            if not isinstance(result, dict) or result.get("is_bot") is not True:
                raise TelegramError("BOT_AUTHENTICATION_NOT_CONFIRMED")
            print("BOT_TOKEN_VALID; POLLING_AVAILABLE; NOT YET CONNECTED TO WINDOWS")
            return 0
        if args.discover_chat_ids:
            return discover_private_chat_ids(api)
        allowed = parse_allowed_chat_ids(os.environ.get("SHPAIZMAN_TELEGRAM_CHAT_IDS", ""))
        return run(api, ServiceFactory(args.data_dir), allowed)
    except (TelegramError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("SHPAIZMAN Telegram poller stopped locally.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
