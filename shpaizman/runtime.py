"""SHPAIZMAN local AI worker. No simulated results, no external actions."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import urllib.request
import uuid

ROLES = {
    "albato": "Integration engineer: produce field mappings and integration plans.",
    "aimylogic": "Conversational AI engineer: produce dialogue flows and acceptance cases.",
    "tomoru": "Voice automation engineer: prepare consent-aware voice scripts.",
    "twin": "Communications engineer: produce communication workflow specifications.",
    "gigachat": "Language AI engineer: analyze requirements and draft text deliverables.",
    "yandex": "Model engineer: design model evaluation and request specifications.",
    "nodul": "Workflow engineer: design workflows and rollback plans.",
    "bitrix24": "CRM engineer: design lead schemas and CRM migration plans.",
    "mws": "Enterprise AI engineer: prepare agent policies and evaluation plans.",
    "cloudru": "Cloud engineer: prepare architecture and cost-control assessments.",
}
ENDPOINT = "http://127.0.0.1:11434/api/chat"
MAX_RESPONSE = 1024 * 1024
LEASE_SECONDS = 180

class RuntimeErrorSafe(Exception):
    pass

def local_inference(model, role, task):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", model):
        raise RuntimeErrorSafe("INVALID_MODEL")
    payload = {"model": model, "stream": False,
        "messages": [{"role": "system", "content": role + " Produce a concrete draft deliverable. Do not claim to have performed external actions."},
                     {"role": "user", "content": task}],
        "options": {"num_predict": 2048}}
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
          headers={"Content-Type": "application/json"}, method="POST")
    try:
        with opener.open(req, timeout=60) as resp:
            raw = resp.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise RuntimeErrorSafe("RESPONSE_TOO_LARGE")
        data = json.loads(raw)
        result = data["message"]["content"]
        if data.get("done") is not True or not isinstance(result, str) or not result.strip():
            raise RuntimeErrorSafe("INVALID_MODEL_RESPONSE")
        return result
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise RuntimeErrorSafe("LOCAL_MODEL_UNAVAILABLE_OR_INVALID_RESPONSE") from exc

class Runtime:
    def __init__(self, root):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "working-runtime.sqlite3"
        with self.db() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS control(id INTEGER PRIMARY KEY CHECK(id=1),
                enabled INTEGER NOT NULL, epoch INTEGER NOT NULL);
            INSERT OR IGNORE INTO control VALUES(1,0,0);
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, agent TEXT NOT NULL,
                task TEXT NOT NULL, state TEXT NOT NULL, token TEXT, epoch INTEGER,
                lease REAL, model TEXT, output TEXT, error TEXT, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, job_id TEXT,
                event TEXT NOT NULL, at REAL NOT NULL);
            """)
    @contextmanager
    def db(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        try:
            with c:
                yield c
        finally:
            c.close()
    @staticmethod
    def event(c, job, event):
        c.execute("INSERT INTO events(job_id,event,at) VALUES(?,?,?)",(job,event,time.time()))
    def set_enabled(self, enabled):
        with self.db() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("UPDATE control SET enabled=?,epoch=epoch+1 WHERE id=1",(int(enabled),))
            c.execute("UPDATE jobs SET state='INTERRUPTED',error='CONTROL_CHANGED',token=NULL WHERE state='RUNNING'")
            self.event(c,None,"ENABLED" if enabled else "STOPPED")
    def submit(self, agent, task):
        if agent not in ROLES or not isinstance(task,str) or not 1 <= len(task.strip()) <= 12000:
            raise RuntimeErrorSafe("INVALID_TASK")
        job = uuid.uuid4().hex
        with self.db() as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT count(*) FROM jobs WHERE state IN ('QUEUED','RUNNING')").fetchone()[0] >= 1000:
                raise RuntimeErrorSafe("QUEUE_FULL")
            c.execute("INSERT INTO jobs(id,agent,task,state,created) VALUES(?,?,?,'QUEUED',?)",
                      (job,agent,task,time.time()))
            self.event(c,job,"QUEUED")
        return job
    def claim(self, model):
        with self.db() as c:
            c.execute("BEGIN IMMEDIATE")
            expired = c.execute("SELECT id FROM jobs WHERE state='RUNNING' AND lease<=?",(time.time(),)).fetchall()
            for row in expired:
                c.execute("UPDATE jobs SET state='INTERRUPTED',error='LEASE_EXPIRED',token=NULL WHERE id=?",(row["id"],))
                self.event(c,row["id"],"INTERRUPTED")
            ctl = c.execute("SELECT * FROM control WHERE id=1").fetchone()
            if not ctl["enabled"] or c.execute("SELECT 1 FROM jobs WHERE state='RUNNING'").fetchone():
                return None
            job = c.execute("SELECT * FROM jobs WHERE state='QUEUED' ORDER BY created,id LIMIT 1").fetchone()
            if not job:
                return None
            token = uuid.uuid4().hex
            c.execute("UPDATE jobs SET state='RUNNING',token=?,epoch=?,lease=?,model=? WHERE id=?",
                      (token,ctl["epoch"],time.time()+LEASE_SECONDS,model,job["id"]))
            self.event(c,job["id"],"RUNNING")
            return dict(job,token=token,epoch=ctl["epoch"])
    def finish(self, job, output=None, error=None):
        with self.db() as c:
            c.execute("BEGIN IMMEDIATE")
            ctl = c.execute("SELECT * FROM control WHERE id=1").fetchone()
            if not ctl["enabled"] or ctl["epoch"] != job["epoch"]:
                return False
            state = "FAILED" if error else "DRAFT_READY"
            changed = c.execute("""UPDATE jobs SET state=?,output=?,error=?,token=NULL
                WHERE id=? AND token=? AND state='RUNNING' AND lease>?""",
                (state,output,error,job["id"],job["token"],time.time())).rowcount
            if changed:
                self.event(c,job["id"],state)
            return bool(changed)
    def once(self, model, infer=None):
        job = self.claim(model)
        if job is None:
            return False
        try:
            output = (infer or local_inference)(model,ROLES[job["agent"]],job["task"])
            if not isinstance(output,str) or not output.strip() or len(output.encode()) > MAX_RESPONSE:
                raise RuntimeErrorSafe("INVALID_OUTPUT")
        except Exception:
            self.finish(job,error="MODEL_EXECUTION_FAILED")
        else:
            self.finish(job,output=output)
        return True
    def status(self):
        with self.db() as c:
            ctl = dict(c.execute("SELECT enabled,epoch FROM control").fetchone())
            counts = {r[0]:r[1] for r in c.execute("SELECT state,count(*) FROM jobs GROUP BY state")}
            return {"enabled":bool(ctl["enabled"]),"epoch":ctl["epoch"],"jobs":counts,
                    "agent_roles":list(ROLES),"provider_connections_verified":0}
    def show(self, job):
        with self.db() as c:
            row=c.execute("SELECT id,agent,task,state,model,output,error FROM jobs WHERE id=?",(job,)).fetchone()
            if row is None:
                raise RuntimeErrorSafe("JOB_NOT_FOUND")
            return dict(row)

def main():
    p=argparse.ArgumentParser(description="SHPAIZMAN real local AI draft worker")
    p.add_argument("--data-dir",default=str(Path(os.environ.get("LOCALAPPDATA") or Path.home())/"SHPAIZMAN"/"runtime"))
    sub=p.add_subparsers(dest="command",required=True)
    for command in ("status","enable","stop"):
        sub.add_parser(command)
    s=sub.add_parser("submit");s.add_argument("agent",choices=ROLES);s.add_argument("task")
    s=sub.add_parser("show");s.add_argument("id")
    for command in ("once","serve"):
        s=sub.add_parser(command);s.add_argument("--model",required=True)
    a=p.parse_args()
    r=Runtime(a.data_dir)
    try:
        if a.command in ("enable","stop"):
            r.set_enabled(a.command=="enable")
            result=r.status()
        elif a.command=="status":
            result=r.status()
        elif a.command=="submit":
            result={"job_id":r.submit(a.agent,a.task)}
        elif a.command=="show":
            result=r.show(a.id)
        elif a.command=="once":
            result={"processed":r.once(a.model),"status":r.status()}
        else:
            while True:
                if not r.once(a.model):
                    time.sleep(2)
        print(json.dumps(result,ensure_ascii=True,indent=2))
    except KeyboardInterrupt:
        return 0
    except RuntimeErrorSafe as exc:
        p.exit(2,str(exc)+"\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
