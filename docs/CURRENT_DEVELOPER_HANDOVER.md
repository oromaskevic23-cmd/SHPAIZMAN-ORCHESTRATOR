# SHPAIZMAN — current developer handover

Use the current GitHub source, not the historical 0.8.0 RC1 archive. This revision implements a local AI draft worker and desktop operator console. It is ready for developer integration work, not certified production operation.

## Install and run on Windows 10/11 x64

1. Install Python 3.12 x64 with the launcher and Tkinter from https://www.python.org/downloads/windows/.
2. Install Ollama from https://ollama.com/download/windows. Use local models only; disable cloud features according to the installed Ollama version.
3. Download or clone the repository, open PowerShell in its root, and run:

```powershell
py -3.12 -c "import tkinter, sqlite3, urllib.request; print('Python components OK')"
py -3.12 -m pip install -r requirements.txt
ollama pull qwen2.5:3b
.\CHECK_LIVE_AI.cmd qwen2.5:3b
py -3.12 -m unittest discover -s tests -v
.\OPEN_SHPAIZMAN.cmd
```

Ollama must be running locally. The example model requires adequate RAM and disk space. The Python runtime uses only the standard library; the requirements file deliberately has no pip packages. No historical ZIP is required for this path. Do not install on another person's computer without consent.

## Current code map

- `run.py`: CLI entry point.
- `shpaizman/runtime.py`: real loopback model inference, SQLite queue, lease and STOP.
- `shpaizman/operator_ui.py`: desktop GUI.
- `shpaizman/live_acceptance.py`: real model challenge; nonzero exit on failure.
- `shpaizman/business.py`: separate local order management.
- `shpaizman/harvey_bridge.py`: separate offline draft workflow.
- `tests/`: unit and contract tests.

## Verified evidence, November 24, 2026

- [Linux and Windows: 66 unit tests each](https://github.com/oromaskevic23-cmd/SHPAIZMAN-ORCHESTRATOR/actions/runs/45426192354).
- [Live Ollama qwen2.5:0.5b challenge on Linux](https://github.com/oromaskevic23-cmd/SHPAIZMAN-ORCHESTRATOR/actions/runs/45426192565): actual response contained the random challenge. This is not a Windows GUI or commercial acceptance test.
- [Merged implementation](https://github.com/oromaskevic23-cmd/SHPAIZMAN-ORCHESTRATOR/commit/6e144ec6336d0a0474fa6d525e99adeea5a1a71f).

## Developer acceptance tasks

- Run the GUI on the beneficiary's actual Windows PC, submit tasks under all ten roles, verify saved output after restart, verify STOP and local permissions.
- Review and integrate the business queue and AI worker; they are currently separate local modules.
- Implement and test documented, authorized external provider adapters. The ten names currently identify local specialist roles, not ten authenticated provider agents. Provider connections verified: 0/10.
- Implement consented persistent startup and recovery, provider-specific cost limits and operator authentication before unattended use.
- Confirm Telegram pairing separately; no automatic outreach or payouts. Do not place tokens or customer secrets in GitHub.

The historical archive instructions and acceptance forms remain provenance records only. Do not confuse the current implementation with the separate original ZIP or with a production-ready autonomous business.
