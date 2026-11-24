import unittest
from unittest.mock import patch
from shpaizman.live_acceptance import verify
from shpaizman.runtime import RuntimeErrorSafe

class LiveAcceptanceTests(unittest.TestCase):
    def test_unavailable_model_never_passes(self):
        with patch("shpaizman.runtime.local_inference",side_effect=RuntimeErrorSafe("unavailable")):
            result=verify("local")
        self.assertEqual(result["status"],"LOCAL_MODEL_CHALLENGE_FAILED")
        self.assertEqual(result["job_state"],"FAILED")
        self.assertIsNone(result["response_sha256"])
    def test_wrong_challenge_never_passes(self):
        with patch("shpaizman.runtime.local_inference",return_value="not the code"):
            result=verify("local")
        self.assertEqual(result["status"],"LOCAL_MODEL_CHALLENGE_FAILED")
    def test_matching_challenge_contract_only(self):
        with patch("shpaizman.runtime.local_inference",side_effect=lambda m,r,t:t.split()[-1]):
            result=verify("local")
        self.assertEqual(result["status"],"LOCAL_MODEL_CHALLENGE_PASSED")
        self.assertEqual(result["external_integrations_verified"],0)
        self.assertEqual(len(result["response_sha256"]),64)
