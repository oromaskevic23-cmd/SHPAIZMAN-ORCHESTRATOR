"""Read-only SHA-256 and ZIP source-audit gate; never extract or execute archive code."""
from __future__ import annotations
import argparse,hashlib,json,re,stat,sys,zipfile
from pathlib import Path,PurePosixPath

ROOT="SHPAIZMAN_BROTHER_EDITION/"
AGENTS=("albato","aimylogic","tomoru","twin","gigachat","yandex","nodul","bitrix24","mws","cloudru")
EXEC={".py",".pyw",".exe",".dll",".pyd",".cmd",".bat",".ps1"}
BANNED={"SOURCE.git.bundle",".env",".env.local","id_rsa","id_ed25519"}
class ReleaseDenied(ValueError):pass
def digest(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()

def verify_release(path,expected_sha256):
 path=Path(path)
 if not re.fullmatch(r"[a-f0-9]{64}",expected_sha256 or ""):raise ReleaseDenied("EXTERNAL_SHA256_REQUIRED")
 if not path.is_file() or path.is_symlink() or path.stat().st_size>15_000_000:
  raise ReleaseDenied("ZIP_NOT_FOUND_OR_UNSAFE")
 if digest(path)!=expected_sha256:raise ReleaseDenied("ZIP_DIGEST_MISMATCH")
 try:z=zipfile.ZipFile(path)
 except (zipfile.BadZipFile,OSError) as e:raise ReleaseDenied("INVALID_ZIP") from e
 with z:
  info=z.infolist()
  if not 25<=len(info)<=200 or sum(i.file_size for i in info)>20_000_000:
   raise ReleaseDenied("ZIP_CAPACITY_LIMIT")
  entries={};seen=set()
  for i in info:
   if i.is_dir():continue
   name=i.filename
   if not name.startswith(ROOT) or "\\" in name or "\x00" in name or ":" in name:
    raise ReleaseDenied("UNSAFE_ARCHIVE_PATH")
   rel=name[len(ROOT):];p=PurePosixPath(rel)
   if not rel or p.is_absolute() or "." in p.parts or ".." in p.parts or len(p.parts)>9:
    raise ReleaseDenied("UNSAFE_ARCHIVE_PATH")
   if name in seen:raise ReleaseDenied("DUPLICATE_ARCHIVE_ENTRY")
   seen.add(name)
   if i.file_size>2_000_000 or (i.file_size>0 and i.compress_size==0) or (
       i.compress_size and i.file_size>max(50_000,i.compress_size*200)):
    raise ReleaseDenied("ARCHIVE_BOMB_OR_RATIO")
   if stat.S_IFMT(i.external_attr>>16)==stat.S_IFLNK:raise ReleaseDenied("ARCHIVE_SYMLINK")
   if p.name in BANNED or p.suffix in {".pem",".p12",".pfx"} or "recovered" in p.parts:
    raise ReleaseDenied("HISTORICAL_OR_SECRET_FILE")
   entries[rel]=i
  if "SHA256SUMS.txt" not in entries:raise ReleaseDenied("SHA_MANIFEST_MISSING")
  try:lines=z.read(entries["SHA256SUMS.txt"]).decode("utf-8").splitlines()
  except UnicodeError as e:raise ReleaseDenied("INVALID_SHA_MANIFEST") from e
  manifest={}
  for line in lines:
   if "  " not in line:raise ReleaseDenied("INVALID_SHA_MANIFEST")
   sha,rel=line.split("  ",1)
   p=PurePosixPath(rel)
   if not re.fullmatch(r"[a-f0-9]{64}",sha) or rel in manifest or rel=="SHA256SUMS.txt" or (
       not rel or p.is_absolute() or ".." in p.parts or rel not in entries):
    raise ReleaseDenied("INVALID_SHA_MANIFEST")
   manifest[rel]=sha
  for rel,sha in manifest.items():
   if hashlib.sha256(z.read(entries[rel])).hexdigest()!=sha:
    raise ReleaseDenied("INTERNAL_SHA256_MISMATCH")
  for rel in entries:
   if PurePosixPath(rel).suffix.lower() in EXEC and rel not in manifest:
    raise ReleaseDenied("UNLISTED_EXECUTABLE")
  required={"shpaizman/orchestrator.py","shpaizman/registry.py",
   "shpaizman/beneficiary.py","shpaizman/handover.py",
   "scripts/astra_handover.py","scripts/install.py","run.py",
   "INSTALL.cmd","START_SHPAIZMAN.cmd","tests/test_beneficiary.py",
   "tests/test_handover.py"}
  required.update("shpaizman/agents/"+agent+".py" for agent in AGENTS)
  if not required.issubset(manifest):raise ReleaseDenied("TEN_AGENT_SOURCE_INCOMPLETE")
  return {"schema":"shpaizman_source_zip_audit_v1","status":"SOURCE_INTEGRITY_VERIFIED_NOT_EXECUTED",
   "archive_sha256":expected_sha256,"files_in_manifest":len(manifest),
   "agents":len(AGENTS),"installed_on_brother_pc":False,
   "platform_connections_verified":0,"profits_verified":False,"wallet_transfers":"DISABLED"}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--zip-path",type=Path,required=True)
 p.add_argument("--expected-sha256",required=True)
 a=p.parse_args()
 try:print(json.dumps(verify_release(a.zip_path,a.expected_sha256),indent=2));return 0
 except (ReleaseDenied,ValueError,OSError) as e:
  print("BLOCKED:",str(e),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
