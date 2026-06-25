@echo off
setlocal
cd /d %~dp0

echo ============================================
echo   SVN AI Review V2.0
echo ============================================
echo.

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env. Edit SVN_USERNAME, SVN_PASSWORD and TEAMS_WEBHOOK_URL if needed.
    echo.
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
    echo.
    echo Setup complete!
    echo.
)

if not exist "app\static\index.html" (
    echo [WARNING] app/static/index.html not found.
    echo Run "构建发布.bat" first to build the frontend.
    echo.
)

start "" "http://127.0.0.1:8000"
echo Server starting at http://127.0.0.1:8000
echo.
".venv\Scripts\python.exe" -m app.main
pause
