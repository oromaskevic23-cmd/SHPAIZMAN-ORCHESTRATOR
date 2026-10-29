# Safe Windows pre-installation verification

The public GitHub repository contains a **read-only ZIP verifier**, not a concealed installer. The repository includes an additional [read-only PowerShell preflight](../scripts/preflight_handover.ps1). It performs local integrity and environment checks without executing the archive.

On the beneficiary's own Windows x64 machine, with Python 3.12 including Tkinter, run the available verifier from the repository root after receiving the separate ZIP from the owner:

```powershell
$SourceZip = Join-Path $env:USERPROFILE "Downloads\SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip"
py -3.12 --version
py -3.12 -c "import tkinter,sqlite3; print('Python stdlib + Tkinter: OK')"
py -3.12 -m enterprise.verify_release --zip-path "$SourceZip" --expected-sha256 "9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e"
```

This reads the ZIP and its expected SHA-256 and manifest. It does not extract the archive, install software, download packages, authorize an external account or execute code from the ZIP.

After a verified PASS, follow [the full installation instructions](WINDOWS_DEVELOPER_SETUP_RU.md). The beneficiary must separately approve extraction and installation; his Windows account, API keys and data remain under his sole control.
