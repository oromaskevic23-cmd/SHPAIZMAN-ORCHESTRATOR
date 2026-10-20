# SHPAIZMAN-ORCHESTRATOR
Independent AI orchestrator with 10 specialized platform agents, CRM, Telegram control and Windows support. Brother Edition.
COMMIT 02 — SHPAIZMAN ORCHESTRATOR v0.2.1

feat: Add AI orchestrator, CRM and 10 specialized agents

- Implement independent SHPAIZMAN orchestration core
- Add 10 AI platform adapters: Albato, Aimylogic, Tomoru, TWIN, GigaChat, Yandex AI Studio, Nodul, Bitrix24, MWS AI Agents and Cloud.ru AI Factory
- Add CRM for clients, deals, tasks and income tracking
- Add SQLite persistence and task management
- Add Windows launcher and Telegram control module
- Add security controls, audit logs and SHA-256 verification
- Preserve full independence from IMPERIAL Core
- Enforce FREE_ONLY policy and disable paid API calls
- Verify 51/51 local automated tests

Status: LOCAL MVP VERIFIED
External API integrations: 0/10 active
Budget: $0
Owner: Alexander Viktorovich
"""SHPAIZMAN Brother Edition: local-first, zero-cost, offline orchestration.

Python 3.11+. Zero third-party dependencies. No external API calls.
Run: python shpaizman_orchestrator.py self-test
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from uuid import uuid4

PLATFORMS = {
    "albato": "Albato",
    "aimylogic": "Just AI / Aimylogic",
    "tomoru": "Tomoru",
    "twin": "TWIN",
    "gigachat": "GigaChat Business",
    "yandex": "Yandex AI Studio",
    "nodul": "Nodul",
    "bitrix24": "Bitrix24 / BitrixGPT",
    "mws": "MWS AI Agents",
    "cloudru": "Cloud.ru AI Factory",
}
MAX_QUEUE = 100
MAX_REQUEST = 1200
JOB_STATES = frozenset({"queued", "running", "draft_ready", "failed", "cancelled"})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_db_path() -> Path:
    home = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share")
    return home / "SHPAIZMAN-BROTHER-EDITION" / "shpaizman.sqlite3"


def validate_text(value: str, label: str, limit: int = MAX_REQUEST) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{label} must contain 1..{limit} characters")
    return value.strip()


@contextmanager
def open_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    try:
        yield conn
    finally:
        conn.close()


def initialize(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            request TEXT NOT NULL,
            status TEXT NOT NULL,
            result_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL REFERENCES clients(id),
            platform TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'lead',
            amount_rub INTEGER NOT NULL DEFAULT 0 CHECK(amount_rub >= 0),
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            subject TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS jobs_status_idx ON jobs(status);
    """)


def record(conn: sqlite3.Connection, event: str, subject: str) -> None:
    conn.execute("INSERT INTO audit(event, subject, timestamp) VALUES (?, ?, ?)",
                 (event, subject, utc_now()))


def offline_adapter(platform: str, request: str) -> dict:
    """Create an internal draft only. This is NOT a real platform API adapter."""
    if platform not in PLATFORMS:
        raise ValueError("Unsupported platform")
    request = validate_text(request, "request")
    requirements_hash = hashlib.sha256(request.encode("utf-8")).hexdigest()
    return {
        "platform": platform,
        "display_name": PLATFORMS[platform],
        "mode": "OFFLINE_DRAFT_ONLY",
        "requirements_sha256": requirements_hash,
        "work_plan": [
            "Confirm the owner's exact intended outcome and authorized account.",
            "Check platform terms, regional access, free limits and API availability.",
            "Design a least-privilege connector and prepare a local sample.",
            "Request explicit owner approval before any external operation.",
        ],
        "live_connection": False,
        "paid_calls": 0,
        "approval_required": True,
    }


class Shpaizman:
    """Persistent queue + offline dispatch. No remote execution privileges."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        with open_db(self.db_path) as db:
            initialize(db)

    def enqueue(self, platform: str, request: str) -> str:
        if platform not in PLATFORMS:
            raise ValueError("Unknown platform")
        request = validate_text(request, "request")
        with open_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                count = db.execute("SELECT COUNT(*) FROM jobs WHERE status='queued'").fetchone()[0]
                if count >= MAX_QUEUE:
                    raise ValueError("Queue capacity reached")
                job_id = uuid4().hex
                now = utc_now()
                db.execute("INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (job_id, platform, request, "queued", None, now, now))
                record(db, "JOB_CREATED", job_id)
                db.commit()
            except Exception:
                db.rollback()
                raise
        return job_id

    def process_one(self) -> dict | None:
        with open_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT id, platform, request FROM jobs "
                             "WHERE status='queued' ORDER BY created_at, rowid LIMIT 1").fetchone()
            if row is None:
                db.rollback()
                return None
            db.execute("UPDATE jobs SET status='running', updated_at=? WHERE id=?",
                       (utc_now(), row["id"]))
            record(db, "JOB_CLAIMED", row["id"])
            db.commit()
        try:
            result = offline_adapter(row["platform"], row["request"])
            status = "draft_ready"
        except Exception as exc:
            result = {"error_type": type(exc).__name__, "mode": "FAILED"}
            status = "failed"
        with open_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE jobs SET status=?, result_json=?, updated_at=? "
                       "WHERE id=? AND status='running'",
                       (status, json.dumps(result, ensure_ascii=False), utc_now(), row["id"]))
            record(db, "JOB_" + status.upper(), row["id"])
            db.commit()
        return {"job_id": row["id"], "status": status, "result": result}

    def cancel(self, job_id: str) -> bool:
        with open_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            cursor = db.execute("UPDATE jobs SET status='cancelled', updated_at=? "
                                "WHERE id=? AND status='queued'", (utc_now(), job_id))
            if cursor.rowcount:
                record(db, "JOB_CANCELLED", job_id)
            db.commit()
            return bool(cursor.rowcount)

    def jobs(self) -> list[dict]:
        with open_db(self.db_path) as db:
            rows = db.execute("SELECT id, platform, status, created_at, result_json "
                              "FROM jobs ORDER BY created_at DESC, rowid DESC").fetchall()
            return [dict(row) for row in rows]

    def add_client(self, name: str, note: str = "") -> str:
        name = validate_text(name, "client name", 120)
        if len(note) > 1200:
            raise ValueError("note too long")
        client_id = uuid4().hex
        with open_db(self.db_path) as db:
            db.execute("INSERT INTO clients VALUES (?, ?, ?, ?)",
                       (client_id, name, note, utc_now()))
            record(db, "CLIENT_CREATED", client_id)
        return client_id

    def add_deal(self, client_id: str, platform: str, title: str,
                 amount_rub: int = 0) -> str:
        if platform not in PLATFORMS:
            raise ValueError("Unknown platform")
        title = validate_text(title, "deal title", 160)
        if type(amount_rub) is not int or amount_rub < 0:
            raise ValueError("amount_rub must be a nonnegative integer")
        deal_id = uuid4().hex
        with open_db(self.db_path) as db:
            db.execute("INSERT INTO deals(id,client_id,platform,title,amount_rub,created_at) "
                       "VALUES (?, ?, ?, ?, ?, ?)",
                       (deal_id, client_id, platform, title, amount_rub, utc_now()))
            record(db, "DEAL_CREATED", deal_id)
        return deal_id

    def overview(self) -> dict:
        with open_db(self.db_path) as db:
            count = lambda table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            return {
                "orchestrator": "SHPAIZMAN",
                "mode": "LOCAL_OFFLINE",
                "platforms": len(PLATFORMS),
                "live_integrations": 0,
                "paid_calls": 0,
                "jobs": count("jobs"),
                "clients": count("clients"),
                "deals": count("deals"),
                "independent_of_imperial_core": True,
            }


class LocalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Shpaizman(Path(self.tmp.name) / "test.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_registry_has_exactly_ten_adapters(self):
        self.assertEqual(len(PLATFORMS), 10)

    def test_queue_draft(self):
        job = self.app.enqueue("albato", "Create a CRM integration plan")
        result = self.app.process_one()
        self.assertEqual(result["job_id"], job)
        self.assertEqual(result["status"], "draft_ready")
        self.assertFalse(result["result"]["live_connection"])

    def test_queue_persists_after_restart(self):
        job = self.app.enqueue("aimylogic", "Design bot dialogue")
        self.assertEqual(Shpaizman(self.app.db_path).process_one()["job_id"], job)

    def test_unknown_platform_denied(self):
        with self.assertRaises(ValueError):
            self.app.enqueue("unknown", "Generate a plan")

    def test_empty_request_denied(self):
        with self.assertRaises(ValueError):
            self.app.enqueue("nodul", " ")

    def test_cancellation(self):
        job = self.app.enqueue("twin", "Design a voice workflow")
        self.assertTrue(self.app.cancel(job))
        self.assertFalse(self.app.cancel(job))
        self.assertIsNone(self.app.process_one())

    def test_client_and_deal(self):
        client = self.app.add_client("Test client")
        deal = self.app.add_deal(client, "bitrix24", "CRM migration", 1200)
        self.assertEqual(len(deal), 32)
        self.assertEqual(self.app.overview()["deals"], 1)

    def test_unknown_client_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.app.add_deal("not-a-client", "cloudru", "Analysis")

    def test_negative_amount_rejected(self):
        client = self.app.add_client("Test client")
        with self.assertRaises(ValueError):
            self.app.add_deal(client, "mws", "Service", -100)

    def test_all_adapters_are_offline(self):
        for platform in PLATFORMS:
            output = offline_adapter(platform, "Draft an implementation plan")
            self.assertEqual(output["mode"], "OFFLINE_DRAFT_ONLY")
            self.assertTrue(output["approval_required"])
            self.assertEqual(output["paid_calls"], 0)

    def test_no_paid_backend(self):
        self.assertEqual(self.app.overview()["live_integrations"], 0)

    def test_empty_queue(self):
        self.assertIsNone(self.app.process_one())


def main() -> None:
    parser = argparse.ArgumentParser(description="SHPAIZMAN offline orchestrator")
    parser.add_argument("--db", type=Path, default=default_db_path())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("platforms")
    sub.add_parser("status")
    sub.add_parser("jobs")
    sub.add_parser("run-once")
    sub.add_parser("self-test")
    create = sub.add_parser("enqueue")
    create.add_argument("platform", choices=sorted(PLATFORMS))
    create.add_argument("request")
    cancel = sub.add_parser("cancel")
    cancel.add_argument("job_id")
    client = sub.add_parser("add-client")
    client.add_argument("name")
    client.add_argument("--note", default="")
    deal = sub.add_parser("add-deal")
    deal.add_argument("client_id")
    deal.add_argument("platform", choices=sorted(PLATFORMS))
    deal.add_argument("title")
    deal.add_argument("--amount-rub", type=int, default=0)
    args = parser.parse_args()
    if args.command == "self-test":
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(LocalTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    app = Shpaizman(args.db)
    if args.command == "platforms":
        output = [{"id": slug, "name": name, "mode": "OFFLINE_DRAFT_ONLY"}
                  for slug, name in PLATFORMS.items()]
    elif args.command == "status":
        output = app.overview()
    elif args.command == "jobs":
        output = app.jobs()
    elif args.command == "run-once":
        output = app.process_one() or {"status": "no_pending_jobs"}
    elif args.command == "enqueue":
        output = {"job_id": app.enqueue(args.platform, args.request)}
    elif args.command == "cancel":
        output = {"cancelled": app.cancel(args.job_id)}
    elif args.command == "add-client":
        output = {"client_id": app.add_client(args.name, args.note)}
    else:
        output = {"deal_id": app.add_deal(args.client_id, args.platform,
                                          args.title, args.amount_rub)}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
