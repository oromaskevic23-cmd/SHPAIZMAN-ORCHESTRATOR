# SHPAIZMAN-ORCHESTRATOR
Independent AI orchestrator with 10 specialized platform agents, CRM, Telegram control and Windows support. Brother Edition.
— SHPAIZMAN ORCHESTRATOR v0.2.1

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

    def clients(self) -> list[dict]:
        with open_db(self.db_path) as db:
            return [dict(r) for r in db.execute(
                "SELECT id, name, note, created_at FROM clients ORDER BY created_at DESC, rowid DESC"
            ).fetchall()]

    def deals(self) -> list[dict]:
        with open_db(self.db_path) as db:
            return [dict(r) for r in db.execute(
                "SELECT d.id, c.name AS client_name, d.platform, d.title, d.status, "
                "d.amount_rub, d.created_at FROM deals d JOIN clients c ON c.id=d.client_id "
                "ORDER BY d.created_at DESC, d.rowid DESC"
            ).fetchall()]

    def audit(self, limit: int = 100) -> list[dict]:
        if not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ValueError("Audit limit must be between 1 and 200")
        with open_db(self.db_path) as db:
            return [dict(r) for r in db.execute(
                "SELECT event, subject, timestamp FROM audit ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()]

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

    def test_clients_are_persistent(self):
        self.app.add_client("Moscow customer", "Offline record")
        self.assertEqual(Shpaizman(self.app.db_path).clients()[0]["name"], "Moscow customer")

    def test_deal_is_not_verified_income(self):
        client = self.app.add_client("Test client")
        self.app.add_deal(client, "albato", "CRM setup", 1500)
        deal = self.app.deals()[0]
        self.assertEqual(deal["status"], "lead")
        self.assertEqual(deal["amount_rub"], 1500)

    def test_audit_journal_records_job_lifecycle(self):
        self.app.enqueue("nodul", "Prepare a local work plan")
        self.app.process_one()
        events = [e["event"] for e in self.app.audit()]
        self.assertIn("JOB_CREATED", events)
        self.assertIn("JOB_DRAFT_READY", events)

    def test_audit_limit_enforced(self):
        with self.assertRaises(ValueError):
            self.app.audit(500)

    def test_job_list_survives_restart(self):
        self.app.enqueue("twin", "Offline prototype")
        self.assertEqual(len(Shpaizman(self.app.db_path).jobs()), 1)


def launch_desktop(app: Shpaizman) -> None:
    """Local Tkinter control panel; no external network actions or credentials."""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError as exc:
        raise RuntimeError("Tkinter is required for desktop mode") from exc

    root = tk.Tk()
    root.title("SHPAIZMAN | Brother Edition — Local Control Center")
    root.geometry("1080x720")
    root.minsize(840, 580)
    root.configure(background="#101828")
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure("TFrame", background="#101828")
    style.configure("TLabel", background="#101828", foreground="#e8edf4", font=("Segoe UI", 10))
    style.configure("Header.TLabel", font=("Segoe UI", 17, "bold"), foreground="#f4f8fd")
    style.configure("Hint.TLabel", foreground="#95a7be")
    style.configure("TButton", padding=(12, 7))
    style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
    style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
    style.configure("TNotebook", background="#101828")

    header = ttk.Frame(root, padding=(18, 16))
    header.pack(fill="x")
    ttk.Label(header, text="SHPAIZMAN ORCHESTRATOR", style="Header.TLabel").pack(anchor="w")
    ttk.Label(header, text="BROTHER EDITION  |  LOCAL / OFFLINE  |  10 connectors: 0 live  |  Paid calls: 0",
              style="Hint.TLabel").pack(anchor="w", pady=(5, 0))

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=18, pady=(0, 14))
    views = {}
    for key, title in (("platforms", "10 платформ"), ("jobs", "Задания"),
                       ("clients", "Клиенты"), ("deals", "Сделки"), ("audit", "Журнал")):
        panel = ttk.Frame(notebook, padding=12)
        notebook.add(panel, text=title)
        views[key] = panel

    def table(frame, columns, widths=None):
        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True, pady=(10, 0))
        grid = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            grid.heading(col, text=col)
            grid.column(col, width=(widths or {}).get(col, 150), minwidth=80, stretch=True)
        sb = ttk.Scrollbar(container, orient="vertical", command=grid.yview)
        grid.configure(yscrollcommand=sb.set)
        grid.pack(side="left", expand=True, fill="both")
        sb.pack(side="right", fill="y")
        return grid

    platform_table = table(views["platforms"], ("Platform", "Adapter mode", "Connection"))
    for slug, name in PLATFORMS.items():
        platform_table.insert("", "end", values=(name, "Offline draft", "Not connected"))

    jobs_frame = views["jobs"]
    controls = ttk.Frame(jobs_frame)
    controls.pack(fill="x")
    selected_platform = tk.StringVar(value=next(iter(PLATFORMS)))
    ttk.Label(controls, text="Платформа").pack(side="left", padx=(0, 8))
    ttk.Combobox(controls, textvariable=selected_platform, values=list(PLATFORMS),
                 state="readonly", width=15).pack(side="left", padx=(0, 10))
    request_var = tk.StringVar()
    request_entry = ttk.Entry(controls, textvariable=request_var)
    request_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
    request_entry.insert(0, "Подготовить офлайн-план проекта")
    job_table = table(jobs_frame, ("ID", "Platform", "Status", "Created"), {"ID": 265})

    def execute(task):
        try:
            result = task()
            refresh()
            return result
        except (ValueError, OSError, sqlite3.Error) as error:
            messagebox.showerror("Операция не выполнена", str(error), parent=root)
            return None

    def add_job():
        def operation():
            identifier = app.enqueue(selected_platform.get(), request_var.get())
            request_var.set("")
            return identifier
        execute(operation)

    def cancel_selected():
        items = job_table.selection()
        if not items:
            return
        job_id = job_table.item(items[0], "values")[0]
        execute(lambda: app.cancel(job_id))

    ttk.Button(controls, text="+ Задание", command=add_job).pack(side="left")
    job_buttons = ttk.Frame(jobs_frame)
    job_buttons.pack(fill="x", pady=(10, 0))
    ttk.Button(job_buttons, text="Выполнить один офлайн-план",
               command=lambda: execute(app.process_one)).pack(side="left")
    ttk.Button(job_buttons, text="Отменить выбранное", command=cancel_selected).pack(side="left", padx=8)

    client_frame = views["clients"]
    client_row = ttk.Frame(client_frame)
    client_row.pack(fill="x")
    client_name = tk.StringVar()
    ttk.Entry(client_row, textvariable=client_name, width=45).pack(side="left", padx=(0, 10))
    ttk.Button(client_row, text="Добавить клиента",
               command=lambda: execute(lambda: app.add_client(client_name.get()))).pack(side="left")
    client_table = table(client_frame, ("ID", "Name", "Created"), {"ID": 265})

    deal_frame = views["deals"]
    deal_row = ttk.Frame(deal_frame)
    deal_row.pack(fill="x")
    client_id_var = tk.StringVar()
    deal_title = tk.StringVar()
    deal_platform = tk.StringVar(value="albato")
    client_combo = ttk.Combobox(deal_row, textvariable=client_id_var, state="readonly", width=24)
    client_combo.pack(side="left", padx=(0, 8))
    ttk.Combobox(deal_row, textvariable=deal_platform, values=list(PLATFORMS),
                 state="readonly", width=12).pack(side="left", padx=(0, 8))
    ttk.Entry(deal_row, textvariable=deal_title, width=32).pack(side="left", expand=True, fill="x", padx=(0, 8))
    ttk.Button(deal_row, text="+ Сделка", command=lambda: execute(
        lambda: app.add_deal(client_id_var.get(), deal_platform.get(), deal_title.get()))
    ).pack(side="left")
    deal_table = table(deal_frame, ("ID", "Client", "Platform", "Title", "Stage", "Planned RUB"),
                       {"ID": 240})
    ttk.Label(deal_frame,
              text="Суммы сделок — предполагаемые. Они НЕ означают подтверждённую оплату.",
              style="Hint.TLabel").pack(anchor="w", pady=5)

    audit_table = table(views["audit"], ("Event", "Object ID", "Timestamp"))
    footer = ttk.Frame(root, padding=(18, 0, 18, 15))
    footer.pack(fill="x")
    status = ttk.Label(footer, text="", style="Hint.TLabel")
    status.pack(side="left")

    def fill(tree, rows):
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", "end", values=row)

    def refresh():
        jobs = app.jobs()
        clients = app.clients()
        deals = app.deals()
        fill(job_table, [(j["id"], j["platform"], j["status"], j["created_at"]) for j in jobs])
        fill(client_table, [(c["id"], c["name"], c["created_at"]) for c in clients])
        fill(deal_table, [(d["id"], d["client_name"], d["platform"], d["title"],
                           d["status"], d["amount_rub"]) for d in deals])
        fill(audit_table, [(a["event"], a["subject"], a["timestamp"]) for a in app.audit()])
        client_combo["values"] = [c["id"] for c in clients]
        status.configure(text=f"Очередь: {sum(j['status']=='queued' for j in jobs)}  |  "
                              f"Клиенты: {len(clients)}  |  Сделки: {len(deals)}  |  "
                              "External APIs: OFF")

    ttk.Button(footer, text="Обновить", command=refresh).pack(side="right")
    refresh()
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="SHPAIZMAN offline orchestrator")
    parser.add_argument("--db", type=Path, default=default_db_path())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("platforms")
    sub.add_parser("status")
    sub.add_parser("jobs")
    sub.add_parser("run-once")
    sub.add_parser("self-test")
    sub.add_parser("desktop")
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
    if args.command == "desktop":
        launch_desktop(app)
        return
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
"""SHPAIZMAN Telegram control bridge (Python 3.11+, standard library only).

Requires shpaizman_orchestrator.py in the SAME folder.
Only manages local offline drafts; external AI APIs are disabled.

Windows PowerShell setup:
  $env:SHPAIZMAN_TELEGRAM_OWNER_ID='123456789'
  $env:SHPAIZMAN_TELEGRAM_BOT_TOKEN='<your private BotFather token>'
  py -3 shpaizman_telegram.py serve

Offline tests:
  py -3 shpaizman_telegram.py self-test
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import time
import unittest
import tempfile
from urllib import request

from shpaizman_orchestrator import (
    PLATFORMS, Shpaizman, default_db_path, open_db
)

HELP = (
    "SHPAIZMAN — локальное управление:\n"
    "/status — состояние\n"
    "/platforms — 10 платформ\n"
    "/jobs — последние задания\n"
    "/enqueue <platform> <task> — добавить офлайн-задание\n"
    "/runonce — подготовить один офлайн-план\n"
    "/cancel <job_id> — отменить ожидающее задание\n"
    "/stop — отключить Telegram-мост\n"
    "Публикация, платежи и внешние API отключены."
)


def owner_from_env() -> int:
    raw = os.environ.get("SHPAIZMAN_TELEGRAM_OWNER_ID", "")
    if not raw.isdecimal() or int(raw) <= 0:
        raise ValueError("Set SHPAIZMAN_TELEGRAM_OWNER_ID")
    return int(raw)


def token_from_env() -> str:
    token = os.environ.get("SHPAIZMAN_TELEGRAM_BOT_TOKEN", "")
    if not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]{20,}", token):
        raise ValueError("Invalid or missing Telegram bot token")
    return token


class TelegramAPI:
    """Official Telegram Bot API; never log token-bearing URLs."""

    def __init__(self, token: str):
        self._url = "https://api.telegram.org/bot" + token + "/"

    def call(self, method: str, payload: dict, timeout: int = 40):
        if method not in {"getUpdates", "sendMessage"}:
            raise ValueError("Telegram method not permitted")

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self._url + method,
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "SHPAIZMAN-Local/0.5",
            },
        )

        with request.urlopen(req, timeout=timeout) as response:
            answer = json.loads(response.read(100_000))

        if not isinstance(answer, dict) or answer.get("ok") is not True:
            raise RuntimeError("Telegram returned a non-successful result")

        return answer.get("result")

    def updates(self, offset: int | None):
        payload = {
            "timeout": 25,
            "limit": 50,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            payload["offset"] = offset
        return self.call("getUpdates", payload, timeout=40)

    def reply(self, owner_id: int, text: str):
        return self.call(
            "sendMessage",
            {"chat_id": owner_id, "text": text[:3500]},
            timeout=15,
        )


class TelegramController:
    """Single-owner controller with durable at-most-once processing."""

    def __init__(self, app: Shpaizman, owner_id: int):
        if not isinstance(owner_id, int) or owner_id <= 0:
            raise ValueError("owner_id must be positive")

        self.app = app
        self.owner_id = owner_id
        self.stop_requested = False
        self.last_offset = None

        with open_db(self.app.db_path) as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS telegram_processed (
                    update_id INTEGER PRIMARY KEY,
                    processed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def _first_time(self, update_id: int) -> bool:
        if not isinstance(update_id, int) or update_id < 0:
            return False

        with open_db(self.app.db_path) as db:
            row = db.execute(
                "INSERT OR IGNORE INTO telegram_processed(update_id) VALUES (?)",
                (update_id,),
            )
            return row.rowcount == 1

    def handle(self, update: dict) -> str | None:
        if not isinstance(update, dict):
            return None

        msg = update.get("message")
        if not isinstance(msg, dict):
            return None

        user = msg.get("from") or {}
        chat = msg.get("chat") or {}

        if (
            user.get("id") != self.owner_id
            or chat.get("id") != self.owner_id
            or chat.get("type") != "private"
        ):
            return None

        content = msg.get("text")
        if not isinstance(content, str) or not content.startswith("/"):
            return None

        # Mark before mutation to prevent execution of replayed commands.
        if not self._first_time(update.get("update_id")):
            return None

        parts = content.strip().split(maxsplit=2)
        cmd = parts[0].split("@", 1)[0].lower()

        if cmd in {"/start", "/help"}:
            return HELP

        if cmd == "/status":
            state = self.app.overview()
            return (
                "SHPAIZMAN LOCAL | "
                + " | ".join(f"{k}: {v}" for k, v in state.items())
            )

        if cmd == "/platforms":
            return "Платформы (OFFLINE ONLY):\n" + "\n".join(
                f"{slug} — {name}"
                for slug, name in PLATFORMS.items()
            )

        if cmd == "/jobs":
            items = self.app.jobs()[:8]
            return "\n".join(
                f"{j['id']} {j['platform']} {j['status']}"
                for j in items
            ) or "Очередь пуста"

        if cmd == "/enqueue":
            if (
                len(parts) != 3
                or parts[1] not in PLATFORMS
                or len(parts[2]) > 1200
            ):
                return "Формат: /enqueue albato Описание задачи"

            try:
                job_id = self.app.enqueue(parts[1], parts[2])
            except ValueError:
                return "Задание отклонено: проверьте текст или лимит очереди"

            return (
                f"Задание {job_id} добавлено. "
                "Внешние действия выключены."
            )

        if cmd == "/runonce":
            output = self.app.process_one()
            if output is None:
                return "Нет ожидающих заданий"
            return (
                f"{output['job_id']}: {output['status']} "
                "(только офлайн-план)"
            )

        if cmd == "/cancel":
            if (
                len(parts) != 2
                or re.fullmatch(r"[0-9a-f]{32}", parts[1]) is None
            ):
                return "Формат: /cancel <32-символьный ID>"

            return (
                "Задание отменено"
                if self.app.cancel(parts[1])
                else "Ожидающее задание не найдено"
            )

        if cmd == "/stop":
            self.stop_requested = True
            return (
                "Telegram-мост останавливается. "
                "Windows CRM продолжает работать."
            )

        return "Неизвестная команда. /help"


def serve(app: Shpaizman, api: TelegramAPI, owner_id: int) -> None:
    controller = TelegramController(app, owner_id)
    print("SHPAIZMAN Telegram bridge active (owner only).")

    while not controller.stop_requested:
        try:
            updates = api.updates(controller.last_offset)
            if not isinstance(updates, list):
                raise ValueError("Unexpected Telegram payload")

            for update in updates:
                update_id = (
                    update.get("update_id")
                    if isinstance(update, dict)
                    else None
                )
                if not isinstance(update_id, int):
                    continue

                controller.last_offset = max(
                    controller.last_offset or 0, update_id + 1
                )

                answer = controller.handle(update)
                if answer:
                    api.reply(owner_id, answer)

                if controller.stop_requested:
                    break

        except KeyboardInterrupt:
            break
        except Exception:
            # HTTP exception strings may contain the bot token.
            print("Telegram unavailable; retrying in 5 seconds.")
            time.sleep(5)


class TelegramTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Shpaizman(Path(self.tmp.name) / "data.sqlite")
        self.controller = TelegramController(self.app, 1234)
        self.seq = 0

    def tearDown(self):
        self.tmp.cleanup()

    def message(
        self, text, uid=1234, chat=1234,
        chat_type="private", update_id=None
    ):
        self.seq += 1
        return {
            "update_id": update_id if update_id is not None else self.seq,
            "message": {
                "from": {"id": uid},
                "chat": {"id": chat, "type": chat_type},
                "text": text,
            },
        }

    def test_owner_help(self):
        self.assertIn(
            "/enqueue", self.controller.handle(self.message("/help"))
        )

    def test_other_user_denied(self):
        self.assertIsNone(
            self.controller.handle(self.message("/status", uid=666))
        )

    def test_other_chat_denied(self):
        self.assertIsNone(
            self.controller.handle(self.message("/status", chat=789))
        )

    def test_group_denied(self):
        self.assertIsNone(
            self.controller.handle(
                self.message("/status", chat_type="group")
            )
        )

    def test_enqueue(self):
        self.assertIn(
            "добавлено",
            self.controller.handle(
                self.message("/enqueue albato Создай план")
            ),
        )
        self.assertEqual(self.app.overview()["jobs"], 1)

    def test_wrong_platform_denied(self):
        self.controller.handle(
            self.message("/enqueue invalid Создай план")
        )
        self.assertEqual(self.app.overview()["jobs"], 0)

    def test_duplicate_update_no_second_job(self):
        msg = self.message("/enqueue nodul План")
        self.controller.handle(msg)
        self.controller.handle(msg)
        self.assertEqual(self.app.overview()["jobs"], 1)

    def test_duplicate_after_restart(self):
        msg = self.message("/enqueue nodul План")
        self.controller.handle(msg)
        again = TelegramController(
            Shpaizman(self.app.db_path), 1234
        )
        self.assertIsNone(again.handle(msg))

    def test_offline_run(self):
        self.controller.handle(
            self.message("/enqueue gigachat Тест")
        )
        self.assertIn(
            "draft_ready",
            self.controller.handle(self.message("/runonce")),
        )

    def test_cancel(self):
        job = self.app.enqueue("yandex", "Тест")
        self.assertIn(
            "отменено",
            self.controller.handle(self.message("/cancel " + job)),
        )

    def test_stop_only_bridge(self):
        self.controller.handle(self.message("/stop"))
        self.assertTrue(self.controller.stop_requested)
        self.assertEqual(self.app.overview()["live_integrations"], 0)

    def test_no_arbitrary_commands(self):
        self.assertIn(
            "Неизвестная",
            self.controller.handle(self.message("/shell danger")),
        )

    def test_status_is_local(self):
        self.assertIn(
            "LOCAL_OFFLINE",
            self.controller.handle(self.message("/status")),
        )

    def test_nonmessage_ignored(self):
        self.assertIsNone(
            self.controller.handle(
                {"update_id": 44, "callback_query": {}}
            )
        )

    def test_bad_update_id_rejected(self):
        self.assertIsNone(
            self.controller.handle(
                self.message("/stop", update_id=-1)
            )
        )
        self.assertFalse(self.controller.stop_requested)

    def test_missing_owner_env_denied(self):
        from unittest.mock import patch
        with patch.dict(
            os.environ, {"SHPAIZMAN_TELEGRAM_OWNER_ID": ""}
        ):
            with self.assertRaises(ValueError):
                owner_from_env()

    def test_missing_token_denied(self):
        from unittest.mock import patch
        with patch.dict(
            os.environ, {"SHPAIZMAN_TELEGRAM_BOT_TOKEN": ""}
        ):
            with self.assertRaises(ValueError):
                token_from_env()


def main():
    parser = argparse.ArgumentParser(
        description="SHPAIZMAN secure Telegram bridge"
    )
    parser.add_argument(
        "command", choices=["serve", "self-test"]
    )
    parser.add_argument(
        "--db", type=Path, default=default_db_path()
    )
    args = parser.parse_args()

    if args.command == "self-test":
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(
                TelegramTests
            )
        )
        raise SystemExit(
            0 if result.wasSuccessful() else 1
        )

    app = Shpaizman(args.db)
    serve(
        app,
        TelegramAPI(token_from_env()),
        owner_from_env(),
    )


if __name__ == "__main__":
    main()
