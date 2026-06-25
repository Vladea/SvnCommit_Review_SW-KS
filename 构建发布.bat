@echo off
setlocal
cd /d %~dp0

echo ============================================
echo   SVN AI Review V2.0 - 构建发布
echo ============================================
echo.

if not exist "frontend\node_modules" (
    echo [1/3] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
) else (
    echo [1/3] Frontend dependencies ready.
)

echo [2/3] Building Next.js static export...
cd frontend
call npm run build
if errorlevel 1 (
    echo.
    echo !!! Build failed !!!
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [3/3] Copying build output to app/static/...

if exist "app\static" (
    rd /s /q "app\static"
)
xcopy /e /i /y "frontend\out" "app\static" >nul

echo.
echo ============================================
echo   Release build complete!
echo.
echo   Output: app/static/ ^(ready for StartTool.bat^)
echo ============================================
pause
