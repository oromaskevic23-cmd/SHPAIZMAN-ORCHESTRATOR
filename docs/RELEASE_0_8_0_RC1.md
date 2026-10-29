# SHPAIZMAN 0.8.0 RC1 — Separate Windows Source Package Register

```text
Package: SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip
SHA-256: 9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e
Type: SOURCE PYTHON INSTALL KIT; not an EXE or signed MSIX
Archive paths: SHPAIZMAN_BROTHER_EDITION/
File entries including SHA256SUMS: 89
Internal SHA256 manifest items: 88
Registered agent source modules: 10
Deployment on beneficiary's Windows machine: NOT VERIFIED
External platform sessions: 0/10 VERIFIED
Real income: NOT VERIFIED
```

**The owner-provided ZIP archive is NOT uploaded to this public GitHub repository.** An absent release asset must never be presented as a real download. Obtain the complete source ZIP from the owner separately and compare its SHA-256 with an independently communicated trusted checksum. The full archive itself was not revalidated during this language-only documentation update.

From a trusted computer and the GitHub clone root, execute the read-only validator:

```powershell
py -3.12 -m enterprise.verify_release --zip-path "C:\Path\SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip" --expected-sha256 "9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e"
```

The previously reported local result was `SOURCE_ZIP_HASHES_VERIFIED_NO_CODE_EXECUTED` for 88 file checks and ten agent source files. The inner manifest does not replace an externally pinned archive checksum. Neither SHA-256 manifest is a signed publisher certificate.

## Claimed contents of the separately supplied ZIP

- `run.py`, `INSTALL.cmd`, `START_SHPAIZMAN.cmd`, `RUN_TESTS.cmd`, `DIAGNOSTICS.cmd`, `BUSINESS_FACTORY.cmd`
- `shpaizman/orchestrator.py`, `registry.py`, `store.py`, `security.py`, `ui.py`, `telegram.py`, `beneficiary.py`
- `shpaizman/agents/{albato,aimylogic,tomoru,twin,gigachat,yandex,nodul,bitrix24,mws,cloudru}.py`
- `shpaizman/connectors/` — provider adapters; source presence is not evidence of an authorized account or available API
- `shpaizman/business.py`, `business_cli.py`, `scripts/service_factory_demo.py`
- `scripts/install.py`, `scripts/verify_manifest.py`, `scripts/astra_handover.py`, `scripts/preflight.ps1`
- Historical filenames within the separate ZIP such as `docs/INSTALL_RU.md`, `PLATFORMS_RU.md`, `ASTRA_ENTERPRISE_HANDOVER_RU.md`, `SERVICE_FACTORY_RU.md`, `ACCEPTANCE_RU.md` are retained as reported source inventory only. They are not hosted or translated by this repository.
- `tests/` and `SHA256SUMS.txt` — required local checks and contents manifest

## Public repository versus separate archive

The present GitHub repository includes the [offline business pipeline](../shpaizman/business.py), [CLI](../shpaizman/business_cli.py), [ZIP validator](../enterprise/verify_release.py), [ASTRA contract](../enterprise/handover-contract.json) and tests. It **does not** contain `run.py`, `shpaizman/orchestrator.py`, the full `shpaizman/agents/*` or `shpaizman/connectors/*` trees. Do not fabricate missing modules or try to launch the incomplete repository clone as a GUI app.

**Next proposed delivery milestone:** perform source, license, secret and Windows CI reviews of the full external package before separately authorizing GitHub publication and an official versioned Release Asset. This document records a specification and previously stated verification limits; it does not claim the asset has already been published.
