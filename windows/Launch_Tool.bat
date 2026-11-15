@echo off
setlocal
title BMW EntryNav2 Android Auto Manager Launcher

:: Change directory to this script's folder
cd /d "%~dp0"

:: Check if user explicitly asked for PowerShell mode
if "%1"=="--powershell" (
    goto :RUN_POWERSHELL
)

:: Prefer compiled standalone EXE if present and launched without CLI arguments
if exist "%~dp0dist\EntryNav2_Manager.exe" (
    if "%1"=="" (
        start "" "%~dp0dist\EntryNav2_Manager.exe"
        exit /b 0
    )
)

:: Prefer pythonw.exe / pyw.exe to run without a console window
where pythonw.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pythonw.exe "%~dp0entrynav2_tool.py" %*
    exit /b 0
)

where pyw.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pyw.exe "%~dp0entrynav2_tool.py" %*
    exit /b 0
)

:: Fallback to python.exe / py.exe (the Python script automatically hides console in GUI mode)
where python.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" python.exe "%~dp0entrynav2_tool.py" %*
    exit /b 0
)

where py.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" py.exe "%~dp0entrynav2_tool.py" %*
    exit /b 0
)

:RUN_POWERSHELL
where powershell.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0EntryNav2_Manager.ps1" %*
    exit /b 0
)

echo [ERROR] Neither PowerShell nor Python was found.
echo Please ensure PowerShell or Python 3 is installed.
pause
exit /b 1
