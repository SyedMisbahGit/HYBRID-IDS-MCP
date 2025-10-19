@echo off
REM Startup script for Hybrid IDS on Windows
REM This script orchestrates the complete integrated intrusion detection system

setlocal enabledelayedexpansion

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script requires Administrator privileges
    echo Please run as Administrator
    pause
    exit /b 1
)

echo ========================================
echo   Hybrid IDS Startup - Windows
echo ========================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

REM Step 1: Check prerequisites
echo [*] Step 1/7: Checking prerequisites...

where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [X] Python is required but not installed
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [√] Python %PYTHON_VERSION% found

REM Check Python dependencies
echo [*] Checking Python dependencies...
python -c "import yaml, zmq, elasticsearch, psutil, watchdog" >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Missing Python dependencies
    echo [*] Installing dependencies...
    pip install -r "%PROJECT_ROOT%\requirements.txt"
)
echo [√] Python dependencies satisfied
echo.

REM Step 2: Load configuration
echo [*] Step 2/7: Loading configuration...

set "CONFIG_FILE=%PROJECT_ROOT%\config\hybrid_ids_config.yaml"
if not exist "%CONFIG_FILE%" (
    echo [X] Configuration file not found: %CONFIG_FILE%
    pause
    exit /b 1
)
echo [√] Configuration loaded
echo.

REM Step 3: Check Docker/ELK Stack
echo [*] Step 3/7: Checking ELK Stack...

where docker >nul 2>&1
if %errorLevel% equ 0 (
    echo [*] Docker found
    set /p START_ELK="Start ELK stack? [y/N]: "
    if /i "!START_ELK!"=="y" (
        echo [*] Starting ELK stack...
        cd "%PROJECT_ROOT%\elk"
        docker-compose up -d
        echo [√] ELK stack started

        echo [*] Waiting for Elasticsearch...
        timeout /t 10 /nobreak >nul

        REM Load Elasticsearch template
        echo [*] Loading Elasticsearch template...
        curl -X PUT "localhost:9200/_index_template/hybrid-ids-template" ^
             -H "Content-Type: application/json" ^
             --data-binary "@%PROJECT_ROOT%\elk\elasticsearch\templates\hybrid-ids-template.json" ^
             >nul 2>&1

        echo [√] Elasticsearch template loaded
        cd "%PROJECT_ROOT%"
    ) else (
        echo [!] ELK stack not started (optional)
    )
) else (
    echo [!] Docker not found - ELK stack will not be started (optional)
)
echo.

REM Step 4: Component selection
echo [*] Step 4/7: Component selection...
echo.
echo Select which components to run:
echo   1) Complete Hybrid IDS (NIDS + HIDS + Integration)
echo   2) HIDS only
echo   3) NIDS only
echo   4) Integration layer only
echo.
set /p COMPONENT_CHOICE="Enter choice [1-4]: "

REM Step 5: Network interface selection
if "%COMPONENT_CHOICE%"=="1" (
    goto :select_interface
) else if "%COMPONENT_CHOICE%"=="3" (
    goto :select_interface
) else (
    goto :skip_interface
)

:select_interface
echo.
echo [*] Step 5/7: Network interface selection...
echo.
echo Available network interfaces:

REM List network interfaces using PowerShell
powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Format-Table -Property Name, InterfaceDescription, Status"

echo.
set /p INTERFACE="Enter network interface name: "

if "!INTERFACE!"=="" (
    echo [X] No interface specified
    pause
    exit /b 1
)

echo [√] Interface selected: !INTERFACE!
goto :after_interface

:skip_interface
echo [*] Step 5/7: Network interface selection (skipped)

:after_interface
echo.

REM Step 6: Build NIDS check
if "%COMPONENT_CHOICE%"=="1" (
    goto :check_nids_build
) else if "%COMPONENT_CHOICE%"=="3" (
    goto :check_nids_build
) else (
    echo [*] Step 6/7: NIDS build check (skipped)
    goto :after_nids_build
)

:check_nids_build
echo [*] Step 6/7: Checking NIDS build...

set "NIDS_BUILD_DIR=%PROJECT_ROOT%\build"

if not exist "%NIDS_BUILD_DIR%\Release\sids.exe" (
    echo [!] NIDS not built
    echo [*] Please build NIDS first:
    echo     mkdir build ^&^& cd build
    echo     cmake .. -G "Visual Studio 17 2022"
    echo     cmake --build . --config Release
    pause
    exit /b 1
)

echo [√] NIDS build found

:after_nids_build
echo.

REM Step 7: Create directories
echo [*] Step 7/7: Creating directories...

if not exist "%PROJECT_ROOT%\logs\alerts" mkdir "%PROJECT_ROOT%\logs\alerts"
if not exist "%PROJECT_ROOT%\logs\hids" mkdir "%PROJECT_ROOT%\logs\hids"
if not exist "%PROJECT_ROOT%\logs\nids" mkdir "%PROJECT_ROOT%\logs\nids"
if not exist "%PROJECT_ROOT%\data\hids" mkdir "%PROJECT_ROOT%\data\hids"

echo [√] Directories created
echo.

REM Step 8: Start components
echo.
echo ========================================
echo   Starting Hybrid IDS Components
echo ========================================
echo.

if "%COMPONENT_CHOICE%"=="1" (
    REM Complete Hybrid IDS
    echo [*] Starting complete Hybrid IDS system...

    REM Start NIDS
    echo [*] Starting NIDS...
    cd "%NIDS_BUILD_DIR%\Release"
    start "NIDS-SIDS" /MIN cmd /c "sids.exe -i %INTERFACE% > %PROJECT_ROOT%\logs\nids\sids.log 2>&1"
    echo [√] NIDS started

    timeout /t 2 /nobreak >nul

    REM Start Hybrid IDS controller
    echo [*] Starting Hybrid IDS controller...
    cd "%PROJECT_ROOT%\src\integration"
    start "Hybrid-IDS" cmd /k "python hybrid_ids.py -c %CONFIG_FILE%"
    echo [√] Hybrid IDS controller started

) else if "%COMPONENT_CHOICE%"=="2" (
    REM HIDS only
    echo [*] Starting HIDS only...
    cd "%PROJECT_ROOT%\src\hids"
    start "HIDS" cmd /k "python hids_main.py -c %PROJECT_ROOT%\config\hids\hids_config.yaml"
    echo [√] HIDS started

) else if "%COMPONENT_CHOICE%"=="3" (
    REM NIDS only
    echo [*] Starting NIDS only...
    cd "%NIDS_BUILD_DIR%\Release"
    start "NIDS-SIDS" cmd /k "sids.exe -i %INTERFACE%"
    echo [√] NIDS started

) else if "%COMPONENT_CHOICE%"=="4" (
    REM Integration layer only
    echo [*] Starting integration layer...
    cd "%PROJECT_ROOT%\src\integration"
    start "Hybrid-IDS" cmd /k "python hybrid_ids.py -c %CONFIG_FILE%"
    echo [√] Integration layer started

) else (
    echo [X] Invalid choice
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Hybrid IDS Running
echo ========================================
echo.
echo [√] Hybrid IDS started successfully!
echo.
echo Logs:
echo   - Hybrid IDS: %PROJECT_ROOT%\logs\hybrid_ids.log
echo   - NIDS: %PROJECT_ROOT%\logs\nids\sids.log
echo   - Alerts: %PROJECT_ROOT%\logs\alerts\unified_alerts.jsonl
echo.

where docker >nul 2>&1
if %errorLevel% equ 0 (
    echo Dashboards:
    echo   - Kibana: http://localhost:5601
    echo   - Elasticsearch: http://localhost:9200
    echo.
)

echo Press any key to exit this window (components will continue running)...
pause >nul
