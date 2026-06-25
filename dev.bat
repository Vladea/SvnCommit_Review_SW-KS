@echo off
setlocal
cd /d %~dp0

echo ============================================
echo   SVN AI Review V2.0 - 开发模式
echo ============================================
echo.

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [1/4] Created .env from template.
) else (
    echo [1/4] .env already exists.
)

if not exist ".venv\Scripts\python.exe" (
    echo [2/4] Creating Python virtual environment...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
    echo [2/4] Python environment ready.
) else (
    echo [2/4] Python environment ready.
)

if not exist "frontend\node_modules" (
    echo [3/4] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    echo [3/4] Frontend dependencies ready.
) else (
    echo [3/4] Frontend dependencies ready.
)

echo [4/4] Starting servers...
echo.
echo   Backend  : http://127.0.0.1:8000
echo   Frontend : http://localhost:3000  (via Next.js HMR)
echo.

start "SVN AI Review - Backend" ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
start "SVN AI Review - Frontend" cmd /c "cd frontend && npm run dev"

timeout /t 4 >nul
start "" "http://localhost:3000"

echo.
echo Both servers started. Close their windows to stop.
echo ============================================
pause
