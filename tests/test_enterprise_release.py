"""Adversarial tests for read-only archive inspection. No code from ZIP runs."""
import hashlib,tempfile,unittest,zipfile
from pathlib import Path
from enterprise.verify_release import AGENTS,ReleaseDenied,verify_release
PREFIX="SHPAIZMAN_BROTHER_EDITION/"
def fixture(p,*,tamper=False,dup=False,traversal=False,missing=False):
 paths=["shpaizman/orchestrator.py","shpaizman/registry.py","shpaizman/beneficiary.py",
  "shpaizman/handover.py","scripts/astra_handover.py","scripts/install.py","run.py",
  "INSTALL.cmd","START_SHPAIZMAN.cmd","tests/test_beneficiary.py","tests/test_handover.py"]
 paths+=["shpaizman/agents/"+x+".py" for x in AGENTS]
 paths+=["docs/example"+str(i)+".md" for i in range(8)]
 if missing:paths.remove("shpaizman/agents/albato.py")
 manifest=[]
 with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as z:
  for path in paths:
   data=("synthetic:"+path).encode()
   z.writestr(PREFIX+path,data)
   manifest.append(hashlib.sha256(data).hexdigest()+"  "+path)
  z.writestr(PREFIX+"SHA256SUMS.txt","\n".join(manifest)+"\n")
  if tamper:z.writestr(PREFIX+"evil.py",b"unlisted executable")
  if dup:z.writestr(PREFIX+"run.py",b"duplicate")
  if traversal:z.writestr(PREFIX+"../escape.py",b"traversal")
 return hashlib.sha256(p.read_bytes()).hexdigest()
class VerificationTests(unittest.TestCase):
 def inspect(self,**kwargs):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"source.zip"
   return verify_release(p,fixture(p,**kwargs))
 def test_valid_source_archive(self):
  report=self.inspect()
  self.assertEqual(report["agents"],10)
  self.assertEqual(report["wallet_transfers"],"DISABLED")
 def test_external_sha_mismatch(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"source.zip";fixture(p)
   with self.assertRaisesRegex(ReleaseDenied,"ZIP_DIGEST_MISMATCH"):
    verify_release(p,"0"*64)
 def test_duplicate_member_rejected(self):
  with self.assertRaisesRegex(ReleaseDenied,"DUPLICATE_ARCHIVE_ENTRY"):self.inspect(dup=True)
 def test_traversal_rejected(self):
  with self.assertRaisesRegex(ReleaseDenied,"UNSAFE_ARCHIVE_PATH"):self.inspect(traversal=True)
 def test_unlisted_executable_rejected(self):
  with self.assertRaisesRegex(ReleaseDenied,"UNLISTED_EXECUTABLE"):self.inspect(tamper=True)
 def test_missing_agent_rejected(self):
  with self.assertRaisesRegex(ReleaseDenied,"TEN_AGENT_SOURCE_INCOMPLETE"):self.inspect(missing=True)
 def test_missing_external_digest_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"source.zip";fixture(p)
   with self.assertRaisesRegex(ReleaseDenied,"EXTERNAL_SHA256_REQUIRED"):
    verify_release(p,"")
