@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo Starting Music Stream Server...
python app.py

pause
