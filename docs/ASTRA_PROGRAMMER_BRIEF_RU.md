# ASTRA technical handover — beneficiary's Windows computer

**Authority:** ASTRA is a bounded technical assistant, not the beneficiary, system owner or administrator. The beneficiary must independently authorize access to his own Windows session and approve each consequential action. GitHub access alone never grants computer control.

1. Read the [presentation](PRESENTATION_RU.md), [Windows setup](WINDOWS_DEVELOPER_SETUP_RU.md), [source map](DEVELOPER_SOURCE_MAP_RU.md), [security policy](../SECURITY.md) and [ten-agent handover contract](../enterprise/handover-contract.json).
2. Obtain `SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip` directly and separately from its owner. The full ZIP/EXE is not hosted in this GitHub repository.
3. Before extraction, perform the read-only ZIP verification described in [release registry](RELEASE_0_8_0_RC1.md). The historical preflight script path `scripts/preflight_handover.ps1` is **not present in the current GitHub tree**; do not pretend it is runnable. STOP on a wrong hash, absent Python/Tkinter, or incomplete archive.
4. Obtain the beneficiary's explicit consent before extraction and installation. No administrator elevation, Defender disablement, BIOS changes or silent overwrites.
5. Run `INSTALL.cmd`, `START_SHPAIZMAN.cmd`, `RUN_TESTS.cmd` and, if present in the independently verified ZIP, GUI/SQLite/agent smoke checks. Record actual results in the [acceptance sheet](PROGRAMMER_ACCEPTANCE_RU.md).
6. Verify the Service Factory with `py -3.12 -m shpaizman.business_cli catalog` and a local synthetic demonstration only. A demo order is not actual revenue.
7. Connect each supported platform separately through the beneficiary's own authorized accounts and independently validated free plans. No spending, spam, ToS bypass, privilege escalation or autonomous binding contracts.
8. The beneficiary configures the Telegram token and authorized user ID **locally**. Never write credentials, wallet recovery phrases, bank details or private keys into GitHub or chats.
9. MetaMask may use only a beneficiary-approved **public receiving address** on a supported network. If payments are unsupported, payouts remain BLOCKED.
10. Handover locally: package hash, installation path, versions, actual test logs, genuinely connected accounts, blockers and backup location.

**Stop conditions:** integrity mismatch, absent authorization, paid-charge risk or unverified source. Do not report fictitious installations, accounts, customers or payments.
