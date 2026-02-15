@echo off
title CleanSweep - PC Cleaner
echo.
echo  ==========================================
echo   CleanSweep - Open Source PC Cleaner
echo  ==========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Please install Python from https://python.org
    pause
    exit /b
)

:: Run as administrator for best results
net session >nul 2>&1
if errorlevel 1 (
    echo  Requesting administrator privileges...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

echo  Running as Administrator - Full cleaning enabled
echo.
python "%~dp0run.py"
pause
