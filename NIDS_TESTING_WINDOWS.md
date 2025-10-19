# NIDS Testing Guide - Windows PowerShell

**Final Year B.Tech Project**
**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Department:** CSE - Cybersecurity

---

## Table of Contents
1. [Windows Environment Setup](#windows-environment-setup)
2. [Building NIDS on Windows](#building-nids-on-windows)
3. [PowerShell Testing Commands](#powershell-testing-commands)
4. [Test Scenarios for Windows](#test-scenarios-for-windows)
5. [Generating Test Traffic on Windows](#generating-test-traffic-on-windows)
6. [Automated Testing Scripts](#automated-testing-scripts)
7. [Troubleshooting Windows Issues](#troubleshooting-windows-issues)

---

## Windows Environment Setup

### Prerequisites Installation

**1. Install MSYS2**
```powershell
# Download from https://www.msys2.org/
# Install to C:\msys64 (default)

# After installation, open MSYS2 MINGW64 terminal
# Update package database
pacman -Syu

# Install build tools
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake mingw-w64-x86_64-make
pacman -S mingw-w64-x86_64-boost mingw-w64-x86_64-pcre
```

**2. Install Npcap**
```powershell
# Download from https://npcap.com/
# Run installer as Administrator
# ✅ Enable "Install Npcap in WinPcap API-compatible Mode"
# ✅ Enable "Support loopback traffic"
```

**3. Install Python and Dependencies**
```powershell
# Install Python 3.10+ from https://python.org
# Add to PATH during installation

# Install Python packages
pip install scapy numpy pandas scikit-learn
```

**4. Verify Installation**
```powershell
# Check Python
python --version

# Check GCC (in MSYS2 MINGW64 terminal)
gcc --version

# Check CMake
cmake --version
```

---

## Building NIDS on Windows

### Method 1: Using MSYS2 Terminal (Recommended)

**Open MSYS2 MINGW64 terminal:**
```bash
# Navigate to project
cd /c/Users/zsyed/Hybrid-IDS-MCP

# Create build directory
mkdir -p build
cd build

# Configure with CMake
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build . --config Release -j4

# Verify executables
ls -lh *.exe
```

**Expected output:**
```
-rwxr-xr-x 1 zsyed 197609 2.5M Oct 19 15:30 nids.exe
-rwxr-xr-x 1 zsyed 197609 1.8M Oct 19 15:30 sids.exe
-rwxr-xr-x 1 zsyed 197609 1.2M Oct 19 15:30 feature_extractor.exe
```

---

### Method 2: Using PowerShell with Visual Studio

**PowerShell (Run as Administrator):**
```powershell
# Navigate to project
cd C:\Users\zsyed\Hybrid-IDS-MCP

# Create build directory
New-Item -ItemType Directory -Path build -Force
Set-Location build

# Configure with Visual Studio
cmake .. -G "Visual Studio 17 2022" -A x64

# Build
cmake --build . --config Release

# Check binaries
Get-ChildItem .\Release\*.exe
```

---

## PowerShell Testing Commands

### Test Environment Setup

**Create Test Directories:**
```powershell
# Create test structure
New-Item -ItemType Directory -Path test_results -Force
New-Item -ItemType Directory -Path test_pcaps -Force
New-Item -ItemType Directory -Path test_logs -Force

# Set execution policy for scripts (one-time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Basic S-IDS Testing

**Test 1: Basic PCAP Analysis**

```powershell
# Navigate to build directory
cd C:\Users\zsyed\Hybrid-IDS-MCP\build

# Test with sample PCAP
.\sids.exe -r ..\test.pcap

# Check output
Get-Content ..\nids_alerts.log -Tail 20
```

**Expected PowerShell output:**
```
========================================
  Hybrid IDS - Signature Detection
========================================

[INFO] Loading signature rules...
[INFO] Loaded 6 signature rules

Active Rules:
-------------
  [1001] Port Scan Detection (MEDIUM)
  [1002] SQL Injection Attempt (HIGH)
  ...

Statistics:
  Total packets: 150
  Alerts generated: 3
```

---

**Test 2: List Network Interfaces**

```powershell
# List available network adapters
.\sids.exe --list-interfaces

# Or use PowerShell command
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status
```

**Example output:**
```
Available interfaces:
  1. Ethernet
  2. Wi-Fi
  3. Loopback Pseudo-Interface 1
```

---

**Test 3: Live Capture (Requires Administrator)**

```powershell
# Open PowerShell as Administrator

# Navigate to build directory
cd C:\Users\zsyed\Hybrid-IDS-MCP\build

# Start live capture on Ethernet
.\sids.exe -i "Ethernet"

# Or Wi-Fi
.\sids.exe -i "Wi-Fi"

# Stop with Ctrl+C
```

---

### Feature Extraction Testing

**Test 4: Extract Features to CSV**

```powershell
# Extract features from PCAP
.\nids.exe -r ..\test.pcap --extract-features --export-csv features.csv

# Check if CSV was created
Test-Path .\features.csv

# Count rows (flows)
(Get-Content .\features.csv | Measure-Object -Line).Lines

# View first few rows
Get-Content .\features.csv -Head 5
```

**PowerShell CSV Analysis:**
```powershell
# Import CSV for analysis
$features = Import-Csv .\features.csv

# Count total flows
$features.Count

# Show first flow
$features[0]

# Check for specific values
$features | Where-Object { $_.fwd_packets -gt 100 }
```

---

**Test 5: Real-time Feature Extraction**

```powershell
# Terminal 1 (PowerShell as Admin) - Start NIDS
cd C:\Users\zsyed\Hybrid-IDS-MCP\build
.\nids.exe -i "Ethernet" --extract-features --export-csv live_features.csv

# Terminal 2 (Regular PowerShell) - Monitor file
cd C:\Users\zsyed\Hybrid-IDS-MCP\build
Get-Content .\live_features.csv -Wait -Tail 10
```

---

## Test Scenarios for Windows

### Scenario 1: SQL Injection Detection

**Create test traffic using Python:**
```powershell
# Create test script
@"
from scapy.all import *

# SQL Injection payloads
payloads = [
    "' OR '1'='1",
    "' UNION SELECT * FROM users--",
    "admin'--",
    "1' AND 1=1--"
]

packets = []
for i, payload in enumerate(payloads):
    pkt = (IP(src="192.168.1.100", dst="10.0.0.50")/
           TCP(sport=12345+i, dport=80, flags="PA")/
           Raw(load=f"GET /search?q={payload} HTTP/1.1\r\nHost: victim.com\r\n\r\n"))
    packets.append(pkt)

wrpcap("sql_injection_test.pcap", packets)
print(f"Created sql_injection_test.pcap with {len(packets)} packets")
"@ | Out-File -FilePath test_sql.py -Encoding UTF8

# Run Python script
python test_sql.py

# Test with SIDS
.\sids.exe -r sql_injection_test.pcap

# Check alerts
Select-String -Path ..\nids_alerts.log -Pattern "1002"
```

**Validation:**
```powershell
# Count SQL injection alerts
(Select-String -Path ..\nids_alerts.log -Pattern '"rule_id": 1002').Count

# Show alert details
Get-Content ..\nids_alerts.log | ConvertFrom-Json | Where-Object { $_.rule_id -eq 1002 }
```

---

### Scenario 2: Port Scan Detection

**Generate port scan PCAP:**
```powershell
# Create port scan test
@"
from scapy.all import *

packets = []
# Generate SYN scan on ports 1-1000
for port in range(1, 1001):
    pkt = IP(src="192.168.1.100", dst="10.0.0.50")/TCP(sport=54321, dport=port, flags="S")
    packets.append(pkt)

wrpcap("port_scan_test.pcap", packets)
print(f"Created port_scan_test.pcap with {len(packets)} SYN packets")
"@ | Out-File -FilePath test_portscan.py -Encoding UTF8

python test_portscan.py
```

**Test and analyze:**
```powershell
# Run test
.\sids.exe -r port_scan_test.pcap

# Check for port scan alert (Rule 1001)
$alerts = Get-Content ..\nids_alerts.log | ConvertFrom-Json
$portscan_alerts = $alerts | Where-Object { $_.rule_id -eq 1001 }

Write-Host "Port scan alerts: $($portscan_alerts.Count)"
$portscan_alerts | Format-Table timestamp, severity, message
```

---

### Scenario 3: XSS Attack Detection

**Create XSS test:**
```powershell
@"
from scapy.all import *

xss_payloads = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "<svg onload=alert(1)>"
]

packets = []
for i, payload in enumerate(xss_payloads):
    pkt = (IP(src="192.168.1.100", dst="10.0.0.50")/
           TCP(sport=13000+i, dport=80, flags="PA")/
           Raw(load=f"GET /search?q={payload} HTTP/1.1\r\nHost: victim.com\r\n\r\n"))
    packets.append(pkt)

wrpcap("xss_test.pcap", packets)
print(f"Created xss_test.pcap with {len(packets)} XSS attempts")
"@ | Out-File -FilePath test_xss.py -Encoding UTF8

python test_xss.py
.\sids.exe -r xss_test.pcap
```

---

### Scenario 4: Combined Attack Test

**Comprehensive test with multiple attack types:**
```powershell
@"
from scapy.all import *
import random

packets = []

# 1. Normal traffic (baseline)
for i in range(50):
    pkt = (IP(src=f"192.168.1.{random.randint(10,250)}", dst="10.0.0.50")/
           TCP(sport=random.randint(10000,65000), dport=80, flags="PA")/
           Raw(load=f"GET /page{i}.html HTTP/1.1\r\nHost: example.com\r\n\r\n"))
    packets.append(pkt)

# 2. SQL Injection
sql_payloads = ["' OR 1=1--", "' UNION SELECT NULL--", "admin'--"]
for payload in sql_payloads:
    pkt = (IP(src="192.168.1.100", dst="10.0.0.50")/
           TCP(sport=12345, dport=80, flags="PA")/
           Raw(load=f"GET /login?user={payload} HTTP/1.1\r\n\r\n"))
    packets.append(pkt)

# 3. XSS
xss_payloads = ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"]
for payload in xss_payloads:
    pkt = (IP(src="192.168.1.101", dst="10.0.0.50")/
           TCP(sport=12346, dport=80, flags="PA")/
           Raw(load=f"GET /search?q={payload} HTTP/1.1\r\n\r\n"))
    packets.append(pkt)

# 4. Port Scan
for port in range(1, 101):
    pkt = IP(src="192.168.1.102", dst="10.0.0.50")/TCP(sport=54321, dport=port, flags="S")
    packets.append(pkt)

# 5. Directory Traversal
dir_payloads = ["../../../../etc/passwd", "..\\..\\..\\windows\\system32\\config\\sam"]
for payload in dir_payloads:
    pkt = (IP(src="192.168.1.103", dst="10.0.0.50")/
           TCP(sport=12347, dport=80, flags="PA")/
           Raw(load=f"GET /{payload} HTTP/1.1\r\n\r\n"))
    packets.append(pkt)

# Shuffle to mix attack and normal traffic
random.shuffle(packets)

wrpcap("comprehensive_test.pcap", packets)
print(f"Created comprehensive_test.pcap with {len(packets)} packets")
print(f"  - Normal traffic: 50")
print(f"  - SQL injection: {len(sql_payloads)}")
print(f"  - XSS attacks: {len(xss_payloads)}")
print(f"  - Port scan: 100")
print(f"  - Directory traversal: {len(dir_payloads)}")
"@ | Out-File -FilePath test_comprehensive.py -Encoding UTF8

python test_comprehensive.py
```

**Run comprehensive test:**
```powershell
# Clear previous logs
Remove-Item ..\nids_alerts.log -ErrorAction SilentlyContinue

# Run test
.\sids.exe -r comprehensive_test.pcap

# Analyze results
$alerts = Get-Content ..\nids_alerts.log | ConvertFrom-Json

# Count by rule type
Write-Host "`n=== Alert Summary ==="
$alerts | Group-Object rule_id | ForEach-Object {
    $ruleName = switch ($_.Name) {
        "1001" { "Port Scan" }
        "1002" { "SQL Injection" }
        "1003" { "XSS Attack" }
        "1004" { "Directory Traversal" }
        "1005" { "Suspicious User-Agent" }
        "1006" { "Large Payload" }
        default { "Unknown" }
    }
    Write-Host "$ruleName (Rule $($_.Name)): $($_.Count) alerts"
}

# Count by severity
Write-Host "`n=== Severity Distribution ==="
$alerts | Group-Object severity | ForEach-Object {
    Write-Host "$($_.Name): $($_.Count) alerts"
}
```

---

## Generating Test Traffic on Windows

### Method 1: Using Scapy (Python)

**Complete test traffic generator:**
```powershell
# Save this as generate_tests.ps1
$pythonScript = @"
from scapy.all import *
import os

def create_sql_injection_test():
    packets = []
    payloads = [
        "' OR '1'='1", "' UNION SELECT * FROM users--",
        "admin'--", "1' AND 1=1--", "' DROP TABLE users--"
    ]
    for i, payload in enumerate(payloads):
        pkt = (IP(src="192.168.1.100", dst="10.0.0.50")/
               TCP(sport=12345+i, dport=80, flags="PA")/
               Raw(load=f"GET /page?id={payload} HTTP/1.1\r\nHost: victim.com\r\n\r\n"))
        packets.append(pkt)
    wrpcap("sql_injection.pcap", packets)
    print(f"✓ Created sql_injection.pcap ({len(packets)} packets)")

def create_xss_test():
    packets = []
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)",
        "<svg onload=alert(1)>"
    ]
    for i, payload in enumerate(payloads):
        pkt = (IP(src="192.168.1.101", dst="10.0.0.50")/
               TCP(sport=13000+i, dport=80, flags="PA")/
               Raw(load=f"GET /search?q={payload} HTTP/1.1\r\n\r\n"))
        packets.append(pkt)
    wrpcap("xss_attack.pcap", packets)
    print(f"✓ Created xss_attack.pcap ({len(packets)} packets)")

def create_port_scan_test():
    packets = []
    for port in range(1, 1001):
        pkt = IP(src="192.168.1.102", dst="10.0.0.50")/TCP(sport=54321, dport=port, flags="S")
        packets.append(pkt)
    wrpcap("port_scan.pcap", packets)
    print(f"✓ Created port_scan.pcap ({len(packets)} packets)")

def create_directory_traversal_test():
    packets = []
    payloads = [
        "../../../../etc/passwd",
        "../../../windows/system32/config/sam",
        "..\\..\\..\\boot.ini",
        "..\\..\\..\\..\\..\\..\\..\\..\\..\\..\\.\\etc\\passwd"
    ]
    for i, payload in enumerate(payloads):
        pkt = (IP(src="192.168.1.103", dst="10.0.0.50")/
               TCP(sport=14000+i, dport=80, flags="PA")/
               Raw(load=f"GET /{payload} HTTP/1.1\r\n\r\n"))
        packets.append(pkt)
    wrpcap("dir_traversal.pcap", packets)
    print(f"✓ Created dir_traversal.pcap ({len(packets)} packets)")

def create_normal_traffic():
    packets = []
    for i in range(100):
        pkt = (IP(src="192.168.1.10", dst="10.0.0.50")/
               TCP(sport=20000+i, dport=80, flags="PA")/
               Raw(load=f"GET /page{i}.html HTTP/1.1\r\nHost: example.com\r\n\r\n"))
        packets.append(pkt)
    wrpcap("normal_traffic.pcap", packets)
    print(f"✓ Created normal_traffic.pcap ({len(packets)} packets)")

if __name__ == "__main__":
    os.makedirs("test_pcaps", exist_ok=True)
    os.chdir("test_pcaps")

    print("Generating test PCAP files...")
    create_sql_injection_test()
    create_xss_test()
    create_port_scan_test()
    create_directory_traversal_test()
    create_normal_traffic()
    print("\nAll test files created in test_pcaps/ directory")
"@

$pythonScript | Out-File -FilePath generate_all_tests.py -Encoding UTF8
python generate_all_tests.py
```

---

### Method 2: Capture Real Traffic

**Using Npcap with PowerShell:**
```powershell
# List interfaces
Get-NetAdapter

# Capture traffic (requires Npcap/WinPcap installed)
# Install dumpcap with Wireshark or use tshark

# Example with tshark (if installed)
tshark -i "Ethernet" -w normal_capture.pcap -c 1000

# Or use PowerShell + .NET (advanced)
# Requires Packet.Net library
```

---

## Automated Testing Scripts

### PowerShell Test Automation

**Create `Run-NIDSTests.ps1`:**
```powershell
<#
.SYNOPSIS
    Automated NIDS testing script for Windows
.DESCRIPTION
    Runs comprehensive tests on NIDS components
.AUTHOR
    Syed Misbah Uddin - Central University of Jammu
#>

param(
    [string]$BuildDir = ".\build",
    [string]$TestDir = ".\test_pcaps",
    [switch]$GenerateTraffic = $false,
    [switch]$Verbose = $false
)

# Colors for output
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Fail { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Test { Write-Host "🧪 $args" -ForegroundColor Yellow }

# Test results
$script:TestsPassed = 0
$script:TestsFailed = 0
$script:Results = @()

function Test-NIDS {
    param(
        [string]$TestName,
        [string]$PcapFile,
        [int]$ExpectedRuleId,
        [string]$Severity
    )

    Write-Test "Running: $TestName"

    # Clear previous log
    Remove-Item "$BuildDir\..\nids_alerts.log" -ErrorAction SilentlyContinue

    # Run SIDS
    $output = & "$BuildDir\sids.exe" -r "$PcapFile" 2>&1

    # Check if alerts were generated
    if (Test-Path "$BuildDir\..\nids_alerts.log") {
        $alerts = Get-Content "$BuildDir\..\nids_alerts.log" | ConvertFrom-Json

        # Check for expected rule
        $matchingAlerts = $alerts | Where-Object { $_.rule_id -eq $ExpectedRuleId }

        if ($matchingAlerts.Count -gt 0) {
            Write-Success "$TestName - PASSED ($($matchingAlerts.Count) alerts)"
            $script:TestsPassed++
            $script:Results += [PSCustomObject]@{
                Test = $TestName
                Status = "PASS"
                Alerts = $matchingAlerts.Count
                RuleID = $ExpectedRuleId
            }
        } else {
            Write-Fail "$TestName - FAILED (No matching alerts)"
            $script:TestsFailed++
            $script:Results += [PSCustomObject]@{
                Test = $TestName
                Status = "FAIL"
                Alerts = 0
                RuleID = $ExpectedRuleId
            }
        }
    } else {
        Write-Fail "$TestName - FAILED (No log file created)"
        $script:TestsFailed++
    }

    Start-Sleep -Milliseconds 500
}

# Main test execution
Write-Info "NIDS Automated Test Suite"
Write-Info "Author: Syed Misbah Uddin"
Write-Info "================================"

# Generate test traffic if requested
if ($GenerateTraffic) {
    Write-Info "Generating test traffic..."
    python generate_all_tests.py
}

# Check build exists
if (-not (Test-Path "$BuildDir\sids.exe")) {
    Write-Fail "SIDS executable not found. Build first!"
    exit 1
}

Write-Info "Starting tests..."

# Run tests
Test-NIDS -TestName "SQL Injection Detection" `
          -PcapFile "$TestDir\sql_injection.pcap" `
          -ExpectedRuleId 1002 `
          -Severity "HIGH"

Test-NIDS -TestName "XSS Attack Detection" `
          -PcapFile "$TestDir\xss_attack.pcap" `
          -ExpectedRuleId 1003 `
          -Severity "HIGH"

Test-NIDS -TestName "Port Scan Detection" `
          -PcapFile "$TestDir\port_scan.pcap" `
          -ExpectedRuleId 1001 `
          -Severity "MEDIUM"

Test-NIDS -TestName "Directory Traversal" `
          -PcapFile "$TestDir\dir_traversal.pcap" `
          -ExpectedRuleId 1004 `
          -Severity "HIGH"

# Results summary
Write-Info "`n================================"
Write-Info "Test Summary"
Write-Info "================================"
Write-Host "Total Tests: $($script:TestsPassed + $script:TestsFailed)"
Write-Success "Passed: $script:TestsPassed"
if ($script:TestsFailed -gt 0) {
    Write-Fail "Failed: $script:TestsFailed"
}

# Detailed results
$script:Results | Format-Table -AutoSize

# Save results to file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "test_results\nids_test_results_$timestamp.json"
$script:Results | ConvertTo-Json | Out-File $resultFile
Write-Info "Results saved to: $resultFile"
```

**Run the automated tests:**
```powershell
# Make script executable
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run tests with traffic generation
.\Run-NIDSTests.ps1 -GenerateTraffic

# Run tests (assuming PCAP files exist)
.\Run-NIDSTests.ps1

# Run with verbose output
.\Run-NIDSTests.ps1 -Verbose
```

---

## Troubleshooting Windows Issues

### Issue 1: "Npcap not found"

**Solution:**
```powershell
# Check if Npcap is installed
Test-Path "C:\Windows\System32\Npcap"

# If not installed, download and install
Start-Process "https://npcap.com/#download"

# After installation, verify
Get-Service npcap
```

---

### Issue 2: "Permission Denied" on live capture

**Solution:**
```powershell
# Run PowerShell as Administrator
# Right-click PowerShell icon → Run as Administrator

# Or use gsudo (if installed)
gsudo .\sids.exe -i "Ethernet"
```

---

### Issue 3: Interface not found

**Solution:**
```powershell
# List all network adapters
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status

# Use exact name from output
.\sids.exe -i "Ethernet"
.\sids.exe -i "Wi-Fi"

# Or get interface programmatically
$adapter = (Get-NetAdapter | Where-Object {$_.Status -eq "Up"})[0]
.\sids.exe -i $adapter.Name
```

---

### Issue 4: Python/Scapy issues

**Solution:**
```powershell
# Install/reinstall Scapy
pip uninstall scapy
pip install scapy

# Install Npcap Python bindings
pip install pypcap

# Test Scapy
python -c "from scapy.all import *; print('Scapy OK')"
```

---

### Issue 5: Build errors with MSYS2

**Solution:**
```powershell
# Update MSYS2
pacman -Syu

# Reinstall dependencies
pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake

# Clean build
Remove-Item -Recurse -Force build
New-Item -ItemType Directory build
cd build
cmake .. -G "MinGW Makefiles"
cmake --build . -j4
```

---

## Performance Testing on Windows

### CPU and Memory Monitoring

**Real-time monitoring:**
```powershell
# Start NIDS in background
$nidsProcess = Start-Process -FilePath ".\sids.exe" `
                              -ArgumentList "-r large_traffic.pcap" `
                              -PassThru

# Monitor performance
while (!$nidsProcess.HasExited) {
    $cpu = (Get-Counter "\Process(sids)\% Processor Time").CounterSamples[0].CookedValue
    $mem = (Get-Process -Id $nidsProcess.Id).WorkingSet64 / 1MB

    Write-Host "CPU: $([math]::Round($cpu, 2))% | Memory: $([math]::Round($mem, 2)) MB"
    Start-Sleep -Seconds 1
}
```

---

### Throughput Testing

**Measure processing speed:**
```powershell
# Generate large PCAP (if needed)
python -c @"
from scapy.all import *
packets = [IP()/TCP()/Raw(load='X'*100) for _ in range(10000)]
wrpcap('large_test.pcap', packets)
"@

# Measure time
$start = Get-Date
.\sids.exe -r large_test.pcap
$end = Get-Date
$duration = ($end - $start).TotalSeconds

# Calculate throughput
$packetCount = 10000
$throughput = $packetCount / $duration

Write-Host "`nPerformance Metrics:"
Write-Host "  Packets: $packetCount"
Write-Host "  Time: $([math]::Round($duration, 2)) seconds"
Write-Host "  Throughput: $([math]::Round($throughput, 0)) packets/second"
```

---

## Test Results Template (PowerShell)

**Generate HTML test report:**
```powershell
$html = @"
<!DOCTYPE html>
<html>
<head>
    <title>NIDS Test Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .pass { color: green; font-weight: bold; }
        .fail { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>NIDS Test Results</h1>
    <p><strong>Date:</strong> $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p>
    <p><strong>Tester:</strong> Syed Misbah Uddin</p>
    <p><strong>Institution:</strong> Central University of Jammu</p>

    <h2>Test Summary</h2>
    <table>
        <tr>
            <th>Test Name</th>
            <th>Status</th>
            <th>Alerts Generated</th>
            <th>Expected Rule ID</th>
        </tr>
"@

foreach ($result in $script:Results) {
    $statusClass = if ($result.Status -eq "PASS") { "pass" } else { "fail" }
    $html += @"
        <tr>
            <td>$($result.Test)</td>
            <td class="$statusClass">$($result.Status)</td>
            <td>$($result.Alerts)</td>
            <td>$($result.RuleID)</td>
        </tr>
"@
}

$html += @"
    </table>

    <h2>Overall Statistics</h2>
    <p>Total Tests: $($script:TestsPassed + $script:TestsFailed)</p>
    <p class="pass">Passed: $script:TestsPassed</p>
    <p class="fail">Failed: $script:TestsFailed</p>
</body>
</html>
"@

$html | Out-File "test_results\report_$(Get-Date -Format 'yyyyMMdd_HHmmss').html"
```

---

**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Project:** Final Year B.Tech - Hybrid IDS
**Last Updated:** October 2025
**Document Purpose:** Windows PowerShell testing guide for NIDS component
