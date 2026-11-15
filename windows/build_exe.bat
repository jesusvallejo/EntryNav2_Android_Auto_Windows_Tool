@echo off
setlocal enabledelayedexpansion
title Build Standalone EntryNav2 Windows Suite EXE
cd /d "%~dp0"

echo =====================================================================
echo  BMW EntryNav2 Android Auto - Standalone Executable Builder
echo =====================================================================
echo.

:: Check Python
where python.exe >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in PATH.
    echo Please install Python 3.10+ from python.org and tick "Add Python to PATH".
    pause
    exit /b 1
)

:: Check PyInstaller
python -m PyInstaller --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] PyInstaller not detected. Installing PyInstaller...
    pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

echo [INFO] Building portable single-file executable...
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "EntryNav2_Manager" ^
    --add-data "entrynav2;entrynav2" ^
    entrynav2_tool.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo =====================================================================
    echo [SUCCESS] Standalone EXE created successfully:
    echo dist\EntryNav2_Manager.exe
    echo =====================================================================
    echo.
) else (
    echo.
    echo [ERROR] Build failed. Please review errors above.
    echo.
)

pause
