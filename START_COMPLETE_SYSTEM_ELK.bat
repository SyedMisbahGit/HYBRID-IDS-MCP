@echo off
REM ============================================
REM Complete Hybrid IDS with ELK Stack Launcher
REM Starts: S-IDS, A-IDS, HIDS, and ELK Dashboard
REM ============================================

echo.
echo ============================================================
echo   Hybrid IDS - Complete System with ELK Stack
echo   S-IDS + A-IDS + HIDS + ELK Dashboard
echo ============================================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo After installation:
    echo 1. Restart your computer
    echo 2. Start Docker Desktop
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo [INFO] Docker detected
docker --version
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running!
    echo.
    echo Please:
    echo 1. Start Docker Desktop
    echo 2. Wait for "Docker Desktop is running" message
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo [INFO] Docker is running
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
echo   Step 1: Starting ELK Stack
echo ============================================================
echo.
echo This will start:
echo   - Elasticsearch (port 9200)
echo   - Logstash (port 5044)
echo   - Kibana (port 5601)
echo.
echo Please wait 2-3 minutes for ELK to fully start...
echo.

cd elk
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start ELK stack
    echo.
    echo Common fixes:
    echo 1. Increase Docker memory to 8GB (Settings - Resources)
    echo 2. Run in PowerShell as Administrator:
    echo    wsl -d docker-desktop
    echo    sysctl -w vm.max_map_count=262144
    echo    exit
    echo.
    pause
    exit /b 1
)

cd ..

echo.
echo [INFO] ELK Stack containers started
echo [INFO] Waiting 30 seconds for Elasticsearch to initialize...
timeout /t 30 /nobreak

echo.
echo ============================================================
echo   Step 2: Checking ELK Stack Health
echo ============================================================
echo.

curl -s http://localhost:9200/_cluster/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Elasticsearch not ready yet
    echo [INFO] Waiting additional 30 seconds...
    timeout /t 30 /nobreak
)

echo [INFO] Elasticsearch is ready
echo [INFO] Kibana will be available at: http://localhost:5601
echo.

echo ============================================================
echo   Step 3: Starting Hybrid IDS Components
echo ============================================================
echo.

REM Start Alert Manager
echo [INFO] Starting Alert Manager...
start "Hybrid IDS - Alert Manager" powershell -NoExit -Command "cd '%CD%'; python src\integration\alert_manager.py"
timeout /t 3 /nobreak

REM Start HIDS
echo [INFO] Starting HIDS (Host-based IDS)...
start "Hybrid IDS - HIDS" powershell -NoExit -Command "cd '%CD%'; python src\hids\hids_main.py --config config\hids\hids_config.yaml --no-logs"
timeout /t 3 /nobreak

REM Start NIDS (S-IDS)
echo [INFO] Starting NIDS/S-IDS (Signature-based)...
start "Hybrid IDS - NIDS/S-IDS" powershell -NoExit -Command "cd '%CD%'; python src\nids_python\nids_main.py -r test.pcap"
timeout /t 3 /nobreak

REM Start AI Engine (A-IDS)
echo [INFO] Starting A-IDS (Anomaly-based ML)...
start "Hybrid IDS - A-IDS" powershell -NoExit -Command "cd '%CD%'; python src\ai\inference\zmq_subscriber.py --model-dir models"
timeout /t 3 /nobreak

echo.
echo ============================================================
echo   System Started Successfully!
echo ============================================================
echo.
echo Components Running:
echo   [1] Elasticsearch  - http://localhost:9200
echo   [2] Kibana         - http://localhost:5601
echo   [3] Logstash       - Ingesting logs
echo   [4] Alert Manager  - Collecting alerts
echo   [5] HIDS           - Host monitoring
echo   [6] NIDS/S-IDS     - Network signature detection
echo   [7] A-IDS          - ML anomaly detection
echo.
echo ============================================================
echo   Next Steps:
echo ============================================================
echo.
echo 1. Wait 2-3 minutes for all components to fully initialize
echo.
echo 2. Open Kibana Dashboard:
echo    http://localhost:5601
echo.
echo 3. Import Dashboard:
echo    - Click Menu (☰) - Stack Management - Saved Objects
echo    - Click Import
echo    - Select: elk\kibana\dashboards\unified-security-dashboard.ndjson
echo    - Click Import
echo.
echo 4. View Dashboard:
echo    - Click Menu (☰) - Dashboard
echo    - Select: Hybrid IDS - Unified Security Dashboard
echo.
echo 5. View Real-time Alerts:
echo    - Click Menu (☰) - Discover
echo    - Select index: hybrid-ids-*
echo.
echo ============================================================
echo   To Stop Everything:
echo ============================================================
echo.
echo 1. Close all PowerShell windows (HIDS, NIDS, Alert Manager, A-IDS)
echo 2. Stop ELK Stack:
echo    cd elk
echo    docker-compose down
echo.
echo ============================================================
echo.
echo Opening Kibana in browser in 10 seconds...
timeout /t 10 /nobreak
start http://localhost:5601
echo.
echo [INFO] System is running. Check Kibana dashboard!
echo.
pause
