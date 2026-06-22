@echo off
cd /d "%~dp0"
title DpiBypass

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto :error
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q
if errorlevel 1 goto :error

cd app
pythonw main.py 2>nul
if errorlevel 1 python main.py
exit /b 0

:error
echo.
echo Failed. Install Python 3.10+ from python.org
pause
