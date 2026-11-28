"""Validate the delivered archive and exercise its installer in Windows CI."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "downloads" / "SHPAIZMAN_Brother_Edition_0.9.1_Windows.zip"
SHA256 = "1d8b8aaffc07704f46095468aeffff43de4baf6714f9f98558afb2131b437c38"
PREFIX = "SHPAIZMAN_BROTHER_EDITION/"


class BrotherPackageTests(unittest.TestCase):
    def test_original_brother_zip_is_preserved(self):
        original = ROOT / "downloads" / "SHPAIZMAN_Brother_Edition_0.9.0_Windows.zip"
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),
                         "87e89f5d10db8fc4dd08dcbd325b06981183fd8c2f5903fb18ad7d7147eea789")

    def test_delivery_hash_manifest_and_entry_points(self):
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), SHA256)
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.assertIsNone(archive.testzip())
            files = archive.namelist()
            self.assertEqual(len(files), len(set(files)))
            manifest = archive.read(PREFIX + "SHA256SUMS.txt").decode().splitlines()
            expected = {PREFIX + "SHA256SUMS.txt"}
            for line in manifest:
                digest, relative = line.split("  ", 1)
                path = PREFIX + relative
                expected.add(path)
                self.assertEqual(hashlib.sha256(archive.read(path)).hexdigest(), digest, relative)
            self.assertEqual(set(files), expected)
            for name in ("INSTALL.cmd", "START_HERE_RU.txt", "START_SHPAIZMAN.cmd",
                         "PAIR_TELEGRAM.cmd", "CHECK_AI.cmd", "README.md"):
                self.assertIn(PREFIX + name, expected)

    @unittest.skipUnless(os.name == "nt", "native Windows installer, GUI and DPAPI")
    def test_install_and_run_delivered_windows_application(self):
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(), SHA256)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with zipfile.ZipFile(ARCHIVE) as archive:
                archive.extractall(root)
            source = root / PREFIX
            installed = root / "installed app"
            env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
            env.pop("PYTHONPATH", None)

            def run(cwd, *args):
                subprocess.run([sys.executable, *args], cwd=cwd, env=env, check=True, timeout=180)

            run(source, "scripts/install.py", "--destination", str(installed))
            run(installed, "scripts/verify_manifest.py")
            run(installed, "run.py", "gui-smoke", "--data-dir", str(root / "gui data"))
            run(installed, "run.py", "smoke", "--data-dir", str(root / "worker data"))
            run(installed, "-m", "unittest", "discover", "-s", "tests", "-v")
