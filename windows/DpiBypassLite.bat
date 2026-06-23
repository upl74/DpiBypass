@echo off
cd /d "%~dp0"
title DpiBypass Lite

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto :error
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q
if errorlevel 1 goto :error

if not exist "third_party\tg-ws-proxy\proxy\tg_ws_proxy.py" (
    echo Installing tg-ws-proxy...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-lite.ps1"
)

cd app
set DPIBYPASS_APPDATA=DpiBypassLite
pythonw main_lite.py %* 2>nul
if errorlevel 1 python main_lite.py %*
exit /b 0

:error
echo.
echo Failed. Install Python 3.10+ from python.org
pause
