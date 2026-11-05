"""Deterministic, adversarial tests of the offline per-agent commercial planning bridge."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from shpaizman.business import PLATFORMS
from shpaizman.harvey_bridge import (
    HarveyBridge, HarveyDenied, catalog, EXTENSIONS, CORE_LABELS,
)


class HarveyBridgeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.bridge = HarveyBridge(self.root)

    def enqueue(self, **override):
        kwargs = dict(agent="albato", provider="albato", task_type="PROSPECT_REVIEW",
                      title="Example customer has a CRM workflow request",
                      source_url="https://example.com/opportunities/123",
                      event_key="harvey_task_00000000001")
        kwargs.update(override)
        return self.bridge.enqueue(**kwargs)

    def test_exactly_ten_core_agents_and_extension_mapping(self):
        self.assertEqual(set(CORE_LABELS), set(PLATFORMS))
        self.assertEqual(len(catalog()["core"]), 10)
        self.assertGreaterEqual(len(EXTENSIONS), 20)
        self.assertTrue(all(spec[1] in PLATFORMS for spec in EXTENSIONS.values()))
        self.assertTrue(all(v["status"] == "RESEARCH_ONLY_NOT_CONNECTED"
                            for v in catalog()["extensions"].values()))

    def test_default_stopped_and_no_external_calls(self):
        self.enqueue()
        with self.assertRaisesRegex(HarveyDenied, "STOPPED"):
            self.bridge.cycle("albato")
        self.assertEqual(self.bridge.status()["provider_connections_verified"], 0)

    def test_operator_ack_to_resume(self):
        with self.assertRaisesRegex(HarveyDenied, "ACK"):
            self.bridge.set_enabled(True)
        self.bridge.set_enabled(True, local_operator_ack=True)
        self.assertTrue(self.bridge.status()["local_processing_enabled"])

    def test_one_offline_task_per_cycle_and_persistence(self):
        first = self.enqueue()
        second = self.enqueue(title="Second independent customer request",
                              event_key="harvey_task_00000000002")
        self.bridge.set_enabled(True, local_operator_ack=True)
        result = self.bridge.cycle("albato")
        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["artifact"]["provider_api_calls"], 0)
        self.assertEqual(result["artifact"]["customer_contact"], "NOT_SENT")
        self.assertFalse(result["artifact"]["income_verified"])
        self.assertEqual(self.bridge.task(first["id"])["state"], "DRAFT_READY")
        self.assertEqual(self.bridge.task(second["id"])["state"], "QUEUED")
        reopened = HarveyBridge(self.root)
        self.assertEqual(reopened.cycle("albato")["processed"], 1)
        self.assertEqual(reopened.cycle("albato")["processed"], 0)
        self.assertEqual(reopened.verify()["tasks"], 2)

    def test_kill_switch_halts_future_cycles(self):
        self.enqueue()
        self.bridge.set_enabled(True, local_operator_ack=True)
        self.bridge.set_enabled(False)
        with self.assertRaisesRegex(HarveyDenied, "STOPPED"):
            self.bridge.cycle("albato")

    def test_each_core_agent_executes_its_own_safe_plan(self):
        for i, agent in enumerate(PLATFORMS):
            self.enqueue(agent=agent, provider=agent,
                         event_key="agent_ten_task_" + str(i).zfill(12))
        self.bridge.set_enabled(True, local_operator_ack=True)
        for agent in PLATFORMS:
            result = self.bridge.cycle(agent)
            self.assertEqual(result["processed"], 1)
            self.assertTrue(result["artifact"]["service_candidates"])
        self.assertEqual(self.bridge.verify()["tasks"], 10)

    def test_extension_routes_only_to_assigned_agent(self):
        self.enqueue(agent="gigachat", provider="gigachain")
        with self.assertRaisesRegex(HarveyDenied, "AGENT_PROVIDER_BOUNDARY"):
            self.enqueue(agent="albato", provider="gigachain",event_key="different_task_00000001")

    def test_external_action_types_rejected(self):
        for typ in ("SEND_EMAIL", "BULK_SCRAPE", "CALL_API", "PAY_INVOICE", "AUTO_TRANSFER"):
            with self.subTest(kind=typ), self.assertRaisesRegex(HarveyDenied, "OFFLINE_TASK_TYPE"):
                self.enqueue(task_type=typ)

    def test_idempotent_retries_and_conflicts(self):
        a = self.enqueue()
        b = self.enqueue()
        self.assertEqual(a["id"], b["id"])
        with self.assertRaisesRegex(HarveyDenied, "IDEMPOTENCY_CONFLICT"):
            self.enqueue(title="Changed customer request")

    def test_disallow_nonpublic_urls_and_secrets(self):
        for url in ("file:///etc/passwd", "http://localhost/private", "http://127.0.0.1/",
                    "http://10.0.0.1/private", "https://test.example/path#fragment",
                    "https://a:b@example.com/"):
            with self.subTest(url=url), self.assertRaises(HarveyDenied):
                self.enqueue(source_url=url)
        with self.assertRaises(HarveyDenied):
            self.enqueue(title="password=not-a-real-credential")

    def test_immutable_audit_and_mutation_detection(self):
        task = self.enqueue()
        self.bridge.set_enabled(True, local_operator_ack=True)
        self.bridge.cycle("albato")
        with sqlite3.connect(self.bridge.path) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("DELETE FROM audit WHERE task_id=?", (task["id"],))
            db.execute("UPDATE tasks SET artifact_json=? WHERE id=?", (json.dumps({"fake":True}), task["id"]))
        with self.assertRaisesRegex(HarveyDenied, "TAMPERED"):
            self.bridge.verify()

    def test_local_queue_limit_is_bounded(self):
        for i in range(100):
            self.enqueue(event_key="unique_event_" + str(i).zfill(12))
        with self.assertRaisesRegex(HarveyDenied, "QUEUE_LIMIT"):
            self.enqueue(event_key="unique_event_" + str(100).zfill(12))


if __name__ == "__main__":
    unittest.main()
