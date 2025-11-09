@echo off
REM ============================================
REM Hybrid IDS - All-in-One Launcher
REM ============================================

echo.
echo ============================================================
echo   Hybrid IDS - Complete System
echo   Starting NIDS, HIDS, and Web Dashboard
echo ============================================================
echo.

REM Start NIDS in a new terminal window
start "Hybrid IDS - NIDS" cmd /k "cd /d %~dp0 && python src/nids_python/nids_main.py -r test.pcap"

REM Start HIDS in a new terminal window
start "Hybrid IDS - HIDS" cmd /k "cd /d %~dp0 && python src/hids/hids_main.py"

REM Start Web Dashboard in a new terminal window
start "Hybrid IDS - Dashboard" cmd /k "cd /d %~dp0 && python web_dashboard.py"

echo.
echo ============================================================
echo   Hybrid IDS System Started Successfully!
echo   - NIDS: Running in a new terminal
echo   - HIDS: Running in a new terminal
echo   - Dashboard: Starting...
echo.
echo   Access the dashboard at: http://localhost:5000
echo ============================================================
echo.

REM Open dashboard in default browser
timeout /t 3 /nobreak >nul
start "" "http://localhost:5000"

echo Press any key to stop all components...
pause >nul

taskkill /FI "WINDOWTITLE eq Hybrid IDS - NIDS*" /F
taskkill /FI "WINDOWTITLE eq Hybrid IDS - HIDS*" /F
taskkill /FI "WINDOWTITLE eq Hybrid IDS - Dashboard*" /F

echo.
echo All components stopped.
pause
