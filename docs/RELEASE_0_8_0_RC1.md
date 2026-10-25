# Реестр полной Windows-поставки — 0.8.0 RC1

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

Владелец подготовил ZIP, но **сам архив ещё не загружен в этот публичный GitHub-репозиторий**. Это принципиально: нельзя выдавать отсутствующий Release Asset или несуществующую ссылку на GitHub за рабочую загрузку. Получите исходный ZIP от владельца отдельно; SHA-256 нужно сравнить с независимо переданной контрольной суммой.

Проверка на доверенной машине из корня GitHub:

```powershell
py -3.12 -m enterprise.verify_release --zip-path "C:\\Path\\SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip" --expected-sha256 "9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e"
```

Проверенный в предыдущем локальном этапе статус: `SOURCE_ZIP_HASHES_VERIFIED_NO_CODE_EXECUTED`, 88 SHA256-сверок, десять агентских исходников. Внутренний манифест не заменяет проверку внешнего SHA, а внешний SHA не является подписанным сертификатом автора.

## Состав исходной программы внутри ZIP

- `run.py`, `INSTALL.cmd`, `START_SHPAIZMAN.cmd`, `RUN_TESTS.cmd`, `DIAGNOSTICS.cmd`, `BUSINESS_FACTORY.cmd`
- `shpaizman/orchestrator.py` + `registry.py` + `store.py` + `security.py` + `ui.py` + `telegram.py` + `beneficiary.py`
- `shpaizman/agents/{albato,aimylogic,tomoru,twin,gigachat,yandex,nodul,bitrix24,mws,cloudru}.py`
- `shpaizman/connectors/` — provider-specific adapters. **Наличие кода не равно действующему аккаунту или подтверждённому API.**
- `shpaizman/business.py` и `business_cli.py` + `scripts/service_factory_demo.py`
- `scripts/install.py`, `scripts/verify_manifest.py`, `scripts/astra_handover.py`, `scripts/preflight.ps1`
- `docs/INSTALL_RU.md`, `PLATFORMS_RU.md`, `ASTRA_ENTERPRISE_HANDOVER_RU.md`, `SERVICE_FACTORY_RU.md`, `ACCEPTANCE_RU.md`
- `tests/` и `SHA256SUMS.txt` — обязательные проверки и список содержимого.

## Сравнение репозитория и ZIP

В GitHub сейчас опубликованы [конвейер заказов](../shpaizman/business.py), [CLI](../shpaizman/business_cli.py), [ZIP-верификатор](../enterprise/verify_release.py), [контракт ASTRA](../enterprise/handover-contract.json) и тесты. Отсутствующие `run.py`, `shpaizman/orchestrator.py`, `shpaizman/agents/*`, `shpaizman/connectors/*` предоставляются через полный 0.8 ZIP — не придумывайте недостающие модули и не пытайтесь запускать неполный клон как GUI-приложение.

**Цель следующей публикации:** разместить проверенные полноценные исходники в GitHub после отдельной проверки лицензий, прав, секретов и Windows CI, затем выпустить официальный источник ZIP как versioned Release Asset. Этот документ фиксирует фактическое состояние, а не утверждает, что такая публикация уже сделана.
