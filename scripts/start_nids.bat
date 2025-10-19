@echo off
REM ============================================
REM Hybrid IDS - NIDS Startup Script (Windows)
REM Starts both S-IDS (Signature) and A-IDS (Anomaly/ML)
REM ============================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set BUILD_DIR=%PROJECT_ROOT%\build
set CONFIG_FILE=%PROJECT_ROOT%\config\nids\nids_config.yaml
set LOG_DIR=%PROJECT_ROOT%\logs
set VENV_DIR=%PROJECT_ROOT%\venv

echo ============================================
echo   Hybrid IDS - NIDS Startup
echo   Two-Tier Detection System
echo ============================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Administrator privileges required for packet capture
    echo Please run as Administrator: Right-click ^> Run as Administrator
    pause
    exit /b 1
)

REM Create required directories
echo [1/8] Creating required directories...
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%PROJECT_ROOT%\data" mkdir "%PROJECT_ROOT%\data"

REM Check if build directory exists
if not exist "%BUILD_DIR%" (
    echo [WARNING] Build directory not found. Please build the project first.
    echo.
    echo Build instructions:
    echo   mkdir build
    echo   cd build
    echo   cmake .. -G "MinGW Makefiles"
    echo   cmake --build . --config Release
    echo.
    pause
    exit /b 1
)

REM Check if executables exist
echo [2/8] Checking NIDS executables...
if not exist "%BUILD_DIR%\sids.exe" (
    if not exist "%BUILD_DIR%\Release\sids.exe" (
        echo [ERROR] S-IDS executable not found
        echo Please build the project first
        pause
        exit /b 1
    )
)

if not exist "%BUILD_DIR%\nids.exe" (
    if not exist "%BUILD_DIR%\Release\nids.exe" (
        echo [WARNING] NIDS feature extractor not found
    )
)

echo [OK] S-IDS executable found
echo [OK] NIDS executable found
echo.

REM Check configuration
echo [3/8] Checking configuration...
if not exist "%CONFIG_FILE%" (
    echo [WARNING] Config file not found at %CONFIG_FILE%
    echo Using default configuration
) else (
    echo [OK] Configuration loaded from %CONFIG_FILE%
)
echo.

REM Detect network interface
echo [4/8] Detecting network interfaces...
echo.
echo Available network interfaces:
echo.

REM Use PowerShell to list interfaces
powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -Property Name,InterfaceDescription | Format-Table -AutoSize"

echo.
set /p INTERFACE="Enter network interface name (e.g., Ethernet, Wi-Fi): "

if "!INTERFACE!"=="" (
    echo [ERROR] No interface specified
    pause
    exit /b 1
)

echo [OK] Using interface: !INTERFACE!
echo.

REM Check Python environment
echo [5/8] Checking Python environment...
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [WARNING] Virtual environment not found
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

REM Check AI dependencies
python -c "import numpy, sklearn, zmq" 2>nul
if %errorLevel% neq 0 (
    echo [WARNING] AI engine dependencies missing. Installing...
    pip install numpy scikit-learn pyzmq msgpack -q
)

echo [OK] Python environment ready
echo.

REM Ask user which components to start
echo [6/8] Select components to start:
echo   1^) S-IDS only (Signature-based detection^)
echo   2^) S-IDS + A-IDS (Complete two-tier system^)
echo   3^) Feature extractor only (for testing^)
echo.
set /p COMPONENT_CHOICE="Enter choice [1-3] (default: 2): "
if "!COMPONENT_CHOICE!"=="" set COMPONENT_CHOICE=2

REM Start components
echo.
echo [7/8] Starting NIDS components...
echo.

if "!COMPONENT_CHOICE!"=="1" (
    REM Start S-IDS only
    echo Starting S-IDS (Tier 1: Signature Detection^)...
    echo Command: %BUILD_DIR%\sids.exe -i !INTERFACE!
    echo.

    if exist "%BUILD_DIR%\sids.exe" (
        "%BUILD_DIR%\sids.exe" -i "!INTERFACE!"
    ) else (
        "%BUILD_DIR%\Release\sids.exe" -i "!INTERFACE!"
    )

) else if "!COMPONENT_CHOICE!"=="2" (
    REM Start complete system
    echo Starting Complete Two-Tier System...
    echo.

    REM Start AI engine in background
    echo [Tier 2] Starting AI Engine (A-IDS^)...
    cd /d "%PROJECT_ROOT%\src\ai\inference"
    start /B python zmq_subscriber.py --model-dir ../../../models --port 5555 > "%LOG_DIR%\ai_engine.log" 2>&1

    echo [OK] AI Engine started
    timeout /t 2 /nobreak >nul

    REM Start NIDS feature extractor in background
    echo [Tier 1/2] Starting Feature Extractor (NIDS^)...
    cd /d "%BUILD_DIR%"

    if exist "nids.exe" (
        start /B nids.exe -i "!INTERFACE!" --extract-features > "%LOG_DIR%\nids_features.log" 2>&1
    ) else (
        start /B Release\nids.exe -i "!INTERFACE!" --extract-features > "%LOG_DIR%\nids_features.log" 2>&1
    )

    echo [OK] Feature Extractor started
    timeout /t 2 /nobreak >nul

    REM Start S-IDS in foreground
    echo [Tier 1] Starting S-IDS (Signature Detection^)...
    echo.
    echo ========================================
    echo   Hybrid IDS Running
    echo ========================================
    echo.
    echo Press Ctrl+C to stop all components
    echo.

    if exist "sids.exe" (
        sids.exe -i "!INTERFACE!"
    ) else (
        Release\sids.exe -i "!INTERFACE!"
    )

) else if "!COMPONENT_CHOICE!"=="3" (
    REM Feature extractor only
    echo Starting Feature Extractor only...
    echo Command: %BUILD_DIR%\nids.exe -i !INTERFACE! --extract-features
    echo.

    if exist "%BUILD_DIR%\nids.exe" (
        "%BUILD_DIR%\nids.exe" -i "!INTERFACE!" --extract-features
    ) else (
        "%BUILD_DIR%\Release\nids.exe" -i "!INTERFACE!" --extract-features
    )

) else (
    echo [ERROR] Invalid choice
    pause
    exit /b 1
)

echo.
echo [8/8] Complete
echo.
pause

endlocal
