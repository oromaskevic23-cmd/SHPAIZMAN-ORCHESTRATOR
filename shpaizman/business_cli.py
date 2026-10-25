"""Offline business service CLI. Flags are caller assertions, not authenticated owner grants."""
from __future__ import annotations
import argparse,json,os
from pathlib import Path
from .business import ServiceFactory,SERVICES,STAGES,BusinessDenied
def local_root():
 base=os.getenv("LOCALAPPDATA")
 return (Path(base) if base else Path.home()/".local"/"share")/"SHPAIZMAN-BROTHER-EDITION"
def main(argv=None):
 p=argparse.ArgumentParser(description="SHPAIZMAN local Service Factory: no network, no payments")
 p.add_argument("--data-dir",type=Path,default=local_root())
 cmds=p.add_subparsers(dest="command",required=True)
 for cmd in ("catalog","dashboard","verify"):cmds.add_parser(cmd)
 lead=cmds.add_parser("lead")
 for flag in ("customer-alias","client-reference","service","currency","event-key"):
  lead.add_argument("--"+flag,required=True)
 lead.add_argument("--quote-minor",type=int,required=True)
 lead.add_argument("--contact-consent-confirmed",action="store_true")
 adv=cmds.add_parser("advance")
 for flag in ("order-id","stage","event-key","evidence-sha256"):
  adv.add_argument("--"+flag,required=True)
 adv.add_argument("--external-ref")
 adv.add_argument("--brother-confirmed",action="store_true")
 a=p.parse_args(argv)
 if a.command=="catalog":
  obj={"schema":"shpaizman_service_catalog_v1","offers":SERVICES,
       "quotes_are_negotiated":True,"revenue_verified":False}
 else:
  business=ServiceFactory(a.data_dir)
  try:
   if a.command=="dashboard":obj=business.dashboard()
   elif a.command=="verify":obj=business.verification()
   elif a.command=="lead":
    obj=business.create_lead(customer_alias=a.customer_alias,
     client_reference=a.client_reference,service=a.service,quote_minor=a.quote_minor,
     currency=a.currency,event_key=a.event_key,
     contact_consent=a.contact_consent_confirmed)
   else:
    obj=business.advance(a.order_id,a.stage,event_key=a.event_key,
     evidence_sha256=a.evidence_sha256,external_ref=a.external_ref,
     brother_confirmed=a.brother_confirmed)
  except BusinessDenied as error:
   p.exit(2,"BLOCKED: "+str(error)+"\n")
 print(json.dumps(obj,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
