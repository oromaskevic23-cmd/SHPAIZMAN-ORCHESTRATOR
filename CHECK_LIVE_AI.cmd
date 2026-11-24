@echo off
cd /d "%~dp0"
if "%~1"=="" (echo Usage: CHECK_LIVE_AI.cmd model-name& exit /b 2)
py -3.12 -m shpaizman.live_acceptance --model "%~1"
exit /b %errorlevel%
