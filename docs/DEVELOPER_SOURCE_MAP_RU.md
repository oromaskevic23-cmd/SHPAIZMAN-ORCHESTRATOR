# SHPAIZMAN 0.8.0 RC1 — developer source map

**Critical scope distinction:** GitHub currently contains a verifiable offline business core and handover documentation. The **full Windows application is supplied separately** as `SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip`. Do not attempt to execute files missing from the clone. See [archive register and SHA-256](RELEASE_0_8_0_RC1.md).

| Subsystem | Actual GitHub files | Separate ZIP contents (claimed, verify on receipt) |
| --- | --- | --- |
| Business Service Factory | [business.py](../shpaizman/business.py), [CLI](../shpaizman/business_cli.py), [tests](../tests/test_business.py) | `shpaizman/business.py`, `business_cli.py`, `scripts/service_factory_demo.py` |
| Central orchestrator | [Contract](../enterprise/handover-contract.json) | `run.py`, `shpaizman/orchestrator.py`, `registry.py`, `cli.py` |
| Ten agents | [Matrix](AGENT_MATRIX.md) | `shpaizman/agents/`, `shpaizman/connectors/` |
| CRM and GUI | NOT PRESENT in GitHub | `shpaizman/store.py`, `ui.py`, `legacy.py` |
| Telegram | NOT PRESENT in GitHub | `shpaizman/telegram.py` |
| MetaMask and accounting | [Finance policy](FINANCE_AND_PAYOUTS.md) | `shpaizman/beneficiary.py`; no private keys or transfers |
| Windows installation | [Setup guide](WINDOWS_DEVELOPER_SETUP_RU.md) | `INSTALL.cmd`, `START_SHPAIZMAN.cmd`, `scripts/install.py` |
| ZIP verification | [Verifier](../enterprise/verify_release.py), [tests](../tests/test_enterprise_release.py) | `SHA256SUMS.txt` |
| Windows acceptance | [Checklist](PROGRAMMER_ACCEPTANCE_RU.md), [CI](../.github/workflows/enterprise-verification.yml) | `RUN_TESTS.cmd`, `tests/`, `DIAGNOSTICS.cmd` |

**Review sequence:** [presentation](PRESENTATION_RU.md) → [ZIP preflight](PREFLIGHT_WINDOWS_RU.md) → [Windows installation](WINDOWS_DEVELOPER_SETUP_RU.md) → [acceptance sheet](PROGRAMMER_ACCEPTANCE_RU.md).

The ten providers are technology integrations for IT service delivery, **not ten proven marketplaces**. There are 0/10 verified live accounts and no independently confirmed cash receipts. Historical scripts/commits must never be executed automatically.
