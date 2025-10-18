@echo off
REM Windows Setup Script for Hybrid IDS
REM Run this as Administrator

echo ========================================
echo   Hybrid IDS - Windows Setup
echo ========================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

echo [2/5] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)
echo.

echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo [4/5] Installing Python dependencies...
pip install --upgrade pip
pip install numpy pandas scikit-learn pyzmq pyyaml
if %errorLevel% neq 0 (
    echo WARNING: Some packages failed to install
) else (
    echo All packages installed successfully!
)
echo.

echo [5/5] Checking Npcap installation...
sc query npcap >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo WARNING: Npcap not detected!
    echo.
    echo Npcap is required for packet capture on Windows.
    echo Please install it from: https://npcap.com/#download
    echo.
    echo Make sure to enable "WinPcap API-compatible Mode"
    echo.
) else (
    echo Npcap service detected!
)
echo.

echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Install Npcap if not already installed
echo   2. Build the C++ components (see REAL_TIME_DEPLOYMENT.md)
echo   3. Test with: python scripts\generate_test_traffic.py test.pcap
echo.
echo Documentation:
echo   - REAL_TIME_DEPLOYMENT.md - Real-time monitoring guide
echo   - COMPLETE_BUILD_GUIDE.md - Complete build instructions
echo   - QUICK_REFERENCE.md - Command reference
echo.
echo Press any key to exit...
pause >nul
