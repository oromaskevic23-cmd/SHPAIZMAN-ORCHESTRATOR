# Complete Windows source package registry — SHPAIZMAN 0.8.0 RC1

```text
Package: SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip
SHA-256: 9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e
Type: SOURCE PYTHON INSTALL KIT; not EXE, not signed MSIX
Archive paths: SHPAIZMAN_BROTHER_EDITION/
File entries including SHA256SUMS: 89
Internal SHA256 manifest items: 88
Registered agents: 10
Windows deployment on beneficiary machine: NOT VERIFIED
External platform sessions: 0/10 VERIFIED
Real income: NOT VERIFIED
```

The owner reported preparing the ZIP, but **the archive is not uploaded to this public GitHub repository**. Do not invent a GitHub Release asset or imply a working download exists. Obtain the source ZIP separately from the owner and compare its SHA-256 against a checksum supplied through a trusted independent channel.

Read-only verification from a trusted Windows host at the GitHub clone root:

```powershell
py -3.12 -m enterprise.verify_release --zip-path "C:\Path\SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip" --expected-sha256 "9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e"
```

Previously reported candidate-stage evidence: `SOURCE_ZIP_HASHES_VERIFIED_NO_CODE_EXECUTED`, 88 SHA-256 comparisons and ten agent source files. Internal manifest checks are not a replacement for outer-archive integrity. An expected hash is not a signed publisher certificate.

## Expected contents of the separate ZIP

- `run.py`, `INSTALL.cmd`, `START_SHPAIZMAN.cmd`, `RUN_TESTS.cmd`, `DIAGNOSTICS.cmd`, `BUSINESS_FACTORY.cmd`
- `shpaizman/orchestrator.py`, `registry.py`, `store.py`, `security.py`, `ui.py`, `telegram.py`, `beneficiary.py`
- `shpaizman/agents/{albato,aimylogic,tomoru,twin,gigachat,yandex,nodul,bitrix24,mws,cloudru}.py`
- `shpaizman/connectors/` — provider adapters; the presence of code is **not evidence of a live account or authorized API access**.
- `shpaizman/business.py`, `business_cli.py`, `scripts/service_factory_demo.py`
- `scripts/install.py`, `scripts/verify_manifest.py`, `scripts/astra_handover.py`, `scripts/preflight.ps1`
- `docs/INSTALL_RU.md`, `PLATFORMS_RU.md`, `ASTRA_ENTERPRISE_HANDOVER_RU.md`, `SERVICE_FACTORY_RU.md`, `ACCEPTANCE_RU.md` (historical ZIP entry names)
- `tests/` and `SHA256SUMS.txt` — expected validation files and manifest.

## GitHub versus the standalone archive

GitHub currently contains the [business engine](../shpaizman/business.py), [CLI](../shpaizman/business_cli.py), [ZIP verifier](../enterprise/verify_release.py), [ASTRA contract](../enterprise/handover-contract.json) and associated tests. The full `run.py`, `shpaizman/orchestrator.py`, `shpaizman/agents/*` and `shpaizman/connectors/*` are **not present in GitHub**. They are claimed as part of the separately delivered version 0.8 archive; do not invent these missing modules or treat a partial clone as the Windows GUI application.

**Future release gate:** publish rights-reviewed and secret-scanned sources, verify Windows CI, and then create a versioned GitHub Release asset with proven source integrity. This document states the current scope, not the successful completion of those future steps.
