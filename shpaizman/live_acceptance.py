"""Opt-in acceptance: exercise the real loopback model, never a mock fallback."""
import argparse
import hashlib
import json
import secrets
import tempfile
from .runtime import Runtime

def verify(model):
    challenge=secrets.token_hex(8)
    with tempfile.TemporaryDirectory(prefix="shpaizman-live-check-") as folder:
        r=Runtime(folder)
        job=r.submit("gigachat","Return exactly this verification code: "+challenge)
        r.set_enabled(True)
        try:
            r.once(model)
            result=r.show(job)
        finally:
            r.set_enabled(False)
        output=result["output"] or ""
        ok=result["state"]=="DRAFT_READY" and challenge in output
        return {"status":"LOCAL_MODEL_CHALLENGE_PASSED" if ok else "LOCAL_MODEL_CHALLENGE_FAILED",
                "model":model,"job_state":result["state"],
                "challenge_matched":challenge in output,
                "response_sha256":hashlib.sha256(output.encode()).hexdigest() if output else None,
                "external_integrations_verified":0,
                "scope":"Loopback model challenge only; not provider or production certification"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True)
    a=p.parse_args()
    result=verify(a.model)
    print(json.dumps(result,indent=2))
    return 0 if result["status"]=="LOCAL_MODEL_CHALLENGE_PASSED" else 1

if __name__=="__main__":
    raise SystemExit(main())
