@echo off
REM ============================================
REM Hybrid IDS - HIDS Startup Script (Windows)
REM ============================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set VENV_DIR=%PROJECT_ROOT%\venv
set HIDS_DIR=%PROJECT_ROOT%\src\hids
set CONFIG_FILE=%PROJECT_ROOT%\config\hids\hids_config.yaml
set LOG_DIR=%PROJECT_ROOT%\logs
set DATA_DIR=%PROJECT_ROOT%\data

echo ============================================
echo   Hybrid IDS - HIDS Startup
echo ============================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Not running as Administrator.
    echo Some features may be limited (e.g., Windows Event Log monitoring^)
    echo Consider running as Administrator: Right-click ^> Run as Administrator
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "!continue!"=="y" exit /b 1
)

REM Create required directories
echo [1/6] Creating required directories...
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

REM Activate virtual environment
echo [2/6] Activating virtual environment...
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at %VENV_DIR%
    echo Please run: python -m venv venv
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"

REM Check dependencies
echo [3/6] Checking dependencies...
python -c "import psutil, yaml" 2>nul
if %errorLevel% neq 0 (
    echo [WARNING] Missing dependencies. Installing...
    pip install psutil pyyaml watchdog elasticsearch pywin32
)

REM Check configuration
echo [4/6] Checking configuration...
if not exist "%CONFIG_FILE%" (
    echo [WARNING] Config file not found. Using default configuration.
    set CONFIG_FILE=
)

REM Check if Elasticsearch is needed
if defined CONFIG_FILE (
    echo [5/6] Checking Elasticsearch configuration...
    REM Basic check - can expand if needed
)

REM Start HIDS
echo [6/6] Starting HIDS...
echo.

cd /d "%HIDS_DIR%"

REM Build command
set CMD=python hids_main.py

if defined CONFIG_FILE (
    set CMD=!CMD! --config "%CONFIG_FILE%"
)

REM Check for command line arguments
if "%1"=="--no-files" set CMD=!CMD! --no-files
if "%1"=="--no-processes" set CMD=!CMD! --no-processes
if "%1"=="--no-logs" set CMD=!CMD! --no-logs
if "%1"=="--elasticsearch" set CMD=!CMD! --elasticsearch

echo Starting HIDS with command:
echo !CMD!
echo.
echo Press Ctrl+C to stop
echo.

REM Execute
!CMD!

endlocal
