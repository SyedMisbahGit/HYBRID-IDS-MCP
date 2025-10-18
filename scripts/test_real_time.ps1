# PowerShell script for real-time testing of Hybrid IDS
# Run as Administrator: Right-click → "Run with PowerShell"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hybrid IDS - Real-Time Test Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click the script and select 'Run with PowerShell as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

# Function to display network interfaces
function Show-NetworkInterfaces {
    Write-Host "`n[INFO] Available Network Interfaces:" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Format-Table Name, InterfaceDescription, LinkSpeed, Status -AutoSize
}

# Function to test Python environment
function Test-PythonEnv {
    Write-Host "`n[INFO] Testing Python environment..." -ForegroundColor Green

    if (Test-Path "venv\Scripts\activate.bat") {
        Write-Host "Virtual environment found!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "Virtual environment not found!" -ForegroundColor Red
        Write-Host "Run: scripts\windows_setup.bat" -ForegroundColor Yellow
        return $false
    }
}

# Function to check Npcap
function Test-Npcap {
    Write-Host "`n[INFO] Checking Npcap installation..." -ForegroundColor Green

    $npcap = Get-Service -Name "npcap" -ErrorAction SilentlyContinue

    if ($npcap) {
        if ($npcap.Status -eq "Running") {
            Write-Host "Npcap is installed and running!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "Npcap is installed but not running!" -ForegroundColor Yellow
            Write-Host "Starting Npcap service..." -ForegroundColor Yellow
            Start-Service npcap
            return $true
        }
    } else {
        Write-Host "Npcap not found!" -ForegroundColor Red
        Write-Host "Download from: https://npcap.com/#download" -ForegroundColor Yellow
        return $false
    }
}

# Main menu
function Show-Menu {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  Select Test Scenario" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Show network interfaces"
    Write-Host "2. Generate test PCAP file"
    Write-Host "3. Test S-IDS with PCAP file"
    Write-Host "4. Test AI engine (simulation mode)"
    Write-Host "5. Capture real traffic with Wireshark (if installed)"
    Write-Host "6. Generate network activity for testing"
    Write-Host "7. View system status"
    Write-Host "8. Exit"
    Write-Host ""

    $choice = Read-Host "Enter choice (1-8)"
    return $choice
}

# Generate test traffic
function Generate-TestPCAP {
    Write-Host "`n[INFO] Generating test PCAP file..." -ForegroundColor Green

    if (Test-Path "venv\Scripts\python.exe") {
        & venv\Scripts\python.exe scripts\generate_test_traffic.py test_traffic.pcap

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Test PCAP created: test_traffic.pcap" -ForegroundColor Green
        } else {
            Write-Host "Failed to generate PCAP!" -ForegroundColor Red
        }
    } else {
        Write-Host "Python virtual environment not found!" -ForegroundColor Red
        Write-Host "Run: scripts\windows_setup.bat" -ForegroundColor Yellow
    }
}

# Test S-IDS
function Test-SIDS {
    Write-Host "`n[INFO] Testing S-IDS..." -ForegroundColor Green

    if (Test-Path "sids.exe") {
        Write-Host "Running S-IDS on test_traffic.pcap..." -ForegroundColor Green
        & .\sids.exe -r test_traffic.pcap
    } elseif (Test-Path "build\sids.exe") {
        Write-Host "Running S-IDS on test_traffic.pcap..." -ForegroundColor Green
        & .\build\sids.exe -r test_traffic.pcap
    } else {
        Write-Host "S-IDS executable not found!" -ForegroundColor Red
        Write-Host "Build it first. See: REAL_TIME_DEPLOYMENT.md" -ForegroundColor Yellow
    }
}

# Test AI engine
function Test-AIEngine {
    Write-Host "`n[INFO] Testing AI Engine..." -ForegroundColor Green

    if (Test-Path "venv\Scripts\python.exe") {
        Write-Host "Starting AI engine in simulation mode..." -ForegroundColor Green
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
        & venv\Scripts\python.exe src\ai\inference\zmq_subscriber.py --simulate
    } else {
        Write-Host "Python virtual environment not found!" -ForegroundColor Red
    }
}

# Capture with Wireshark
function Start-WiresharkCapture {
    Write-Host "`n[INFO] Checking for Wireshark..." -ForegroundColor Green

    $dumpcap = Get-Command dumpcap -ErrorAction SilentlyContinue

    if ($dumpcap) {
        Write-Host "Wireshark found!" -ForegroundColor Green
        Show-NetworkInterfaces
        $interface = Read-Host "`nEnter interface name (e.g., 'Wi-Fi', 'Ethernet')"
        $packetCount = Read-Host "Number of packets to capture (e.g., 100)"
        $filename = "capture_$(Get-Date -Format 'yyyyMMdd_HHmmss').pcap"

        Write-Host "`nCapturing $packetCount packets from '$interface'..." -ForegroundColor Green
        & dumpcap -i $interface -c $packetCount -w $filename

        Write-Host "`nCapture saved to: $filename" -ForegroundColor Green
        Write-Host "Analyze with: .\sids.exe -r $filename" -ForegroundColor Yellow
    } else {
        Write-Host "Wireshark not found!" -ForegroundColor Red
        Write-Host "Download from: https://www.wireshark.org/download.html" -ForegroundColor Yellow
    }
}

# Generate network activity
function Generate-NetworkActivity {
    Write-Host "`n[INFO] Generating network activity..." -ForegroundColor Green
    Write-Host "This will generate various network requests for testing" -ForegroundColor Yellow
    Write-Host ""

    # DNS queries
    Write-Host "Generating DNS queries..." -ForegroundColor Cyan
    nslookup google.com | Out-Null
    nslookup microsoft.com | Out-Null
    nslookup github.com | Out-Null

    # HTTP requests (if curl is available)
    $curl = Get-Command curl -ErrorAction SilentlyContinue
    if ($curl) {
        Write-Host "Generating HTTP requests..." -ForegroundColor Cyan
        curl -s http://example.com | Out-Null
        curl -s http://httpbin.org/get | Out-Null
    }

    # Test local connectivity
    Write-Host "Testing localhost connectivity..." -ForegroundColor Cyan
    Test-NetConnection -ComputerName localhost -Port 80 -InformationLevel Quiet | Out-Null
    Test-NetConnection -ComputerName localhost -Port 443 -InformationLevel Quiet | Out-Null
    Test-NetConnection -ComputerName localhost -Port 22 -InformationLevel Quiet | Out-Null

    Write-Host "`nNetwork activity generated!" -ForegroundColor Green
    Write-Host "If you're capturing traffic, you should see these packets." -ForegroundColor Yellow
}

# Show system status
function Show-Status {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  System Status" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    # Check binaries
    Write-Host "`nBinaries:" -ForegroundColor Green
    if (Test-Path "sids.exe") { Write-Host "  ✓ sids.exe found" -ForegroundColor Green } else { Write-Host "  ✗ sids.exe not found" -ForegroundColor Red }
    if (Test-Path "nids.exe") { Write-Host "  ✓ nids.exe found" -ForegroundColor Green } else { Write-Host "  ✗ nids.exe not found" -ForegroundColor Red }
    if (Test-Path "build\sids.exe") { Write-Host "  ✓ build\sids.exe found" -ForegroundColor Green }
    if (Test-Path "build\nids.exe") { Write-Host "  ✓ build\nids.exe found" -ForegroundColor Green }

    # Check Python
    Write-Host "`nPython Environment:" -ForegroundColor Green
    if (Test-Path "venv") { Write-Host "  ✓ Virtual environment exists" -ForegroundColor Green } else { Write-Host "  ✗ Virtual environment not found" -ForegroundColor Red }

    # Check Npcap
    Write-Host "`nPacket Capture:" -ForegroundColor Green
    Test-Npcap | Out-Null

    # Check test files
    Write-Host "`nTest Files:" -ForegroundColor Green
    if (Test-Path "test_traffic.pcap") { Write-Host "  ✓ test_traffic.pcap exists" -ForegroundColor Green }
    if (Test-Path "nids_alerts.log") { Write-Host "  ✓ nids_alerts.log exists" -ForegroundColor Green }

    Write-Host ""
}

# Main loop
Write-Host "[INFO] System checks..." -ForegroundColor Green
Test-PythonEnv | Out-Null
Test-Npcap | Out-Null

do {
    $choice = Show-Menu

    switch ($choice) {
        "1" { Show-NetworkInterfaces }
        "2" { Generate-TestPCAP }
        "3" { Test-SIDS }
        "4" { Test-AIEngine }
        "5" { Start-WiresharkCapture }
        "6" { Generate-NetworkActivity }
        "7" { Show-Status }
        "8" {
            Write-Host "`nExiting..." -ForegroundColor Green
            break
        }
        default { Write-Host "`nInvalid choice!" -ForegroundColor Red }
    }

    if ($choice -ne "8") {
        Write-Host "`nPress any key to continue..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }

} while ($choice -ne "8")

Write-Host "`nGoodbye!" -ForegroundColor Cyan
