@echo off
REM ============================================
REM Hybrid IDS - HIDS Launcher for Windows
REM ============================================

echo.
echo ============================================================
echo   Hybrid IDS - Host-based Intrusion Detection System
echo   Windows Platform
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7 or later
    pause
    exit /b 1
)

echo [INFO] Python detected
python --version
echo.

REM Check if required packages are installed
echo [INFO] Checking dependencies...
python -c "import psutil, watchdog, yaml" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some dependencies may be missing
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo [INFO] Starting HIDS...
echo.
echo Options:
echo   1. Run full HIDS (File + Process + Log monitoring)
echo   2. Run HIDS without log monitoring (recommended for testing)
echo   3. Run HIDS test (quick demo)
echo   4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo [INFO] Starting full HIDS system...
    echo Press Ctrl+C to stop
    echo.
    python src\hids\hids_main.py --config config\hids\hids_config.yaml
) else if "%choice%"=="2" (
    echo.
    echo [INFO] Starting HIDS (without log monitoring)...
    echo Press Ctrl+C to stop
    echo.
    python src\hids\hids_main.py --config config\hids\hids_config.yaml --no-logs
) else if "%choice%"=="3" (
    echo.
    echo [INFO] Running HIDS test...
    echo.
    python test_hids.py
    echo.
    pause
) else if "%choice%"=="4" (
    echo.
    echo [INFO] Exiting...
    exit /b 0
) else (
    echo.
    echo [ERROR] Invalid choice
    pause
    exit /b 1
)

pause
