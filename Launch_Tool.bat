@echo off
setlocal
title BMW EntryNav2 Android Auto Manager

cd /d "%~dp0"

:: Prefer standalone compiled executable if present
if exist "%~dp0windows\dist\EntryNav2_Manager.exe" (
    start "" "%~dp0windows\dist\EntryNav2_Manager.exe" %*
    exit /b 0
)

:: Prefer pythonw.exe to launch without console window
where pythonw.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pythonw.exe "%~dp0windows\entrynav2_tool.py" %*
    exit /b 0
)

where pyw.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pyw.exe "%~dp0windows\entrynav2_tool.py" %*
    exit /b 0
)

:: Fallback to python.exe / py.exe
where python.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" python.exe "%~dp0windows\entrynav2_tool.py" %*
    exit /b 0
)

where py.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" py.exe "%~dp0windows\entrynav2_tool.py" %*
    exit /b 0
)

echo [ERROR] Neither EntryNav2_Manager.exe nor Python was found.
echo Please ensure Python 3 is installed or download the pre-compiled EntryNav2_Manager.exe.
pause
exit /b 1
