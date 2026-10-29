# SHPAIZMAN 0.8.0 RC1 — Developer Installation and Windows Acceptance

**Repository:** https://github.com/oromaskevic23-cmd/SHPAIZMAN-ORCHESTRATOR

**This is a two-part handover.** The GitHub repository contains documentation, the offline business engine, a read-only ZIP verifier and CI. The full Windows Python application is provided as a **separate ZIP** named `SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip`. The repository does not host that ZIP, and cannot launch the full GUI by itself.

## 0. Requirements

- Windows 10/11 x64, in Alexander Viktorovich's own standard user session.
- Python 3.12 x64 with Python Launcher and Tkinter: https://www.python.org/downloads/windows/
- Git for Windows: https://git-scm.com/download/win . Alternatively obtain the public GitHub repository via **Code → Download ZIP**.
- Independently provided `SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip` and its trusted expected SHA-256 in the [release register](RELEASE_0_8_0_RC1.md).
- Docker, Hyper-V, BIOS changes, Defender disablement, paid AI APIs, dedicated GPUs and MetaMask secrets are **not required** for initial local offline tests.

**Beneficiary approval** is required before installation, account connection, outbound communications, financial actions or persistent autorun.

## 1. Obtain the repository

Open an ordinary **PowerShell** under the beneficiary's account, **not as Administrator**.

```powershell
cd "$env:USERPROFILE\Documents"
git clone https://github.com/oromaskevic23-cmd/SHPAIZMAN-ORCHESTRATOR.git
cd SHPAIZMAN-ORCHESTRATOR
py -3.12 --version
py -3.12 -c "import tkinter,sqlite3; print('Python stdlib + Tkinter: OK')"
```

If Git is unavailable, download the public repository as a ZIP and extract it under Documents. Do not provide GitHub credentials for an unauthenticated public read-only clone.

## 2. Verify the separate ZIP before extracting

Place the owner-provided ZIP in Downloads. From the root of the GitHub clone:

```powershell
$SourceZip = Join-Path $env:USERPROFILE "Downloads\SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip"
Get-FileHash -LiteralPath $SourceZip -Algorithm SHA256
py -3.12 -m enterprise.verify_release --zip-path "$SourceZip" --expected-sha256 "9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e"
```

Accept only a genuine `SOURCE_ZIP_HASHES_VERIFIED_NO_CODE_EXECUTED` or equivalent verified result from this revision. On an outer hash mismatch, **STOP** and obtain trusted replacement evidence. The stored SHA does not by itself authenticate a publisher signature.

## 3. Extract into a new folder

```powershell
$ExtractRoot = Join-Path $env:USERPROFILE "Documents\SHPAIZMAN-Source-0.8.0"
if (Test-Path -LiteralPath $ExtractRoot) { throw "Destination already exists; refusing to overwrite files." }
Expand-Archive -LiteralPath $SourceZip -DestinationPath $ExtractRoot
$App = Join-Path $ExtractRoot "SHPAIZMAN_BROTHER_EDITION"
Set-Location -LiteralPath $App
py -3.12 scripts\verify_manifest.py
```

The extracted `SHPAIZMAN_BROTHER_EDITION` should include `run.py`, `INSTALL.cmd`, `START_SHPAIZMAN.cmd`, `shpaizman/orchestrator.py`, `shpaizman/agents/`, `tests/`, `docs/` and `SHA256SUMS.txt`. If they are not present, STOP.

## 4. Perform authorized local installation

Only with explicit beneficiary consent, from the verified `$App` directory:

```powershell
.\INSTALL.cmd
```

The previously documented installer is intended to deploy under `%LOCALAPPDATA%\SHPAIZMAN-BROTHER-EDITION\app-0.8.0-rc1` without elevation or overwriting existing data. This behavior must be **verified on the actual target**; do not assume it succeeded.

```powershell
$Installed = Join-Path $env:LOCALAPPDATA "SHPAIZMAN-BROTHER-EDITION\app-0.8.0-rc1"
Set-Location -LiteralPath $Installed
.\START_SHPAIZMAN.cmd
```

No pip downloads are expected for the standard Python/Tkinter/SQLite mode. PyInstaller/EXE would be a separate build stage.

## 5. Verify local functionality before connecting accounts

```powershell
.\RUN_TESTS.cmd
py -3.12 run.py diagnostics --data-dir "$env:TEMP\shpaizman-diagnostics"
py -3.12 run.py gui-smoke --data-dir "$env:TEMP\shpaizman-gui-smoke"
py -3.12 run.py smoke --data-dir "$env:TEMP\shpaizman-agent-smoke"
py -3.12 -m shpaizman.business_cli catalog
py -3.12 -m scripts.service_factory_demo
```

Fill in the [developer acceptance record](PROGRAMMER_ACCEPTANCE_RU.md) using the actual Python and Windows versions, hashes and test logs. Verify orchestrator shutdown, SQLite restart persistence and restoration of a synthetic backup.

## 6. Connect up to ten platforms only after local acceptance

Provider-specific setup rules are reported to exist in the **separate ZIP**, under `docs/PLATFORMS_RU.md`. See the current [agent matrix](AGENT_MATRIX.md). API tokens must never be placed in GitHub, README, issue, commit or chat. The beneficiary creates each provider account himself and checks the free-plan limitations. If actions are not officially authorized, the provider remains `BLOCKED`.

## 7. Configure Telegram and payouts with consent

Create the Telegram bot only with the beneficiary's consent via the official [BotFather](https://t.me/BotFather); store its token and authorized user ID **locally**. Test `/status`, `/agents` and `/crm` with the authorized identity.

MetaMask: only the approved public receiving address and a verified supported network; never ask for the recovery phrase. The application does not automatically send funds. Business revenue is confirmed only by independent external payment records, not by CRM status.

## 8. Handover checklist

Deliver to the beneficiary: installed application folder, expected and observed ZIP hashes, local test logs, GUI and agent test evidence, a list of approved connected accounts, blocked providers, DB/backup locations and the [signed-off acceptance record](PROGRAMMER_ACCEPTANCE_RU.md). Never attach credentials, passwords or seed phrases.

**Hard boundary:** an ASTRA connection to GitHub does not authorize control of the beneficiary's PC. Installation and account setup need independently authorized local access or a developer acting under his direct consent.
