# SHPAIZMAN 0.8.0 RC1 — Developer Acceptance Record

**Beneficiary:** Alexander Viktorovich. The installer/developer must document actual results from the target Windows computer. Linux or GitHub CI test numbers are not proof of target-machine deployment.

| Gate | Required evidence on beneficiary's PC | Status before inspection |
| --- | --- | --- |
| 01. Separate ZIP | Outer SHA-256 `9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e`, 88 inner SHA-256 manifest items | NOT VERIFIED ON TARGET |
| 02. Windows | Windows 10/11 x64, beneficiary's standard user account, Python 3.12 and Tkinter | NOT VERIFIED |
| 03. Installation | No administrator privileges and no overwriting an earlier installation | NOT VERIFIED |
| 04. Windows tests | `RUN_TESTS.cmd` with a complete log and no concealed failures | NOT VERIFIED |
| 05. Orchestrator | Ten distinct agents, local smoke execution, correct STOP behavior | NOT VERIFIED |
| 06. SQLite / backups | Persistence across restart and restoration of a synthetic backup | NOT VERIFIED |
| 07. GUI and diagnostics | Successful launch, dialogs and performance | NOT VERIFIED |
| 08. Telegram | Beneficiary-approved user ID only, local secrets, authorized replies | NOT VERIFIED |
| 09. Platforms | Separate proof of actual official accounts and access; 0/10 until verified | NOT VERIFIED |
| 10. Business workflow | Service catalog, synthetic order, idempotency and local audit logs | NOT VERIFIED |
| 11. Revenue and payouts | Contract, client acceptance and independently reconciled payment | NOT VERIFIED |
| 12. Handover | Installed folder, logs, limitations list and backup location | NOT VERIFIED |

The acceptance record must contain: date, Windows version, Python version, repository SHA, external ZIP SHA, application/data paths, actual developer, beneficiary consent and known blockers. Never publish real personal information, API tokens or payment credentials.

Passing gates 01–07 may support a **local offline trial only**. It does not establish access to third-party platforms, revenue rights or persistent autonomous operation.

**NO PAYMENTS / NO GUARANTEED INCOME / NO AUTOMATIC WALLET TRANSFERS.**
