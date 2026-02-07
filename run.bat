@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo Checking/Installing dependencies...
pip install -r requirements.txt

echo Starting Music Stream Server...
python app.py

pause
