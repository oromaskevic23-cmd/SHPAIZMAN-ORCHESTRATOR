# Безопасная предварительная проверка Windows

В публичном репозитории находится **только предустановочная проверка**, не скрытый установщик.

```powershell
cd "$env:USERPROFILE\Documents\SHPAIZMAN-ORCHESTRATOR"
powershell.exe -NoProfile -File .\scripts\preflight_handover.ps1 -ArchivePath "$env:USERPROFILE\Downloads\SHPAIZMAN_SERVICE_FACTORY_0.8.0_RC1.zip"
```

Команда требует Windows x64, Python 3.12 с Tkinter и SHA256 ZIP `9c26a398e585d9e1f79d75df71d3b99084b599cf5b832e0279dd857f94feb75e`. Она обращается только к локальным путям, запускает Python-модуль **чтения ZIP**, не извлекает содержимое, не скачивает файлы и ничего не устанавливает.

После PASS откройте [полную инструкцию](WINDOWS_DEVELOPER_SETUP_RU.md). Брат отдельно разрешает распаковку и установку; пользовательский Windows-аккаунт и реальные API-ключи остаются под его контролем.
