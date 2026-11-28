"""Connect consent-gated Service Factory orders to the real local AI worker.

Outputs are local review drafts, never executed provider actions or accepted work.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
import uuid

from .business import ServiceFactory, SERVICES, BusinessDenied
from .business_cli import local_root
from .runtime import Runtime, RuntimeErrorSafe

class OrderExecution:
    def __init__(self, business, runtime):
        self.business = business
        self.runtime = runtime
        with runtime.db() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS order_batches(
                order_id TEXT PRIMARY KEY, service TEXT NOT NULL,
                brief_hash TEXT NOT NULL, jobs_json TEXT NOT NULL)""")

    def schedule(self, order_id, brief):
        if not isinstance(order_id,str) or not re.fullmatch(r"[a-f0-9]{32}",order_id):
            raise RuntimeErrorSafe("INVALID_ORDER_ID")
        if not isinstance(brief,str) or not 1 <= len(brief.strip()) <= 8000:
            raise RuntimeErrorSafe("INVALID_BRIEF")
        if any(x in brief.lower() for x in ("seed phrase","private key","password=","api_key","bearer ")):
            raise RuntimeErrorSafe("SECRET_MATERIAL_DENIED")
        self.business.verification()
        order=self.business.get(order_id)
        if not order or order["stage"]!="IN_PROGRESS" or order["brother_approval"]!="SELF_ASSERTED":
            raise RuntimeErrorSafe("ORDER_REQUIRES_LOCALLY_APPROVED_IN_PROGRESS_STATE")
        spec=SERVICES[order["service"]]
        digest=hashlib.sha256(brief.encode()).hexdigest()
        with self.runtime.db() as c:
            c.execute("BEGIN IMMEDIATE")
            previous=c.execute("SELECT * FROM order_batches WHERE order_id=?",(order_id,)).fetchone()
            if previous:
                if previous["brief_hash"]!=digest or previous["service"]!=order["service"]:
                    raise RuntimeErrorSafe("ORDER_BATCH_CONFLICT")
                return json.loads(previous["jobs_json"])
            count=c.execute("SELECT count(*) FROM jobs WHERE state IN ('QUEUED','RUNNING')").fetchone()[0]
            if count+len(spec["agents"])>1000:
                raise RuntimeErrorSafe("QUEUE_FULL")
            jobs={}
            for agent in spec["agents"]:
                jid=uuid.uuid4().hex
                task=("Authorized local service draft. Service: "+spec["name"]+
                    "\nRequested deliverables: "+", ".join(spec["deliverables"])+
                    "\nPrepare only your role's contribution. State assumptions and verification steps. "
                    "Do not claim external execution or client acceptance.\nBrief:\n"+brief)
                c.execute("INSERT INTO jobs(id,agent,task,state,created) VALUES(?,?,?,'QUEUED',?)",
                          (jid,agent,task,time.time()))
                self.runtime.event(c,jid,"QUEUED")
                jobs[agent]=jid
            c.execute("INSERT INTO order_batches VALUES(?,?,?,?)",
                      (order_id,order["service"],digest,json.dumps(jobs,sort_keys=True)))
            return jobs

    def report(self, order_id):
        self.business.verification()
        order=self.business.get(order_id)
        if not order:
            raise RuntimeErrorSafe("UNKNOWN_ORDER")
        with self.runtime.db() as c:
            batch=c.execute("SELECT * FROM order_batches WHERE order_id=?",(order_id,)).fetchone()
        if not batch:
            raise RuntimeErrorSafe("NO_ORDER_BATCH")
        jobs=json.loads(batch["jobs_json"])
        results={}
        for agent,jid in jobs.items():
            result=self.runtime.show(jid)
            if result["agent"]!=agent:
                raise RuntimeErrorSafe("ROLE_BINDING_MISMATCH")
            results[agent]={"job_id":jid,"state":result["state"],"model":result["model"],
                           "output":result["output"],"error":result["error"]}
        complete=all(x["state"]=="DRAFT_READY" and x["output"] for x in results.values())
        return {"order_id":order_id,"service":batch["service"],"order_stage":order["stage"],
                "status":"DRAFT_PACKAGE_READY" if complete else "DRAFT_PACKAGE_NOT_READY",
                "brief_sha256":batch["brief_hash"],"results":results,
                "human_review_required":True,"external_actions_executed":False,
                "revenue_verified":False}

    def export(self, order_id, destination):
        report=self.report(order_id)
        if report["status"]!="DRAFT_PACKAGE_READY":
            raise RuntimeErrorSafe("INCOMPLETE_DRAFT_PACKAGE")
        raw=(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8")
        with Path(destination).open("xb") as f:
            f.write(raw)
        return {"path":str(destination),"sha256":hashlib.sha256(raw).hexdigest(),
                "status":"DRAFT_EXPORTED_FOR_HUMAN_REVIEW"}

def main():
    p=argparse.ArgumentParser(description="SHPAIZMAN order-to-AI execution")
    p.add_argument("--business-dir",type=Path,default=local_root())
    import os
    p.add_argument("--runtime-dir",type=Path,default=Path(os.environ.get("LOCALAPPDATA") or Path.home())/"SHPAIZMAN"/"runtime")
    sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("schedule");s.add_argument("order_id");s.add_argument("brief_file",type=Path)
    s=sub.add_parser("report");s.add_argument("order_id")
    s=sub.add_parser("export");s.add_argument("order_id");s.add_argument("destination",type=Path)
    a=p.parse_args()
    try:
        x=OrderExecution(ServiceFactory(a.business_dir),Runtime(a.runtime_dir))
        if a.command=="schedule":
            if a.brief_file.stat().st_size>32000:
                raise RuntimeErrorSafe("BRIEF_TOO_LARGE")
            result={"jobs":x.schedule(a.order_id,a.brief_file.read_text(encoding="utf-8"))}
        elif a.command=="report":
            result=x.report(a.order_id)
        else:
            result=x.export(a.order_id,a.destination)
        print(json.dumps(result,ensure_ascii=True,indent=2))
    except (RuntimeErrorSafe,BusinessDenied,OSError,UnicodeError) as exc:
        p.exit(2,str(exc)+"\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
