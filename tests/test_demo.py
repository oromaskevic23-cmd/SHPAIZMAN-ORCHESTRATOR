"""Acceptance test for the isolated competition demonstration."""
import unittest
from unittest.mock import patch

from shpaizman.demo import run_demo


class DemoTest(unittest.TestCase):
    def test_offline_demo_exercises_stop_draft_and_audit(self):
        # A network connection attempt is a defect in this offline scenario.
        with patch("socket.socket.connect", side_effect=AssertionError("network access")):
            result = run_demo()
        self.assertEqual(result["stop_by_default"], "VERIFIED_IN_THIS_DEMO")
        self.assertEqual(result["stop_after_draft"], "VERIFIED_IN_THIS_DEMO")
        self.assertEqual(result["local_draft"], "DRAFT_READY")
        self.assertEqual(result["draft_approval"], "PENDING_BENEFICIARY_REVIEW")
        self.assertEqual(result["synthetic_order_stage"], "QUALIFIED")
        self.assertEqual(result["business_events"], 2)
        self.assertEqual(result["queue_events"], 4)
        self.assertGreaterEqual(result["elapsed_ms"], 0)


if __name__ == "__main__":
    unittest.main()
