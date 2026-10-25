"""SHPAIZMAN Service Factory: offline, consent-gated IT service business pipeline.

No unsolicited contact, account access, invoices sent, wallet transfer,
bank verification or automatically earned income is implemented.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import uuid

PLATFORMS=("albato","aimylogic","tomoru","twin","gigachat",
           "yandex","nodul","bitrix24","mws","cloudru")
SERVICES={
 "crm_pipeline":{"name":"CRM Pipeline Setup","agents":("bitrix24","albato"),
                 "deliverables":("field_map","migration_plan","offline_acceptance_test")},
 "support_assistant":{"name":"Customer Support Knowledge Assistant",
                      "agents":("aimylogic","gigachat"),
                      "deliverables":("intent_catalog","privacy_policy","qa_dialogues")},
 "business_workflow":{"name":"Back-Office Workflow Automation",
                      "agents":("nodul","albato"),
                      "deliverables":("workflow_spec","rollback_plan","test_receipt")},
 "voice_support":{"name":"Voice Support Prototype","agents":("tomoru","twin"),
                  "deliverables":("call_flow","consent_check","offline_script_tests")},
 "ai_ops_assessment":{"name":"AI Operations Readiness Assessment",
                      "agents":("yandex","mws","cloudru"),
                      "deliverables":("architecture","cost_limits","evaluation_report")}
}
assert set(a for item in SERVICES.values() for a in item["agents"])==set(PLATFORMS)
STAGES=("LEAD","QUALIFIED","PROPOSED","CLIENT_APPROVED","IN_PROGRESS",
        "QA_PASSED","DELIVERED","CLIENT_ACCEPTED","INVOICED","SETTLEMENT_CLAIMED")
NEXT=dict(zip(STAGES,STAGES[1:]))
GATES=frozenset({"CLIENT_APPROVED","IN_PROGRESS","CLIENT_ACCEPTED",
                 "INVOICED","SETTLEMENT_CLAIMED"})
HEX=re.compile(r"^[a-f0-9]{64}$")
REF=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{5,119}$")
KEY=re.compile(r"^[A-Za-z0-9_-]{12,96}$")
CURRENCIES=frozenset({"RUB","UAH","USD","EUR"})
SECRETS=("seed phrase","private key","mnemonic","password=","api_key","secret recovery")
class BusinessDenied(ValueError):pass
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,
                                   separators=(",",":"),allow_nan=False)
def utc():return datetime.now(timezone.utc).isoformat(timespec="milliseconds")
def label(value,name,minlen=3,maxlen=160):
 if not isinstance(value,str) or not minlen<=len(value)<=maxlen or value.strip()!=value or any(ord(c)<32 for c in value):
  raise BusinessDenied("INVALID_"+name)
 if any(x in value.lower() for x in SECRETS):
  raise BusinessDenied("SECRET_MATERIAL_DENIED")
 return value

class ServiceFactory:
 """Separate bounded SQLite customer-order state machine and hash-chained ledger.

 Local hashes detect accidental or partial tampering, NOT hostile rewriting of
 the whole database or independent verification of commercial transactions.
 """
 def __init__(self,root:Path):
  root=Path(root);root.mkdir(parents=True,exist_ok=True)
  self.path=root/"service-factory.sqlite3"
  with self._db() as c:
   c.executescript("""
    CREATE TABLE IF NOT EXISTS orders(
     id TEXT PRIMARY KEY,customer_alias TEXT NOT NULL,client_reference TEXT NOT NULL,
     service TEXT NOT NULL,quote_minor INTEGER NOT NULL CHECK(quote_minor>0),
     currency TEXT NOT NULL,stage TEXT NOT NULL,created_at TEXT NOT NULL,
     updated_at TEXT NOT NULL,contact_consent TEXT NOT NULL,
     brother_approval TEXT NOT NULL DEFAULT 'NOT_VERIFIED');
    CREATE TABLE IF NOT EXISTS business_events(
     seq INTEGER PRIMARY KEY AUTOINCREMENT,event_key TEXT NOT NULL UNIQUE,
     order_id TEXT NOT NULL,previous_stage TEXT,target_stage TEXT NOT NULL,
     evidence_sha256 TEXT,external_ref TEXT,operator_assertion TEXT NOT NULL,
     occurred_at TEXT NOT NULL,prev_hash TEXT NOT NULL,
     event_hash TEXT NOT NULL UNIQUE,FOREIGN KEY(order_id) REFERENCES orders(id));
    CREATE INDEX IF NOT EXISTS orders_stage_idx ON orders(stage);
    CREATE TRIGGER IF NOT EXISTS business_events_no_update
     BEFORE UPDATE ON business_events BEGIN SELECT RAISE(ABORT,'IMMUTABLE_EVENT'); END;
    CREATE TRIGGER IF NOT EXISTS business_events_no_delete
     BEFORE DELETE ON business_events BEGIN SELECT RAISE(ABORT,'IMMUTABLE_EVENT'); END;
   """)
 @contextmanager
 def _db(self):
  c=sqlite3.connect(self.path,timeout=10,isolation_level=None)
  c.row_factory=sqlite3.Row
  c.execute("PRAGMA foreign_keys=ON")
  c.execute("PRAGMA busy_timeout=10000")
  c.execute("PRAGMA journal_mode=WAL")
  try:yield c
  finally:c.close()
 @staticmethod
 def _append(db,*,event_key,order_id,previous_stage,target_stage,
             evidence_sha256,external_ref,operator_assertion):
  prior=db.execute("SELECT event_hash FROM business_events ORDER BY seq DESC LIMIT 1").fetchone()
  data=dict(event_key=event_key,order_id=order_id,previous_stage=previous_stage,
   target_stage=target_stage,evidence_sha256=evidence_sha256,external_ref=external_ref,
   operator_assertion=operator_assertion,occurred_at=utc(),
   prev_hash=prior[0] if prior else "0"*64)
  stamp=sha256(canonical(data).encode()).hexdigest()
  db.execute("INSERT INTO business_events(event_key,order_id,previous_stage,target_stage,"
             "evidence_sha256,external_ref,operator_assertion,occurred_at,prev_hash,event_hash)"
             " VALUES (?,?,?,?,?,?,?,?,?,?)",(*data.values(),stamp))
  return stamp
 def create_lead(self,*,customer_alias,client_reference,service,
                 quote_minor,currency,event_key,contact_consent=False):
  label(customer_alias,"CUSTOMER_ALIAS",3,100)
  if not REF.fullmatch(client_reference or "") or not KEY.fullmatch(event_key or ""):
   raise BusinessDenied("BAD_EXTERNAL_REFERENCE_OR_IDEMPOTENCY_KEY")
  if service not in SERVICES:raise BusinessDenied("UNKNOWN_SERVICE")
  if type(quote_minor) is not int or not 1<=quote_minor<=10_000_000_000 or currency not in CURRENCIES:
   raise BusinessDenied("INVALID_QUOTE")
  if contact_consent is not True:raise BusinessDenied("CLIENT_CONTACT_CONSENT_REQUIRED")
  with self._db() as db:
   db.execute("BEGIN IMMEDIATE")
   existing=db.execute("SELECT o.* FROM orders o JOIN business_events e ON e.order_id=o.id "
                       "WHERE e.event_key=?",(event_key,)).fetchone()
   if existing:
    if (existing["customer_alias"],existing["client_reference"],existing["service"],
        existing["quote_minor"],existing["currency"])!=(customer_alias,client_reference,
                                                      service,quote_minor,currency):
     db.rollback();raise BusinessDenied("IDEMPOTENCY_CONFLICT")
    db.commit();return dict(existing)
   order_id=uuid.uuid4().hex;now=utc()
   db.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",
    (order_id,customer_alias,client_reference,service,quote_minor,currency,
     "LEAD",now,now,"SELF_DECLARED_CONSENT_NOT_VERIFIED","NOT_VERIFIED"))
   self._append(db,event_key=event_key,order_id=order_id,previous_stage=None,
    target_stage="LEAD",evidence_sha256=None,external_ref=client_reference,
    operator_assertion="CLIENT_CONTACT_CONSENT_SELF_DECLARED")
   db.commit()
  return self.get(order_id)
 def get(self,order_id):
  with self._db() as db:
   row=db.execute("SELECT * FROM orders WHERE id=?",(order_id,)).fetchone()
  return dict(row) if row else None
 def advance(self,order_id,target_stage,*,event_key,evidence_sha256,
             brother_confirmed=False,external_ref=None):
  if not KEY.fullmatch(event_key or "") or not HEX.fullmatch(evidence_sha256 or ""):
   raise BusinessDenied("VALID_EVENT_KEY_AND_EVIDENCE_SHA256_REQUIRED")
  if target_stage not in STAGES or target_stage=="LEAD":
   raise BusinessDenied("UNKNOWN_TARGET_STAGE")
  if external_ref is not None and not REF.fullmatch(external_ref):
   raise BusinessDenied("INVALID_EXTERNAL_REFERENCE")
  if target_stage in {"CLIENT_APPROVED","CLIENT_ACCEPTED","INVOICED","SETTLEMENT_CLAIMED"} and not external_ref:
   raise BusinessDenied("EXTERNAL_DOCUMENT_REFERENCE_REQUIRED")
  if target_stage in GATES and brother_confirmed is not True:
   raise BusinessDenied("BROTHER_LOCAL_APPROVAL_REQUIRED")
  with self._db() as db:
   db.execute("BEGIN IMMEDIATE")
   previous=db.execute("SELECT * FROM business_events WHERE event_key=?",(event_key,)).fetchone()
   if previous:
    if (previous["order_id"],previous["target_stage"],previous["evidence_sha256"],
        previous["external_ref"])!=(order_id,target_stage,evidence_sha256,external_ref):
     db.rollback();raise BusinessDenied("IDEMPOTENCY_CONFLICT")
    db.commit();return self.get(order_id)
   row=db.execute("SELECT * FROM orders WHERE id=?",(order_id,)).fetchone()
   if not row:db.rollback();raise BusinessDenied("UNKNOWN_ORDER")
   if NEXT.get(row["stage"])!=target_stage:
    db.rollback();raise BusinessDenied("ILLEGAL_BUSINESS_STAGE_TRANSITION")
   self._append(db,event_key=event_key,order_id=order_id,
    previous_stage=row["stage"],target_stage=target_stage,
    evidence_sha256=evidence_sha256,external_ref=external_ref,
    operator_assertion=("BROTHER_CONFIRMED_LOCALLY_NOT_AUTHENTICATED"
                        if brother_confirmed else "LOCAL_OPERATOR_UNVERIFIED"))
   db.execute("UPDATE orders SET stage=?,updated_at=?,brother_approval=? WHERE id=?",
    (target_stage,utc(),"SELF_ASSERTED" if brother_confirmed else row["brother_approval"],
     order_id))
   db.commit()
  return self.get(order_id)
 def verification(self):
  prior="0"*64
  with self._db() as db:
   events=db.execute("SELECT * FROM business_events ORDER BY seq").fetchall()
   stage={}
   for e in events:
    record={k:e[k] for k in ("event_key","order_id","previous_stage","target_stage",
             "evidence_sha256","external_ref","operator_assertion","occurred_at","prev_hash")}
    if record["prev_hash"]!=prior or sha256(canonical(record).encode()).hexdigest()!=e["event_hash"]:
     raise BusinessDenied("BUSINESS_EVENT_CHAIN_BROKEN")
    last=stage.get(e["order_id"])
    if last!=e["previous_stage"] or (last is not None and NEXT.get(last)!=e["target_stage"]) or (
      last is None and e["target_stage"]!="LEAD"):
     raise BusinessDenied("BUSINESS_STATE_REPLAY_MISMATCH")
    stage[e["order_id"]]=e["target_stage"]
    prior=e["event_hash"]
   orders=db.execute("SELECT id,stage FROM orders").fetchall()
   if len(orders)!=len(stage) or any(stage.get(r["id"])!=r["stage"] for r in orders):
    raise BusinessDenied("BUSINESS_ORDER_PROJECTION_TAMPERED")
  return {"status":"INTERNAL_LEDGER_CHAIN_VALID_ONLY","events":len(events),
          "head_sha256":prior,"settlement_verified":False,"wallet_transfers":"DISABLED"}
 def dashboard(self):
  self.verification()
  with self._db() as db:
   rows=db.execute("SELECT stage,currency,COUNT(*) AS n,SUM(quote_minor) AS q "
                   "FROM orders GROUP BY stage,currency").fetchall()
  return {"beneficiary":"Alexander Viktorovich","pipeline":[dict(r) for r in rows],
          "verified_received_revenue_minor":0,
          "cash_balance":"NOT_CONNECTED_TO_BANK_OR_BLOCKCHAIN",
          "quotes_are_not_cash":True,"settlement_claims_are_not_verified_receipts":True,
          "automated_wallet_transfers":"DISABLED","platform_accounts_connected":0}
