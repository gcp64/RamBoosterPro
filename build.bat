@echo off
title RamBooster - Build Script
echo ============================================
echo    RamBooster EXE Builder
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo      Done.
echo.

:: Build EXE with PyInstaller
echo [2/3] Building EXE with PyInstaller...
echo      This may take a minute...
echo.

pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "RamBooster" ^
    --add-data "ram_booster;ram_booster" ^
    --hidden-import customtkinter ^
    --hidden-import psutil ^
    --hidden-import PIL ^
    --collect-all customtkinter ^
    --icon "icon.ico" ^
    --clean ^
    run.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.
echo ============================================
echo    EXE Location: dist\RamBooster.exe
echo ============================================
echo.

:: Ask to run
set /p RUN="Run the application now? (y/n): "
if /i "%RUN%"=="y" (
    echo Starting RamBooster...
    start "" "dist\RamBooster.exe"
)

pause
