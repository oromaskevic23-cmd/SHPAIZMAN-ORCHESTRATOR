"""Run an isolated, offline demonstration using synthetic customer data."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from .business import ServiceFactory
from .harvey_bridge import HarveyBridge, HarveyDenied


def run_demo():
    """Exercise the current local code; do not touch operator or provider data."""
    started = perf_counter()
    with TemporaryDirectory(prefix="shpaizman-demo-") as temporary:
        root = Path(temporary)
        queue = HarveyBridge(root / "queue")
        business = ServiceFactory(root / "business")
        task = queue.enqueue(
            agent="albato", provider="albato", task_type="SOLUTION_PLAN",
            title="Synthetic CRM workflow for a fictional customer",
            source_url="https://example.com/synthetic-opportunity",
            event_key="demo_queue_event_00001",
        )
        try:
            queue.cycle("albato")
        except HarveyDenied as exc:
            if str(exc) != "STOPPED_BY_DEFAULT_OR_KILL_SWITCH":
                raise
        else:
            raise RuntimeError("DEMO_STOP_BY_DEFAULT_FAILED")

        queue.set_enabled(True, local_operator_ack=True)
        draft = queue.cycle("albato")
        queue.set_enabled(False)
        try:
            queue.cycle("albato")
        except HarveyDenied as exc:
            if str(exc) != "STOPPED_BY_DEFAULT_OR_KILL_SWITCH":
                raise
        else:
            raise RuntimeError("DEMO_STOP_SWITCH_FAILED")

        # Consent and the quote below are synthetic assertions, not customer facts.
        lead = business.create_lead(
            customer_alias="Synthetic customer", client_reference="demo:fictional-client",
            service="crm_pipeline", quote_minor=10000, currency="USD",
            event_key="demo_business_lead_00001", contact_consent=True,
        )
        qualified = business.advance(
            lead["id"], "QUALIFIED", event_key="demo_business_qualify_00001",
            evidence_sha256=sha256(b"synthetic qualification evidence").hexdigest(),
        )
        queue_evidence = queue.verify()
        business_evidence = business.verification()
        if (draft["task_id"] != task["id"] or draft["processed"] != 1
                or draft["artifact"]["approval"] != "PENDING_BENEFICIARY_REVIEW"
                or qualified["stage"] != "QUALIFIED"):
            raise RuntimeError("DEMO_UNEXPECTED_RESULT")

        return {
            "schema": "shpaizman_offline_demo_v1",
            "scenario": "fictional CRM workflow; no real customer, consent or sale",
            "stop_by_default": "VERIFIED_IN_THIS_DEMO",
            "local_draft": draft["state"],
            "draft_approval": draft["artifact"]["approval"],
            "stop_after_draft": "VERIFIED_IN_THIS_DEMO",
            "synthetic_order_stage": qualified["stage"],
            "queue_ledger": queue_evidence["status"],
            "business_ledger": business_evidence["status"],
            "queue_events": queue_evidence["events"],
            "business_events": business_evidence["events"],
            "elapsed_ms": round((perf_counter() - started) * 1000, 2),
            "limitations": [
                "No AI model or external provider was called.",
                "No messages, invoices, payments or real customer actions were sent.",
                "Operator acknowledgement is not authenticated owner approval.",
                "Local hash chains do not prevent a complete database rewrite.",
                "Duration is a local measurement, not a business savings claim.",
            ],
        }


def main():
    print(json.dumps(run_demo(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
