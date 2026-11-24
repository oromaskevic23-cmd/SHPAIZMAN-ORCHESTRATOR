@echo off
cd /d "%~dp0"
py -3.12 -m shpaizman.operator_ui
exit /b %errorlevel%
