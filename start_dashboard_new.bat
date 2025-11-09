@echo off
title Hybrid IDS Dashboard Launcher
echo Starting Hybrid IDS Dashboard...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Create a virtual environment for the backend
if not exist "dashboard\backend\venv" (
    echo Creating Python virtual environment...
    python -m venv dashboard\backend\venv
    call dashboard\backend\venv\Scripts\activate
    pip install --upgrade pip
    pip install -r dashboard\backend\requirements.txt
) else (
    call dashboard\backend\venv\Scripts\activate
)

REM Install and build frontend
cd dashboard\frontend
echo Installing frontend dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo Error installing frontend dependencies
    pause
    exit /b 1
)

echo Building frontend...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo Error building frontend
    pause
    exit /b 1
)

cd ..\..

REM Start the backend
start "Hybrid IDS Backend" cmd /k "cd /d %~dp0 && call dashboard\backend\venv\Scripts\activate && python dashboard\backend\main.py"

echo.
echo Dashboard is starting...
echo - Backend API: http://localhost:8000
echo - Dashboard: http://localhost:8000
echo.

REM Open the dashboard in the default browser
start "" http://localhost:8000

pause
