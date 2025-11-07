@echo off
REM ============================================
REM Hybrid IDS - Complete Integrated System Launcher
REM Runs all components with ZeroMQ integration
REM ============================================

echo.
echo ============================================================
echo   Hybrid IDS - Complete Integrated System
echo   Master Control Plane (MCP)
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo [INFO] Python detected
python --version
echo.

REM Check ZeroMQ
python -c "import zmq" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ZeroMQ not installed
    echo [INFO] Installing ZeroMQ...
    pip install pyzmq
)

echo.
echo [INFO] System Components:
echo   1. Integration Controller (MCP)
echo   2. Alert Manager
echo   3. NIDS (Network IDS)
echo   4. HIDS (Host IDS)
echo   5. Event Correlator
echo.
echo [INFO] Choose launch mode:
echo.
echo   1. Full Integrated System (All components)
echo   2. Integration Controller Only
echo   3. Alert Manager Only
echo   4. NIDS + HIDS (No integration)
echo   5. Exit
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo [INFO] Starting Complete Integrated System...
    echo.
    echo This will start all components in the correct order:
    echo   1. Alert Manager
    echo   2. HIDS
    echo   3. NIDS
    echo   4. Event Correlator
    echo   5. Integration Controller
    echo.
    echo Press Ctrl+C to stop all components
    echo.
    pause
    
    REM Start Integration Controller (it will start other components)
    python src\integration\integration_controller.py
    
) else if "%choice%"=="2" (
    echo.
    echo [INFO] Starting Integration Controller...
    echo.
    python src\integration\integration_controller.py
    
) else if "%choice%"=="3" (
    echo.
    echo [INFO] Starting Alert Manager...
    echo.
    python src\integration\alert_manager.py
    
) else if "%choice%"=="4" (
    echo.
    echo [INFO] Starting NIDS and HIDS (separate terminals)...
    echo.
    echo Opening HIDS in new window...
    start "Hybrid IDS - HIDS" python src\hids\hids_main.py --config config\hids\hids_config.yaml --no-logs
    
    timeout /t 3 >nul
    
    echo Opening NIDS in new window...
    start "Hybrid IDS - NIDS" python src\nids_python\nids_main.py -r test.pcap
    
    echo.
    echo [INFO] Components started in separate windows
    echo.
    pause
    
) else if "%choice%"=="5" (
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
