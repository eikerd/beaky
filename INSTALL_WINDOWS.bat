@echo off
REM Quick Windows Setup - Run this as Administrator
echo ================================
echo   Beaky Windows Setup
echo ================================
echo.
echo This will run the PowerShell setup script.
echo Make sure you run this as Administrator!
echo.
pause

PowerShell.exe -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"

pause
