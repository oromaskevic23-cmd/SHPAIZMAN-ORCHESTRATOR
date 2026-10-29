# SHPAIZMAN 0.8.0 RC1 — Windows developer setup

**Repository:** https://github.com/oromaskevic23-cmd/SHPAIZMAN-ORCHESTRATOR

**Two-part handover:** this repository contains documentation, an offline business core, SHA/ZIP verifier and CI. The full Windows Python program is supplied **in a separate archive**, `SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip`. The developer must obtain it from its owner. GitHub does not currently provide the full executable GUI source bundle, so this README alone cannot install that application.

## 0. Requirements

- Windows 10/11 x64, using the beneficiary Alexander Viktorovich's ordinary user session.
- Python 3.12 x64, Python Launcher and Tcl/Tk: https://www.python.org/downloads/windows/ .
- Git for Windows: https://git-scm.com/download/win , or use GitHub **Code → Download ZIP** for the public repository.
- A separately supplied `SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip` and its independently confirmed SHA-256 listed in [package register](RELEASE_0_8_0_RC1.md).
- Initial offline checks do not require Docker, Hyper-V, BIOS modification, Defender disablement, paid AI APIs, GPU or MetaMask secrets.

**The beneficiary's explicit approval** is required before installation, account connections, outbound messaging, financial activity and permanent auto-start.

## 1. Clone the public repository

Use the beneficiary's ordinary PowerShell session, **not Run as Administrator**:

```powershell
cd "$env:USERPROFILE\Documents"
git clone https://github.com/oromaskevic23-cmd/SHPAIZMAN-ORCHESTRATOR.git
cd SHPAIZMAN-ORCHESTRATOR
py -3.12 --version
py -3.12 -c "import tkinter,sqlite3; print('Python stdlib + Tkinter: OK')"
```

If Git is unavailable, download the public repository from GitHub and extract the repository archive into Documents. No GitHub password is necessary for a public read-only clone.

## 2. Verify the separate Windows archive **before extraction**

Put the owner-supplied ZIP in Downloads, then at the repository root run:

```powershell
$SourceZip = Join-Path $env:USERPROFILE "Downloads\SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip"
Get-FileHash -LiteralPath $SourceZip -Algorithm SHA256
py -3.12 -m enterprise.verify_release --zip-path "$SourceZip" --expected-sha256 "9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e"
```

Expect `SOURCE_ZIP_HASHES_VERIFIED_NO_CODE_EXECUTED` (or equivalent verified status for the exact revision). On mismatch, **STOP** and verify the source through a trusted channel. A GitHub-published checksum does not independently establish file authorship or replace a signed publisher certificate.

## 3. Extract into a fresh directory and verify again

```powershell
$ExtractRoot = Join-Path $env:USERPROFILE "Documents\SHPAIZMAN-Source-0.8.0"
if (Test-Path -LiteralPath $ExtractRoot) { throw "Destination exists: overwriting is prohibited." }
Expand-Archive -LiteralPath $SourceZip -DestinationPath $ExtractRoot
$App = Join-Path $ExtractRoot "SHPAIZMAN_BROTHER_EDITION"
Set-Location -LiteralPath $App
py -3.12 scripts\verify_manifest.py
```

Verify that the extracted archive actually contains `run.py`, `INSTALL.cmd`, `START_SHPAIZMAN.cmd`, `shpaizman/orchestrator.py`, `shpaizman/agents/`, `tests/`, `docs/` and `SHA256SUMS.txt`.

## 4. Install locally only after authorization

From `$App`, after the beneficiary approves installation:

```powershell
.\INSTALL.cmd
```

The expected installer creates a separate version under `%LOCALAPPDATA%\SHPAIZMAN-BROTHER-EDITION\app-0.8.0-rc1`. It should not require administrator rights or overwrite existing application data. On an error, inspect `docs/INSTALL_RU.md` **inside the separate ZIP**. Do not automatically remove earlier installed versions.

```powershell
$Installed = Join-Path $env:LOCALAPPDATA "SHPAIZMAN-BROTHER-EDITION\app-0.8.0-rc1"
Set-Location -LiteralPath $Installed
.\START_SHPAIZMAN.cmd
```

The standard Tkinter/SQLite mode should not need new pip downloads. Building an EXE/PyInstaller is a separate unverified release step.

## 5. Perform technical acceptance before connecting accounts

```powershell
.\RUN_TESTS.cmd
py -3.12 run.py diagnostics --data-dir "$env:TEMP\shpaizman-diagnostics"
py -3.12 run.py gui-smoke --data-dir "$env:TEMP\shpaizman-gui-smoke"
py -3.12 run.py smoke --data-dir "$env:TEMP\shpaizman-agent-smoke"
py -3.12 -m shpaizman.business_cli catalog
py -3.12 -m scripts.service_factory_demo
```

Complete the [developer acceptance sheet](PROGRAMMER_ACCEPTANCE_RU.md) using observed Python version, archive SHA-256, test counts and separate results for the GUI, SQLite, ten agents and Service Factory. Also test controlled shutdown, SQLite state persistence and restoration from a test backup.

## 6. Connect the ten platforms only after local acceptance

Platform-specific instructions are expected **inside the separate ZIP** as `docs/PLATFORMS_RU.md`. The [agent matrix](AGENT_MATRIX.md) describes their current verification status. Never put tokens in GitHub README files, commits, issues or chats. The beneficiary personally creates/authorizes accounts through official providers and independently checks any free-plan limits. Unauthorized actions remain `BLOCKED`.

## 7. Telegram, payout address and support

Telegram setup is performed via the official [@BotFather](https://t.me/BotFather). The beneficiary enters the token and allowed Telegram user ID **locally**. Test `/status`, `/agents` and `/crm` only from authorized accounts.

MetaMask may use a beneficiary-approved **public** receive-only address on an eligible network. Never request recovery phrases, and do not claim the application moves funds. Payment requires an independent incoming-payment record, not merely a CRM entry.

## 8. Handover checklist

Provide the beneficiary with the actual installed folder, source ZIP SHA-256, local test logs, GUI/agent test results, his own configured accounts, blocked integrations, database/backup locations and [signed-off acceptance sheet](PROGRAMMER_ACCEPTANCE_RU.md). Never attach passwords, private keys or seed phrases.

**Security boundary:** GitHub read-only access never authorizes ASTRA to control a Windows computer. An installation requires a locally authorized person or an explicitly authorized remote tool controlled by the beneficiary.
