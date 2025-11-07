@echo off
REM ============================================
REM Complete Hybrid IDS WITHOUT Docker
REM Uses Python Web Dashboard instead of ELK
REM ============================================

echo.
echo ============================================================
echo   Hybrid IDS - Complete System (No Docker Required)
echo   S-IDS + A-IDS + HIDS + Web Dashboard
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

echo ============================================================
echo   Starting All Components
echo ============================================================
echo.

REM Start Web Dashboard
echo [1/5] Starting Web Dashboard (http://localhost:8080)...
start "Hybrid IDS - Web Dashboard" powershell -NoExit -Command "cd '%CD%'; python web_dashboard.py"
timeout /t 3 /nobreak

REM Start Alert Manager
echo [2/5] Starting Alert Manager...
start "Hybrid IDS - Alert Manager" powershell -NoExit -Command "cd '%CD%'; python src\integration\alert_manager.py"
timeout /t 3 /nobreak

REM Start HIDS
echo [3/5] Starting HIDS (Host-based IDS)...
start "Hybrid IDS - HIDS" powershell -NoExit -Command "cd '%CD%'; python src\hids\hids_main.py --config config\hids\hids_config.yaml --no-logs"
timeout /t 3 /nobreak

REM Start NIDS (S-IDS)
echo [4/5] Starting NIDS/S-IDS (Signature-based)...
start "Hybrid IDS - NIDS/S-IDS" powershell -NoExit -Command "cd '%CD%'; python src\nids_python\nids_main.py -r test.pcap"
timeout /t 3 /nobreak

REM Start A-IDS (ML)
echo [5/5] Starting A-IDS (ML Anomaly Detection)...
start "Hybrid IDS - A-IDS" powershell -NoExit -Command "cd '%CD%'; python src\ai\inference\zmq_subscriber.py --model-dir models"
timeout /t 3 /nobreak

echo.
echo ============================================================
echo   System Started Successfully!
echo ============================================================
echo.
echo Components Running:
echo   [1] Web Dashboard  - http://localhost:8080
echo   [2] Alert Manager  - Collecting alerts
echo   [3] HIDS           - Host monitoring
echo   [4] NIDS/S-IDS     - Network signature detection
echo   [5] A-IDS          - ML anomaly detection
echo.
echo ============================================================
echo   Access Dashboard:
echo ============================================================
echo.
echo   Web Dashboard: http://localhost:8080
echo   - Real-time statistics
echo   - Recent alerts
echo   - System metrics
echo   - Auto-refresh every 5 seconds
echo.
echo ============================================================
echo   To Stop Everything:
echo ============================================================
echo.
echo   Close all PowerShell windows
echo.
echo ============================================================
echo.
echo Opening dashboard in 5 seconds...
timeout /t 5 /nobreak
start http://localhost:8080
echo.
echo [INFO] System is running. Check dashboard at http://localhost:8080
echo.
pause
