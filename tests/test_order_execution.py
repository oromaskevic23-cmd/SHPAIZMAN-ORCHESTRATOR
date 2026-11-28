import hashlib
import tempfile
import unittest
from pathlib import Path
from shpaizman.business import ServiceFactory
from shpaizman.runtime import Runtime, RuntimeErrorSafe
from shpaizman.order_execution import OrderExecution

class OrderExecutionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.b=ServiceFactory(self.root/"business")
        self.r=Runtime(self.root/"runtime")
        self.x=OrderExecution(self.b,self.r)
        self.order=self.b.create_lead(customer_alias="Authorized test customer",
            client_reference="test:customer",service="crm_pipeline",quote_minor=10000,
            currency="USD",event_key="test_order_event_001",contact_consent=True)["id"]

    def approve(self):
        for n,stage in enumerate(("QUALIFIED","PROPOSED","CLIENT_APPROVED","IN_PROGRESS")):
            self.b.advance(self.order,stage,event_key="test_advance_%04d"%n,
                evidence_sha256="a"*64,brother_confirmed=True,external_ref="test:document")

    def test_unapproved_order_denied(self):
        with self.assertRaises(RuntimeErrorSafe):
            self.x.schedule(self.order,"Prepare a CRM plan")
        self.assertEqual(self.r.status()["jobs"],{})

    def test_schedule_atomic_idempotency(self):
        self.approve()
        first=self.x.schedule(self.order,"Prepare a CRM plan")
        self.assertEqual(set(first),{"bitrix24","albato"})
        self.assertEqual(first,self.x.schedule(self.order,"Prepare a CRM plan"))
        with self.assertRaises(RuntimeErrorSafe):
            self.x.schedule(self.order,"Different scope")
        self.assertEqual(self.r.status()["jobs"],{"QUEUED":2})

    def test_full_draft_package_and_no_auto_acceptance(self):
        self.approve()
        self.x.schedule(self.order,"Prepare a CRM plan")
        dest=self.root/"deliverable.json"
        with self.assertRaises(RuntimeErrorSafe):
            self.x.export(self.order,dest)
        self.r.set_enabled(True)
        while self.r.once("test",lambda model,role,task:role+" Test draft"):
            pass
        self.assertEqual(self.x.report(self.order)["status"],"DRAFT_PACKAGE_READY")
        result=self.x.export(self.order,dest)
        self.assertEqual(result["sha256"],hashlib.sha256(dest.read_bytes()).hexdigest())
        self.assertEqual(self.b.get(self.order)["stage"],"IN_PROGRESS")
        with self.assertRaises(FileExistsError):
            self.x.export(self.order,dest)

    def test_model_failure_blocks_export(self):
        self.approve()
        self.x.schedule(self.order,"Prepare a CRM plan")
        self.r.set_enabled(True)
        while self.r.once("test",lambda *args:""):
            pass
        with self.assertRaises(RuntimeErrorSafe):
            self.x.export(self.order,self.root/"no.json")
