@echo off
setlocal
cd /d %~dp0

echo ============================================
echo   SVN AI Review V2.0 - BUILD RELEASE
echo ============================================
echo.

if not exist "frontend\node_modules" (
    echo [1/4] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
) else (
    echo [1/4] Frontend dependencies ready.
)

echo [2/4] Building Next.js static export...
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
echo [3/4] Copying build output to app/static/...

if exist "app\static" (
    rd /s /q "app\static"
)
xcopy /e /i /y "frontend\out" "app\static" >nul

echo.
echo [4/4] Packaging release...
set "STAGING=release\SVN_AI_Review_V2.0"
if exist "release" rd /s /q "release"
mkdir "%STAGING%"

echo   Copying app/...
xcopy /e /i /y "app" "%STAGING%\app" >nul
echo   Copying config...
copy /y "config.yaml" "%STAGING%\" >nul
copy /y ".env.example" "%STAGING%\" >nul
copy /y "requirements.txt" "%STAGING%\" >nul
copy /y "StartTool.bat" "%STAGING%\" >nul
copy /y "README.md" "%STAGING%\" >nul

echo   Cleaning staging...
rd /s /q "%STAGING%\app\__pycache__" 2>nul
for /d /r "%STAGING%\app" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo   Creating SVN_AI_Review_V2.0.zip...
powershell -NoProfile -Command "Compress-Archive -Path 'release\SVN_AI_Review_V2.0' -DestinationPath 'SVN_AI_Review_V2.0.zip' -Force"

echo   Cleaning up staging...
rd /s /q "release"

echo.
echo ============================================
echo   Release build complete!
echo.
echo   Output: SVN_AI_Review_V2.0.zip
echo   Deploy: unzip + double-click StartTool.bat
echo ============================================
pause
