# Карта исходного кода для программиста — SHPAIZMAN 0.8.0 RC1

**Важное различие:** текущий GitHub хранит проверяемое бизнес-ядро и схему передачи. **Полная Windows-программа передаётся отдельным ZIP** `SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip`. Не пытайтесь запускать отсутствующие файлы из клона. [Реестр ZIP и SHA-256](RELEASE_0_8_0_RC1.md).

| Подсистема | Реальные файлы в GitHub | Файлы из отдельного ZIP |
|---|---|---|
| Business Service Factory | [business.py](../shpaizman/business.py), [CLI](../shpaizman/business_cli.py), [тесты](../tests/test_business.py) | `shpaizman/business.py`, `business_cli.py`, `scripts/service_factory_demo.py` |
| Центральный оркестратор | [Контракт](../enterprise/handover-contract.json) | `run.py`, `shpaizman/orchestrator.py`, `registry.py`, `cli.py` |
| 10 агентов | [Матрица](AGENT_MATRIX.md) | `shpaizman/agents/`, `shpaizman/connectors/` |
| CRM / UI | **Пока нет в GitHub** | `shpaizman/store.py`, `ui.py`, `legacy.py` |
| Telegram | **Пока нет в GitHub** | `shpaizman/telegram.py` |
| MetaMask и учёт | [Финансовая политика](FINANCE_AND_PAYOUTS.md) | `shpaizman/beneficiary.py`; нет ключей/переводов |
| Windows установка | [Руководство](WINDOWS_DEVELOPER_SETUP_RU.md), [read-only preflight](../scripts/preflight_handover.ps1) | `INSTALL.cmd`, `START_SHPAIZMAN.cmd`, `scripts/install.py` |
| ZIP verification | [verify_release.py](../enterprise/verify_release.py), [тесты](../tests/test_enterprise_release.py) | `SHA256SUMS.txt` |
| Windows acceptance | [Акт](PROGRAMMER_ACCEPTANCE_RU.md), [Enterprise CI](../.github/workflows/enterprise-verification.yml) | `RUN_TESTS.cmd`, `tests/`, `DIAGNOSTICS.cmd` |

**Порядок работы:** [презентация](PRESENTATION_RU.md) → [проверка ZIP](PREFLIGHT_WINDOWS_RU.md) → [установка](WINDOWS_DEVELOPER_SETUP_RU.md) → [акт](PROGRAMMER_ACCEPTANCE_RU.md).

Текущие 10 SaaS/AI-платформ — это средства выполнения IT-услуг, а не десять доказанных маркетплейсов. Реальные подключения 0/10, поступления денег НЕ ПОДТВЕРЖДЕНЫ. Исторические файлы/проекты в Git history не должны автоматически исполняться.
