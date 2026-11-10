"""SHPAIZMAN HARVEY-pattern offline scout/offer queue, no external-provider access.

Founding project architect: Alexander Nikolaevich Romaskevich (RomaskevicH).
Harvey-pattern is an independently authored integration, not a vendored Harvey
runtime or evidence of authentication to external sales/AI platforms.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import ipaddress
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit
import uuid

from .business import PLATFORMS, SERVICES

# Original ten agent identities; extra technologies do not create agents.
CORE_LABELS = {
    "albato": "Albato", "aimylogic": "Just AI / Aimylogic", "tomoru": "Tomoru",
    "twin": "TWIN", "gigachat": "GigaChat Business / GigaCowork",
    "yandex": "Yandex AI Studio", "nodul": "Nodul",
    "bitrix24": "Bitrix24 / BitrixGPT", "mws": "MWS AI Agents Platform",
    "cloudru": "Cloud.ru AI Services / AI Factory",
}
assert set(CORE_LABELS) == set(PLATFORMS), "CORE_REGISTRY_DRIFT"

# Alice overview: research-only candidates, not LIVE or authenticated connectors.
# extension ID => (display label, assigned original agent, classification)
EXTENSIONS = {
    "vk_ai_space": ("VK AI Space", "mws", "enterprise_platform"),
    "gigaplatform_ai_studio": ("GigaPlatform AI Studio", "gigachat", "enterprise_platform"),
    "just_ai_agent_platform": ("Just AI Agent Platform", "aimylogic", "enterprise_platform"),
    "agentnavigator": ("AgentNavigator", "twin", "voice_platform"),
    "digital_q_gpt": ("Digital Q.GPT", "mws", "enterprise_platform"),
    "nord_clan": ("Nord Clan", "nodul", "enterprise_platform"),
    "selectel_itmo": ("Selectel × ITMO", "cloudru", "enterprise_platform"),
    "bit_agent_factory": ("BIT Agent Factory", "bitrix24", "enterprise_platform"),
    "wikibot": ("Wikibot", "aimylogic", "no_code_candidate"),
    "botman": ("BotMan", "aimylogic", "no_code_candidate"),
    "salebot": ("Salebot", "aimylogic", "no_code_candidate"),
    "bothelp": ("BotHelp", "aimylogic", "no_code_candidate"),
    "chat2desk": ("Chat2Desk", "twin", "customer_service_candidate"),
    "umnico": ("Umnico", "twin", "customer_service_candidate"),
    "livetex": ("LiveTex", "twin", "customer_service_candidate"),
    "jivo": ("Jivo", "twin", "customer_service_candidate"),
    "richat": ("Richat", "aimylogic", "no_code_candidate"),
    "tvoybot": ("TvoiBot", "aimylogic", "no_code_candidate"),
    "leadteh": ("LeadTeh", "aimylogic", "no_code_candidate"),
    "gigachain": ("GigaChain", "gigachat", "framework_candidate"),
    "maestro": ("MAESTRO", "mws", "standard_research_only"),
}
assert all(agent in PLATFORMS for _, agent, _ in EXTENSIONS.values())

TASK_TYPES = frozenset(("PROSPECT_REVIEW", "SOLUTION_PLAN", "OFFER_DRAFT"))
KEY = re.compile(r"^[A-Za-z0-9_-]{12,96}$")
SENSITIVE = ("seed phrase", "private key", "mnemonic", "api_key", "password=",
             "secret recovery", "bot token", "bearer ", "authorization:")
DAILY_LOCAL_TASK_LIMIT = 50
MAX_PENDING_PER_AGENT = 100

class HarveyDenied(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def validate_text(value, *, name, limit=240):
    if (not isinstance(value, str) or not 5 <= len(value) <= limit
            or value.strip() != value or any(ord(c) < 32 for c in value)
            or any(secret in value.lower() for secret in SENSITIVE)):
        raise HarveyDenied("INVALID_OR_SENSITIVE_" + name)
    return value


def validate_source(url):
    validate_text(url, name="SOURCE_URL", limit=512)
    try:
        parts = urlsplit(url)
        host = parts.hostname
        if (parts.scheme not in ("https", "http") or not host
                or parts.username is not None or parts.password is not None
                or parts.fragment or parts.port not in (None, 80, 443)):
            raise HarveyDenied("INVALID_PUBLIC_SOURCE_URL")
        if host.lower() in ("localhost", "localhost.localdomain") or host.endswith(".local"):
            raise HarveyDenied("NONPUBLIC_SOURCE_URL")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise HarveyDenied("NONPUBLIC_SOURCE_URL")
    except (ValueError, UnicodeError) as exc:
        raise HarveyDenied("INVALID_PUBLIC_SOURCE_URL") from exc
    return url


def catalog():
    core = {agent: {"label": CORE_LABELS[agent], "agent": agent,
                    "kind": "core_execution_technology", "status": "OFFLINE_ONLY"}
            for agent in PLATFORMS}
    extensions = {name: {"label": label, "agent": agent, "kind": kind,
                         "status": "RESEARCH_ONLY_NOT_CONNECTED"}
                  for name, (label, agent, kind) in EXTENSIONS.items()}
    return {"schema": "shpaizman_harvey_provider_catalog_v1", "core": core,
            "extensions": extensions, "live_external_connections_verified": 0,
            "paid_calls_allowed": False, "outbound_messaging_enabled": False}


class HarveyBridge:
    """Persistent bounded draft jobs per agent with a local stop switch.

    A CLI assertion is NOT an authenticated owner grant. This code cannot
    send messages, scrape sites, call models/provider APIs, operate wallets
    or establish Windows autorun.
    """
    def __init__(self, root: Path):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "harvey-bridge.sqlite3"
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS control (
                  id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL
                  CHECK(enabled IN (0,1)));
                INSERT OR IGNORE INTO control VALUES(1,0);
                CREATE TABLE IF NOT EXISTS tasks (
                  id TEXT PRIMARY KEY, event_key TEXT NOT NULL UNIQUE,
                  agent TEXT NOT NULL, provider TEXT NOT NULL,
                  task_type TEXT NOT NULL, title TEXT NOT NULL,
                  source_url TEXT NOT NULL, request_hash TEXT NOT NULL,
                  state TEXT NOT NULL CHECK(state IN ('QUEUED','DRAFT_READY')),
                  created_at TEXT NOT NULL, finished_at TEXT,
                  artifact_json TEXT);
                CREATE INDEX IF NOT EXISTS tasks_agent_state_idx
                  ON tasks(agent,state,created_at);
                CREATE TABLE IF NOT EXISTS audit (
                  seq INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_type TEXT NOT NULL, task_id TEXT NOT NULL,
                  details_sha256 TEXT NOT NULL, occurred_at TEXT NOT NULL,
                  prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL UNIQUE);
                CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
                  BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AUDIT'); END;
                CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
                  BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AUDIT'); END;
            """)

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA journal_mode=WAL")
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    def _log(db, event_type, task_id, details):
        prev = db.execute("SELECT event_hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        record = {"event_type": event_type, "task_id": task_id,
                  "details_sha256": sha256(canonical(details).encode()).hexdigest(),
                  "occurred_at": timestamp(),
                  "prev_hash": prev[0] if prev else "0" * 64}
        digest = sha256(canonical(record).encode()).hexdigest()
        db.execute("INSERT INTO audit(event_type,task_id,details_sha256,occurred_at,"
                   "prev_hash,event_hash) VALUES (?,?,?,?,?,?)",
                   (*record.values(), digest))

    def set_enabled(self, enabled: bool, *, local_operator_ack=False):
        if type(enabled) is not bool:
            raise HarveyDenied("INVALID_CONTROL_STATE")
        if enabled and local_operator_ack is not True:
            raise HarveyDenied("LOCAL_OPERATOR_ACK_REQUIRED")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE control SET enabled=? WHERE id=1", (int(enabled),))
            self._log(db, "LOCAL_RESUME" if enabled else "LOCAL_STOP", "CONTROL",
                      {"enabled": enabled, "identity_authenticated": False})
            db.commit()
        return {"local_processing_enabled": enabled,
                "external_provider_access": "DISABLED"}

    @staticmethod
    def _agent_for_provider(provider):
        if provider in CORE_LABELS:
            return provider
        if provider in EXTENSIONS:
            return EXTENSIONS[provider][1]
        raise HarveyDenied("UNKNOWN_PROVIDER")

    def enqueue(self, *, agent, provider, task_type, title, source_url, event_key):
        if agent not in PLATFORMS or self._agent_for_provider(provider) != agent:
            raise HarveyDenied("AGENT_PROVIDER_BOUNDARY_DENIED")
        if task_type not in TASK_TYPES:
            raise HarveyDenied("OFFLINE_TASK_TYPE_ONLY")
        validate_text(title, name="TASK_TITLE")
        validate_source(source_url)
        if not isinstance(event_key, str) or not KEY.fullmatch(event_key):
            raise HarveyDenied("INVALID_IDEMPOTENCY_KEY")
        details = {"agent": agent, "provider": provider, "task_type": task_type,
                   "title": title, "source_url": source_url}
        request_hash = sha256(canonical(details).encode()).hexdigest()
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM tasks WHERE event_key=?", (event_key,)).fetchone()
            if old:
                if old["request_hash"] != request_hash:
                    db.rollback()
                    raise HarveyDenied("IDEMPOTENCY_CONFLICT")
                db.commit()
                return self._summary(dict(old))
            n = db.execute("SELECT COUNT(*) FROM tasks WHERE agent=? AND state='QUEUED'",
                           (agent,)).fetchone()[0]
            if n >= MAX_PENDING_PER_AGENT:
                db.rollback()
                raise HarveyDenied("AGENT_QUEUE_LIMIT")
            task_id = uuid.uuid4().hex
            db.execute("INSERT INTO tasks(id,event_key,agent,provider,task_type,title,"
                       "source_url,request_hash,state,created_at)"
                       " VALUES (?,?,?,?,?,?,?,?,'QUEUED',?)",
                       (task_id, event_key, agent, provider, task_type, title,
                        source_url, request_hash, timestamp()))
            self._log(db, "ENQUEUED", task_id, details)
            db.commit()
        return {"id": task_id, "agent": agent, "provider": provider,
                "task_type": task_type, "state": "QUEUED"}

    @staticmethod
    def _summary(task):
        return {k: task[k] for k in ("id", "agent", "provider", "task_type", "state")}

    @staticmethod
    def _check_task_request(db, task):
        """Check the stored request against its original local audit digest."""
        details = {k: task[k] for k in ("agent", "provider", "task_type", "title", "source_url")}
        digest = sha256(canonical(details).encode()).hexdigest()
        events = db.execute("SELECT details_sha256 FROM audit WHERE event_type='ENQUEUED'"
                            " AND task_id=?", (task["id"],)).fetchall()
        if len(events) != 1 or digest != task["request_hash"] or digest != events[0][0]:
            raise HarveyDenied("LOCAL_TASK_REQUEST_TAMPERED")

    @staticmethod
    def _artifact(task):
        candidate_services = [name for name, spec in SERVICES.items()
                              if task["agent"] in spec["agents"]]
        if not candidate_services:
            raise HarveyDenied("SERVICE_FACTORY_AGENT_NOT_MAPPED")
        return {
            "schema": "shpaizman_harvey_offline_artifact_v1",
            "task_id": task["id"], "agent": task["agent"],
            "technology": task["provider"], "type": task["task_type"],
            "prospect_reference": task["source_url"],
            "opportunity_title": task["title"],
            "service_candidates": candidate_services,
            "preparation": ["Confirm the demand is genuine and publicly accessible",
                            "Check lawful customer contact permission and eligibility",
                            "Prepare a scope, estimate and proof-of-work plan",
                            "Get client and beneficiary authorization before any execution",
                            "Run independent QA before presenting a deliverable"],
            "customer_contact": "NOT_SENT",
            "provider_api_calls": 0, "paid_calls": 0,
            "approval": "PENDING_BENEFICIARY_REVIEW",
            "client_verified": False, "contract_signed": False,
            "income_verified": False, "payment_received": False,
        }

    def cycle(self, agent):
        """Process at most ONE pending offline task for this agent atomically."""
        if agent not in PLATFORMS:
            raise HarveyDenied("UNKNOWN_AGENT")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute("SELECT enabled FROM control WHERE id=1").fetchone()[0]:
                db.rollback()
                raise HarveyDenied("STOPPED_BY_DEFAULT_OR_KILL_SWITCH")
            start = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            count = db.execute("SELECT COUNT(*) FROM audit WHERE event_type='DRAFT_READY'"
                               " AND task_id IN (SELECT id FROM tasks WHERE agent=?)"
                               " AND occurred_at>=?", (agent, start)).fetchone()[0]
            if count >= DAILY_LOCAL_TASK_LIMIT:
                db.rollback()
                raise HarveyDenied("DAILY_LOCAL_AGENT_QUOTA_REACHED")
            row = db.execute("SELECT * FROM tasks WHERE agent=? AND state='QUEUED'"
                             " ORDER BY created_at,id LIMIT 1", (agent,)).fetchone()
            if not row:
                db.commit()
                return {"agent": agent, "processed": 0, "state": "IDLE"}
            task = dict(row)
            self._check_task_request(db, task)
            result = self._artifact(task)
            db.execute("UPDATE tasks SET state='DRAFT_READY',finished_at=?,"
                       "artifact_json=? WHERE id=? AND state='QUEUED'",
                       (timestamp(), canonical(result), task["id"]))
            self._log(db, "DRAFT_READY", task["id"], result)
            db.commit()
            return {"agent": agent, "processed": 1, "state": "DRAFT_READY",
                    "task_id": task["id"], "artifact": result}

    def task(self, task_id):
        if not isinstance(task_id, str) or not re.fullmatch(r"[a-f0-9]{32}", task_id):
            raise HarveyDenied("INVALID_TASK_ID")
        with self._db() as db:
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise HarveyDenied("TASK_NOT_FOUND")
        result = self._summary(dict(row))
        result["artifact"] = json.loads(row["artifact_json"]) if row["artifact_json"] else None
        return result

    def status(self):
        with self._db() as db:
            enabled = bool(db.execute("SELECT enabled FROM control WHERE id=1").fetchone()[0])
            rows = db.execute("SELECT agent,state,COUNT(*) as n FROM tasks"
                              " GROUP BY agent,state").fetchall()
        return {"schema": "shpaizman_harvey_local_status_v1",
                "local_processing_enabled": enabled,
                "agents": list(PLATFORMS),
                "counts": [dict(r) for r in rows],
                "provider_connections_verified": 0,
                "outbound_messages_sent": 0,
                "independently_verified_revenue_minor": 0,
                "always_on_server_deployed": False}

    def verify(self):
        prior = "0" * 64
        with self._db() as db:
            events = db.execute("SELECT * FROM audit ORDER BY seq").fetchall()
            for row in events:
                data = {k: row[k] for k in ("event_type", "task_id", "details_sha256",
                          "occurred_at", "prev_hash")}
                if data["prev_hash"] != prior or sha256(canonical(data).encode()).hexdigest() != row["event_hash"]:
                    raise HarveyDenied("LOCAL_AUDIT_CHAIN_BROKEN")
                prior = row["event_hash"]
            queued = {r["task_id"] for r in events if r["event_type"] == "ENQUEUED"}
            ready = {r["task_id"] for r in events if r["event_type"] == "DRAFT_READY"}
            tasks = db.execute("SELECT * FROM tasks").fetchall()
            if (len(queued) != len(tasks)
                    or len(ready) != sum(t["state"] == "DRAFT_READY" for t in tasks)
                    or any(t["id"] not in queued or
                           (t["state"] == "DRAFT_READY") != (t["id"] in ready)
                           for t in tasks)):
                raise HarveyDenied("LOCAL_TASK_PROJECTION_MISMATCH")
            digest_by_task = {r["task_id"]: r["details_sha256"]
                              for r in events if r["event_type"] == "DRAFT_READY"}
            for t in tasks:
                self._check_task_request(db, t)
                if t["state"] == "DRAFT_READY":
                    if (t["artifact_json"] is None or
                            sha256(t["artifact_json"].encode()).hexdigest() != digest_by_task[t["id"]]):
                        raise HarveyDenied("LOCAL_ARTIFACT_TAMPERED")
        return {"status": "LOCAL_AUDIT_CHAIN_VALID_NOT_EXTERNALLY_ATTESTED",
                "events": len(events), "tasks": len(tasks),
                "head_sha256": prior, "provider_connections_verified": 0}
