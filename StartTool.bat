@echo off
setlocal
cd /d %~dp0

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env. Edit SVN_USERNAME, SVN_PASSWORD and TEAMS_WEBHOOK_URL if needed.
)

if not exist ".venv\Scripts\python.exe" (
    echo First run: creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Check Python installation.
        pause
        exit /b 1
    )
    echo First run: installing dependencies...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies. Check network or pip source.
        pause
        exit /b 1
    )
)

start "" "http://127.0.0.1:8000"
".venv\Scripts\python.exe" -m app.main
pause
