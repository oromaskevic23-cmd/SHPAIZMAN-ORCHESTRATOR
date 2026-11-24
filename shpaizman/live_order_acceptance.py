"""Explicit live integration check: synthetic order, real model responses, no external actions."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from .business import ServiceFactory
from .runtime import Runtime
from .order_execution import OrderExecution

def verify(model):
    with tempfile.TemporaryDirectory(prefix="shpaizman-order-live-") as directory:
        root=Path(directory)
        business=ServiceFactory(root/"business")
        runtime=Runtime(root/"runtime")
        execution=OrderExecution(business,runtime)
        order=business.create_lead(customer_alias="Synthetic acceptance fixture",
            client_reference="test:acceptance",service="crm_pipeline",quote_minor=100,
            currency="USD",event_key="live_check_order_001",contact_consent=True)["id"]
        for index,stage in enumerate(("QUALIFIED","PROPOSED","CLIENT_APPROVED","IN_PROGRESS")):
            business.advance(order,stage,event_key="live_check_stage_%04d"%index,
                evidence_sha256=hashlib.sha256(stage.encode()).hexdigest(),
                brother_confirmed=True,external_ref="test:fixture")
        jobs=execution.schedule(order,"Design a CRM for a repair shop. Include customer_id and ticket_id. Keep the response under 100 words.")
        runtime.set_enabled(True)
        try:
            for _ in jobs:
                runtime.once(model)
        finally:
            runtime.set_enabled(False)
        result=execution.report(order)
        if result["status"]!="DRAFT_PACKAGE_READY":
            raise RuntimeError("LIVE_ORDER_INCOMPLETE")
        exported=execution.export(order,root/"draft.json")
        if business.get(order)["stage"]!="IN_PROGRESS":
            raise RuntimeError("UNAUTHORIZED_STAGE_CHANGE")
        return {"status":"LIVE_ORDER_DRAFT_EXPORTED","model":model,
                "roles":list(jobs),"job_states":{k:v["state"] for k,v in result["results"].items()},
                "package_sha256":exported["sha256"],"synthetic_order":True,
                "real_model_calls":len(jobs),"provider_connections_verified":0}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True)
    print(json.dumps(verify(p.parse_args().model),indent=2))
