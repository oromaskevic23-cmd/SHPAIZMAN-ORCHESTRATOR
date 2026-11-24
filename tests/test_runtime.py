"""Local worker contract tests; model calls here are deliberately mocked."""
import tempfile
import unittest
from unittest.mock import patch
from shpaizman.runtime import Runtime, ROLES, RuntimeErrorSafe

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.r=Runtime(self.tmp.name)
    def test_ten_roles(self):
        self.assertEqual(len(ROLES),10)
        self.assertEqual(len(set(ROLES.values())),10)
    def test_stopped_and_persistence(self):
        job=self.r.submit("albato","Map CRM fields")
        self.assertFalse(self.r.once("local",lambda *a: self.fail("called while stopped")))
        r=Runtime(self.tmp.name)
        self.assertEqual(r.show(job)["state"],"QUEUED")
        r.set_enabled(True)
        self.assertTrue(r.once("local",lambda *a:"field map draft"))
        self.assertEqual(r.show(job)["output"],"field map draft")
        self.assertEqual(r.show(job)["state"],"DRAFT_READY")
    def test_fail_closed(self):
        job=self.r.submit("gigachat","Draft service requirements")
        self.r.set_enabled(True)
        with patch("shpaizman.runtime.local_inference",side_effect=RuntimeErrorSafe("unavailable")):
            self.r.once("local")
        self.assertEqual(self.r.show(job)["state"],"FAILED")
        self.assertIsNone(self.r.show(job)["output"])
    def test_stop_fences_late_output(self):
        job=self.r.submit("nodul","Prepare rollback plan")
        self.r.set_enabled(True)
        def infer(*args):
            self.r.set_enabled(False)
            return "late output"
        self.r.once("local",infer)
        self.assertEqual(self.r.show(job)["state"],"INTERRUPTED")
        self.assertIsNone(self.r.show(job)["output"])
    def test_single_active_claim_and_expired_lease(self):
        self.r.set_enabled(True)
        j=self.r.submit("twin","Draft communications flow")
        k=self.r.submit("mws","Draft agent policy")
        claim=self.r.claim("local")
        self.assertIsNone(self.r.claim("local"))
        with self.r.db() as c:
            c.execute("UPDATE jobs SET lease=0 WHERE id=?",(j,))
        self.assertEqual(self.r.claim("local")["id"],k)
        self.assertEqual(self.r.show(j)["state"],"INTERRUPTED")
        self.assertFalse(self.r.finish(claim,output="stale"))
    def test_reject_unknown_role(self):
        with self.assertRaises(RuntimeErrorSafe):
            self.r.submit("unknown","test")
    def test_empty_output_not_success(self):
        j=self.r.submit("cloudru","Draft cost controls")
        self.r.set_enabled(True)
        self.r.once("local",lambda *a:" ")
        self.assertEqual(self.r.show(j)["state"],"FAILED")

if __name__=="__main__":
    unittest.main()
