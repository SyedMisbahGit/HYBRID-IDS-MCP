@echo off
REM ============================================
REM Hybrid IDS - Complete System Launcher
REM ============================================

echo.
echo ============================================================
echo   Starting Hybrid IDS - Complete System
echo   This will launch NIDS, HIDS, and ELK Stack
echo ============================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Start ELK Stack in a new terminal window
echo Starting ELK Stack...
start "ELK Stack" cmd /k "cd /d %~dp0 && docker-compose -f elk/docker-compose.yml up"

REM Wait for Elasticsearch to be ready
echo Waiting for Elasticsearch to be ready...
timeout /t 30 /nobreak >nul

REM Start NIDS in a new terminal window
echo Starting NIDS...
start "Hybrid IDS - NIDS" cmd /k "cd /d %~dp0 && call run_nids.bat"

REM Start HIDS in a new terminal window
echo Starting HIDS...
start "Hybrid IDS - HIDS" cmd /k "cd /d %~dp0 && call run_hids.bat"

echo.
echo ============================================================
echo   Hybrid IDS System Started Successfully!
echo   - NIDS: Running in a new terminal
echo   - HIDS: Running in a new terminal
echo   - ELK Stack: Starting... (may take a few minutes)
echo.
echo   Access Kibana dashboard at: http://localhost:5601
echo   Username: elastic
   echo   Password: changeme
echo ============================================================
echo.

REM Open Kibana in default browser after a delay
start "" "http://localhost:5601"

exit /b 0
