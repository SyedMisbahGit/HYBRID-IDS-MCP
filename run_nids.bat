@echo off
REM ============================================
REM Hybrid IDS - NIDS Launcher for Windows
REM Python-based implementation (no C++ build required)
REM ============================================

echo.
echo ============================================================
echo   Hybrid IDS - Network Intrusion Detection System
echo   Python Implementation (No Compilation Required)
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
python -c "import scapy" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Scapy not installed
    echo [INFO] Installing Scapy...
    pip install scapy
)

echo.
echo [INFO] NIDS Options:
echo.
echo   1. Test NIDS components (recommended first)
echo   2. Run NIDS with test.pcap file
echo   3. Run NIDS with custom PCAP file
echo   4. Run NIDS live capture (requires admin)
echo   5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo [INFO] Running NIDS component tests...
    echo.
    python test_nids.py
    echo.
    pause
) else if "%choice%"=="2" (
    if exist test.pcap (
        echo.
        echo [INFO] Running NIDS with test.pcap...
        echo Press Ctrl+C to stop
        echo.
        python src\nids_python\nids_main.py -r test.pcap
    ) else (
        echo.
        echo [ERROR] test.pcap not found
        echo Please place a PCAP file named test.pcap in the project root
        pause
    )
) else if "%choice%"=="3" (
    echo.
    set /p pcapfile="Enter PCAP file path: "
    if exist "%pcapfile%" (
        echo.
        echo [INFO] Running NIDS with %pcapfile%...
        echo Press Ctrl+C to stop
        echo.
        python src\nids_python\nids_main.py -r "%pcapfile%"
    ) else (
        echo.
        echo [ERROR] File not found: %pcapfile%
        pause
    )
) else if "%choice%"=="4" (
    echo.
    echo [WARNING] Live capture requires Administrator privileges
    echo.
    set /p interface="Enter network interface (or press Enter for default): "
    echo.
    echo [INFO] Starting live capture...
    echo Press Ctrl+C to stop
    echo.
    if "%interface%"=="" (
        python src\nids_python\nids_main.py
    ) else (
        python src\nids_python\nids_main.py -i "%interface%"
    )
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
