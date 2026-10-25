# ASTRA Handover — authorized installation protocol

The brother's ASTRA can use this GitHub repository for **instructions and source verification**, not as authority to access a computer. The operator must locally connect an authorized computer-control capability in his own session, pass OS-level confirmation and accept changes explicitly.

## Machine-readable contract

Read [handover-contract.json](../enterprise/handover-contract.json) and validate its exact ten registry entries. No shell command, network endpoint, budget, wallet key or authorization may be inferred from README prose.

## Execution ladder

1. **Inventory (no write):** verify operating system Windows 10/11 x64, Python 3.12 + Tkinter, free disk/memory and existing installation status; never modify BIOS, GPU driver, antivirus, Windows Defender or firewall.
2. **Verify source ZIP:** run the repository's read-only `python -m enterprise.verify_release --zip-path … --expected-sha256 …`. Reject duplicate/traversal paths, executables omitted from SHA256SUMS, missing 10 agents, unexpected archives, invalid digest or size inflation. Do not run source during archive inspection.
3. **Explicit approval:** ask the brother to approve installation *on his local device*. He chooses destination under his own Windows profile. Installer must never silently overwrite existing data, obtain admin rights or create a startup task.
4. **Offline QA:** after install, run `py -3.12 -m unittest discover -s tests -v` and local `run.py smoke`; record actual failures and exact package digest.
5. **Ten independent platform grants:** brother authenticates inside official providers, reviews Terms and pricing; never paste passwords/recovery codes in chat. Stop unapproved or potentially billed operations.
6. **Treasury:** public MetaMask address is optional and validated as EVM *format only*. Do not import keys, approve token allowances or send transactions. Log unverified revenue events separately, never assert settlement without independent accounting.
7. **Monitoring:** surface job states, error reports and the Owner Kill Switch. Enabling scheduled/paid/external activity requires explicit, narrow and revocable beneficiary consent.

## Success is conditional

`PREPARED` means the plan and source are available. `INSTALLED` requires actual Windows installation evidence. `CONNECTED` requires each provider's real authenticated self-check. `EARNING` requires verified lawful settlements. No status may be inferred from a README or app presence alone.

If the brother does not have a connected local computer-control tool, ASTRA can prepare commands and plans, **not remotely operate the machine**. If no payout rail supports MetaMask, funds must arrive through legitimate provider-supported settlement channels, then the brother alone may decide whether and how to move them.
