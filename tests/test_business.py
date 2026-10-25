"""Test customer delivery workflow, revenue claims and hostile state changes offline."""
import hashlib,sqlite3,tempfile,unittest
from pathlib import Path
from shpaizman.business import BusinessDenied,ServiceFactory,SERVICES,STAGES
def sha(x):return hashlib.sha256(x.encode()).hexdigest()
def key(x):return "enterprise_business_event_"+str(x).zfill(5)
class ServiceFactoryTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  self.db=ServiceFactory(Path(self.t.name));self.i=0
 def lead(self,**kwargs):
  x=dict(customer_alias="DEMO customer",client_reference="DEMO-REF-001",
    service="crm_pipeline",quote_minor=50000,currency="RUB",
    event_key=key(0),contact_consent=True);x.update(kwargs)
  return self.db.create_lead(**x)
 def step(self,order,stage,**kwargs):
  self.i+=1
  x=dict(event_key=key(self.i),evidence_sha256=sha(stage),
    brother_confirmed=stage in {"CLIENT_APPROVED","IN_PROGRESS",
     "CLIENT_ACCEPTED","INVOICED","SETTLEMENT_CLAIMED"})
  if stage in ("CLIENT_APPROVED","CLIENT_ACCEPTED","INVOICED","SETTLEMENT_CLAIMED"):
   x["external_ref"]="EVIDENCE-REF-001"
  x.update(kwargs);return self.db.advance(order,stage,**x)
 def test_service_catalog_covers_ten_real_agent_roles(self):
  self.assertEqual(len({a for v in SERVICES.values() for a in v["agents"]}),10)
 def test_zero_real_verified_revenue_in_empty_business(self):
  self.assertEqual(self.db.dashboard()["verified_received_revenue_minor"],0)
 def test_contact_without_permission_fails_closed(self):
  with self.assertRaises(BusinessDenied):self.lead(contact_consent=False)
 def test_zero_negative_nonint_price_blocked(self):
  for n in (-1,0,True,1.2):
   with self.subTest(quote=n),self.assertRaises(BusinessDenied):
    self.lead(quote_minor=n)
 def test_unknown_service_or_currency_rejected(self):
  for a in (dict(service="unknown"),dict(currency="CRYPTO")):
   with self.assertRaises(BusinessDenied):self.lead(**a)
 def test_wallet_secret_not_recordable_in_alias(self):
  with self.assertRaises(BusinessDenied):self.lead(customer_alias="seed phrase fake")
 def test_lead_idempotent(self):
  a=self.lead();b=self.lead()
  self.assertEqual(a["id"],b["id"])
  self.assertEqual(self.db.verification()["events"],1)
 def test_idempotency_conflicts_blocked(self):
  self.lead()
  with self.assertRaisesRegex(BusinessDenied,"IDEMPOTENCY"):
   self.lead(quote_minor=999999)
 def test_no_skipping_signed_contract_and_qa(self):
  a=self.lead()
  with self.assertRaisesRegex(BusinessDenied,"ILLEGAL"):
   self.step(a["id"],"INVOICED")
 def test_full_stages_no_real_cash_even_if_claimed(self):
  a=self.lead()
  for stage in STAGES[1:]:
   a=self.step(a["id"],stage)
   self.assertEqual(a["stage"],stage)
  self.assertEqual(self.db.verification()["events"],len(STAGES))
  self.assertEqual(self.db.dashboard()["verified_received_revenue_minor"],0)
  self.assertEqual(self.db.dashboard()["automated_wallet_transfers"],"DISABLED")
 def test_brother_local_approval_needed_for_contract(self):
  a=self.lead()
  self.step(a["id"],"QUALIFIED");self.step(a["id"],"PROPOSED")
  with self.assertRaisesRegex(BusinessDenied,"BROTHER_LOCAL_APPROVAL_REQUIRED"):
   self.step(a["id"],"CLIENT_APPROVED",brother_confirmed=False)
 def test_client_approval_document_ref_is_required(self):
  a=self.lead()
  self.step(a["id"],"QUALIFIED");self.step(a["id"],"PROPOSED")
  with self.assertRaisesRegex(BusinessDenied,"EXTERNAL_DOCUMENT_REFERENCE_REQUIRED"):
   self.step(a["id"],"CLIENT_APPROVED",external_ref=None)
 def test_evidence_sha256_required(self):
  a=self.lead()
  with self.assertRaisesRegex(BusinessDenied,"EVIDENCE_SHA256_REQUIRED"):
   self.step(a["id"],"QUALIFIED",evidence_sha256="PASS")
 def test_retry_stage_idempotent(self):
  a=self.lead();self.step(a["id"],"QUALIFIED")
  b=self.db.advance(a["id"],"QUALIFIED",event_key=key(1),evidence_sha256=sha("QUALIFIED"))
  self.assertEqual(b["stage"],"QUALIFIED")
  self.assertEqual(self.db.verification()["events"],2)
 def test_duplicate_stage_key_for_different_target_denied(self):
  a=self.lead();self.step(a["id"],"QUALIFIED")
  with self.assertRaisesRegex(BusinessDenied,"IDEMPOTENCY"):
   self.db.advance(a["id"],"PROPOSED",event_key=key(1),evidence_sha256=sha("PROPOSED"))
 def test_immutable_journal_update_delete_rejected(self):
  a=self.lead()
  with sqlite3.connect(self.db.path) as conn:
   with self.assertRaises(sqlite3.IntegrityError):
    conn.execute("UPDATE business_events SET target_stage='INVOICED' WHERE order_id=?",(a["id"],))
   with self.assertRaises(sqlite3.IntegrityError):
    conn.execute("DELETE FROM business_events WHERE order_id=?",(a["id"],))
 def test_mutated_orders_table_detected_by_reprojection(self):
  a=self.lead()
  with sqlite3.connect(self.db.path) as conn:
   conn.execute("UPDATE orders SET stage='INVOICED' WHERE id=?",(a["id"],))
  with self.assertRaisesRegex(BusinessDenied,"TAMPERED"):
   self.db.verification()
 def test_event_hash_chain_rewrite_detected(self):
  self.lead()
  with sqlite3.connect(self.db.path) as conn:
   conn.execute("DROP TRIGGER business_events_no_update")
   conn.execute("UPDATE business_events SET event_hash=?",("0"*64,))
  with self.assertRaisesRegex(BusinessDenied,"BROKEN"):self.db.verification()
 def test_unknown_order_denied(self):
  with self.assertRaises(BusinessDenied):self.step("unknown","QUALIFIED")
 def test_reopen_persists_without_replaying_any_jobs(self):
  a=self.lead();self.step(a["id"],"QUALIFIED")
  other=ServiceFactory(Path(self.t.name))
  self.assertEqual(other.get(a["id"])["stage"],"QUALIFIED")
  self.assertEqual(other.verification()["events"],2)
