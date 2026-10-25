# Инструкция программисту: запуск SHPAIZMAN 0.8.0 RC1 на Windows

**Адрес репозитория:** https://github.com/oromaskevic23-cmd/SHPAIZMAN-ORCHESTRATOR

**Это двухкомпонентная передача.** Репозиторий содержит документацию, бизнес-ядро, SHA/ZIP-верификатор и CI. Полный Windows Python-код пока находится в **отдельном ZIP** `SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip`, который программист должен получить от владельца. GitHub не может автоматически загрузить отсутствующий архив. По одному README установка полного GUI невозможна.

## 0. Что нужно

- Windows 10/11 x64, обычная локальная учётная запись самого Александра Викторовича.
- Python 3.12 x64, установленный с Python Launcher и Tcl/Tk: https://www.python.org/downloads/windows/ .
- Git для Windows (для клонирования): https://git-scm.com/download/win . Либо скачать публичный репозиторий по **Code → Download ZIP** без Git.
- Отдельно предоставленный `SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip` и независимо подтверждённый SHA-256 из [реестра поставки](RELEASE_0_8_0_RC1.md).
- Не нужны Docker, Hyper-V, изменения BIOS, отключение Defender, платный AI API, GPU или MetaMask-ключи для первых локальных тестов.

**Подтверждение брата** требуется перед установкой, подключением аккаунтов, отправкой сообщений, финансовыми действиями и постоянным автозапуском.

## 1. Забрать репозиторий

Откройте обычный **PowerShell** от пользователя брата, без Run as Administrator:

```powershell
cd "$env:USERPROFILE\Documents"
git clone https://github.com/oromaskevic23-cmd/SHPAIZMAN-ORCHESTRATOR.git
cd SHPAIZMAN-ORCHESTRATOR
py -3.12 --version
py -3.12 -c "import tkinter,sqlite3; print('Python stdlib + Tkinter: OK')"
```

Если `git` недоступен, используйте GitHub **Code → Download ZIP** и распакуйте репозиторий в Documents. Не нужно вводить пароль GitHub в терминал для публичного read-only клона.

## 2. Проверить внешний Windows-архив **до распаковки**

Поместите ZIP, полученный от владельца, например, в `Downloads`. В корне GitHub-клона:

```powershell
$SourceZip = Join-Path $env:USERPROFILE "Downloads\SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip"
Get-FileHash -LiteralPath $SourceZip -Algorithm SHA256
py -3.12 -m enterprise.verify_release --zip-path "$SourceZip" --expected-sha256 "9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e"
```

Ожидается `SOURCE_ZIP_HASHES_VERIFIED_NO_CODE_EXECUTED` (или эквивалентный VERIFIED-статус вашей ревизии). Если внешний SHA не совпал, **прекратить установку** и перепроверить исходный файл другим разрешённым каналом. SHA в GitHub не доказывает авторство архива и не заменяет подпись издателя.

## 3. Распаковать и ещё раз проверить

```powershell
$ExtractRoot = Join-Path $env:USERPROFILE "Documents\SHPAIZMAN-Source-0.8.0"
if (Test-Path -LiteralPath $ExtractRoot) { throw "Папка уже существует: запрещено перезаписывать." }
Expand-Archive -LiteralPath $SourceZip -DestinationPath $ExtractRoot
$App = Join-Path $ExtractRoot "SHPAIZMAN_BROTHER_EDITION"
Set-Location -LiteralPath $App
py -3.12 scripts\verify_manifest.py
```

В `SHPAIZMAN_BROTHER_EDITION` должны быть: `run.py`, `INSTALL.cmd`, `START_SHPAIZMAN.cmd`, `shpaizman/orchestrator.py`, каталог `shpaizman/agents`, `tests`, `docs` и `SHA256SUMS.txt`.

## 4. Установить локальную программу

Запустить из `$App` только после согласия брата:

```powershell
.\INSTALL.cmd
```

Исходный установщик создаёт отдельную версию программы под `%LOCALAPPDATA%\SHPAIZMAN-BROTHER-EDITION\app-0.8.0-rc1`. Он не требует прав администратора и **не должен перезаписывать** существующие данные. При ошибке смотрите `docs/INSTALL_RU.md` внутри ZIP. Не удаляйте старую установленную версию автоматически.

```powershell
$Installed = Join-Path $env:LOCALAPPDATA "SHPAIZMAN-BROTHER-EDITION\app-0.8.0-rc1"
Set-Location -LiteralPath $Installed
.\START_SHPAIZMAN.cmd
```

**Никаких скачиваний pip** для штатного Python/Tkinter/SQLite-режима не нужно. PyInstaller / EXE — отдельный этап сборки, в текущий ZIP не входит.

## 5. Техническая приёмка до аккаунтов

```powershell
.\RUN_TESTS.cmd
py -3.12 run.py diagnostics --data-dir "$env:TEMP\shpaizman-diagnostics"
py -3.12 run.py gui-smoke --data-dir "$env:TEMP\shpaizman-gui-smoke"
py -3.12 run.py smoke --data-dir "$env:TEMP\shpaizman-agent-smoke"
py -3.12 -m shpaizman.business_cli catalog
py -3.12 -m scripts.service_factory_demo
```

Заполнить [акт программиста](PROGRAMMER_ACCEPTANCE_RU.md) с точной версией Python, SHA ZIP, количеством прошедших тестов и отдельными результатами GUI, SQLite, десяти агентов и Service Factory. Отдельно проверить остановку оркестратора, сохранение SQLite после перезапуска и восстановление тестовой копии.

## 6. Подключить 10 платформ только после локальной приёмки

Руководство по настройке для каждой платформы и её API находится в **ZIP**: `docs/PLATFORMS_RU.md`. Матрица статусов есть в [AGENT_MATRIX.md](AGENT_MATRIX.md). Не передавайте токены в GitHub, README, коммиты, issue или чат. Профиль аккаунта брат создаёт лично через официальный сервис и проверяет ограничения бесплатного тарифа. Отсутствие разрешённых операций = `BLOCKED`.

## 7. Настроить Telegram, адрес выплат и поддержку

Telegram: бот создаётся через официальный [@BotFather](https://t.me/BotFather). Токен и ID брата вводятся **локально**. Тест: `/status`, `/agents`, `/crm` с разрешённого ID.

MetaMask: фиксируется только публичный адрес **при подтверждении брата**, секретная фраза никогда не запрашивается. Программа не делает переводов. Доход подтверждается только независимым платёжным источником, а не записями бизнес-CRM.

## 8. Что передать брату по завершении

Папку установленного приложения, `SHA256` исходного ZIP, журнал локальных тестов, отчёт GUI/агентов, настроенные им аккаунты, перечень `BLOCKED` площадок, расположение базы/backup и [акт приёмки](PROGRAMMER_ACCEPTANCE_RU.md). Никакие пароли, ключи или seed-фразы не прикладывать.

**Красная линия:** GitHub read-only подключение ASTRA не даёт ей права управления компьютером. Установка и настройки выполняются только через предоставленный братом локальный инструмент/его программиста.
