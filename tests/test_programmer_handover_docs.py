"""Read-only QA for published programmer documentation and release instructions."""
import hashlib
from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit,unquote

ROOT=Path(__file__).resolve().parents[1]
DOCUMENTS=[
 "README.md",
 "docs/PRESENTATION_RU.md",
 "docs/WINDOWS_DEVELOPER_SETUP_RU.md",
 "docs/RELEASE_0_8_0_RC1.md",
 "docs/PROGRAMMER_ACCEPTANCE_RU.md",
]
PIN="9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e"
class HandoverDocumentTests(unittest.TestCase):
 def test_programmer_links_resolve_inside_repository(self):
  for document in DOCUMENTS:
   path=ROOT/document
   self.assertTrue(path.is_file(),document)
   text=path.read_text(encoding="utf8")
   for target in re.findall(r"!?(?:\[[^\]]*\])\(([^)]+)\)",text):
    if target.startswith(("https://","http://","mailto:","#")):continue
    url=urlsplit(target)
    if url.scheme:continue
    dest=(path.parent / unquote(url.path)).resolve()
    with self.subTest(document=document,target=target):
     self.assertTrue(dest.is_relative_to(ROOT.resolve()))
     self.assertTrue(dest.exists(),"Missing relative documentation link: "+target)
 def test_explicit_zip_sha256_consistent(self):
  for document in ("README.md","docs/WINDOWS_DEVELOPER_SETUP_RU.md",
                   "docs/RELEASE_0_8_0_RC1.md"):
   self.assertIn(PIN,(ROOT/document).read_text(encoding="utf8"))
 def test_no_false_bundle_claims(self):
  readme=(ROOT/"README.md").read_text(encoding="utf8")
  release=(ROOT/"docs/RELEASE_0_8_0_RC1.md").read_text(encoding="utf8")
  self.assertIn("is not present in this GitHub repository",readme)
  self.assertIn("zip archive is not uploaded to this public github repository",release.lower())
  self.assertFalse((ROOT/"run.py").exists())
  self.assertFalse((ROOT/"SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip").exists())
 def test_preflight_is_read_only_and_references_present_files(self):
  script_path=ROOT/"scripts/preflight_handover.ps1"
  self.assertTrue(script_path.is_file())
  script=script_path.read_text(encoding="utf8")
  for item in ("Get-FileHash","enterprise.verify_release","PYTHON_312_TKINTER_REQUIRED",
               "SOURCE_ZIP_INTERNAL_VERIFICATION_FAILED"):
   self.assertIn(item,script)
  for pattern in (r"\bInvoke-Expression\b",r"\bStart-Process\b",
                  r"\bExpand-Archive\b",r"\bInvoke-WebRequest\b",
                  r"\bSet-ExecutionPolicy\b"):
   self.assertNotRegex(script,pattern)
  guide=(ROOT/"docs/PREFLIGHT_WINDOWS_RU.md").read_text(encoding="utf8")
  self.assertIn("PowerShell preflight",guide)
  self.assertIn("enterprise.verify_release",guide)
  self.assertIn(PIN,guide)
  verifier=(ROOT/"enterprise/verify_release.py").read_text(encoding="utf8")
  for pattern in (r"\bsubprocess\.",r"\bos\.system\(",r"\bextractall\("):
   self.assertNotRegex(verifier,pattern)
 def test_ten_agents_and_denied_external_money(self):
  import json
  obj=json.loads((ROOT/"enterprise/handover-contract.json").read_text())
  self.assertEqual(len(obj["platform_agents"]),10)
  self.assertEqual(len({a["platform"] for a in obj["platform_agents"]}),10)
  self.assertIn("AUTO_TRANSFER",obj["deny"])
  self.assertFalse(obj["paid_services_allowed"])
  self.assertFalse(obj["income_verified"])
if __name__=="__main__":unittest.main()
