@echo off
cd /d "%~dp0"
py -3.12 -m shpaizman.order_execution %*
exit /b %errorlevel%
