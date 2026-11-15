@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0windows\Launch_Tool.bat" (
    call "%~dp0windows\Launch_Tool.bat" %*
) else (
    echo [ERROR] windows\Launch_Tool.bat not found!
    pause
)
