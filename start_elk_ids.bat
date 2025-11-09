@echo off
REM ============================================
REM Hybrid IDS with ELK Stack Launcher
REM ============================================

:check_docker
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker daemon is not running
    echo Please start Docker Desktop and wait for it to be ready
    pause
    exit /b 1
)

:start_elk
echo.
echo ============================================================
echo   Starting ELK Stack (Elasticsearch, Logstash, Kibana)
echo   This may take a few minutes on first run...
echo ============================================================
echo.

REM Start ELK Stack in the background
start "ELK Stack" cmd /k "cd /d %~dp0elk && docker-compose up"

echo Waiting for ELK to initialize (this may take 2-3 minutes)...
timeout /t 180 /nobreak >nul

:start_ids
echo.
echo ============================================================
echo   Starting IDS Components
echo ============================================================
echo.

REM Start NIDS in a new terminal window
start "Hybrid IDS - NIDS" cmd /k "cd /d %~dp0 && python src/nids_python/nids_main.py -r test.pcap"

REM Start HIDS in a new terminal window
start "Hybrid IDS - HIDS" cmd /k "cd /d %~dp0 && python src/hids/hids_main.py"

:show_info
echo.
echo ============================================================
echo   Hybrid IDS with ELK Stack is now running!
echo.
echo   Access the Kibana dashboard at:
   echo   http://localhost:5601
echo.
echo   Components:
echo   - NIDS: Running in a new terminal
echo   - HIDS: Running in a new terminal
echo   - ELK Stack: Starting (check Docker logs)
echo.
echo   Press any key to stop all components...
echo ============================================================
echo.

REM Open Kibana in default browser
start "" "http://localhost:5601"

:wait_for_exit
pause >nul

:cleanup
echo.
echo Stopping all components...

echo Stopping NIDS and HIDS...
taskkill /FI "WINDOWTITLE eq Hybrid IDS - NIDS*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Hybrid IDS - HIDS*" /F >nul 2>&1

echo Stopping ELK Stack...
cd /d %~dp0elk
docker-compose down

echo.
echo All components have been stopped.
pause
