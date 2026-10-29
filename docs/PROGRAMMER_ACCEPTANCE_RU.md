# SHPAIZMAN 0.8.0 RC1 — Windows developer acceptance sheet

**Beneficiary:** Alexander Viktorovich. The developer must record **observed results on the actual target machine**, not reuse Linux or GitHub CI numbers as if they were Windows acceptance.

| Gate | Evidence required on target PC | Precheck status |
| --- | --- | --- |
| 01. Separate ZIP | Expected outer SHA-256 `9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e` and 88 individually verified source-file digests | NOT VERIFIED ON TARGET |
| 02. Windows environment | Windows 10/11 x64, beneficiary's user session, Python 3.12 with Tkinter | NOT VERIFIED |
| 03. Installation | No administrator rights and no overwrite of existing installation | NOT VERIFIED |
| 04. Windows tests | `RUN_TESTS.cmd` with complete actual log and no hidden failures | NOT VERIFIED |
| 05. Orchestrator | Ten unique agent sources, actual local smoke and reliable STOP | NOT VERIFIED |
| 06. SQLite and backup | Restart, persist a synthetic record and recover a backup | NOT VERIFIED |
| 07. GUI and diagnostics | Starts without error; dialogs and resource use verified | NOT VERIFIED |
| 08. Telegram | Beneficiary-only authorized ID, locally stored secrets and safe commands | NOT VERIFIED |
| 09. Platforms | Independently validated real beneficiary accounts and authorized access; initially 0/10 | NOT VERIFIED |
| 10. Business workflow | Service catalog, synthetic order, idempotence and local audit records | NOT VERIFIED |
| 11. Income | Actual contract + customer acceptance + independent incoming-payment reconciliation | NOT VERIFIED |
| 12. Handover | Installation directory, logs, outstanding blockers, backup location | NOT VERIFIED |

Record the date, Windows/Python versions, repository commit SHA, archive SHA-256, installation and data paths, technical operator, beneficiary authorization and all known blockers. Never publish personal data or tokens to GitHub.

Passing gates 01–07 demonstrates only readiness for a local **offline trial**. It does not establish access to external services, permission to receive funds or a durable autonomous business.

**NO PAYMENTS / NO GUARANTEED INCOME / NO AUTOMATIC WALLET TRANSFERS.**
