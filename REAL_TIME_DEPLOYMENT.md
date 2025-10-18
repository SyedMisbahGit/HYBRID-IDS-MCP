# 🌐 Real-Time Network Traffic Deployment Guide

**Purpose:** Deploy Hybrid IDS to monitor live network traffic in your environment

---

## 🎯 Prerequisites

### **For Windows (Your Current System)**

1. **Install Npcap** (Windows Packet Capture)
   ```powershell
   # Download from: https://npcap.com/#download
   # Install with "WinPcap API-compatible Mode" enabled
   ```

2. **Install MinGW-w64 or Visual Studio**

   **Option A: MinGW-w64 (Recommended for quick setup)**
   ```powershell
   # Download MSYS2 from: https://www.msys2.org/
   # After installation, open MSYS2 terminal and run:
   pacman -Syu
   pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake make
   pacman -S mingw-w64-x86_64-libpcap
   ```

   **Option B: Visual Studio**
   - Install Visual Studio 2019+ with C++ Development Tools
   - Install CMake from https://cmake.org/download/

3. **Install Python 3.10+**
   ```powershell
   # Download from: https://www.python.org/downloads/
   # Or use winget:
   winget install Python.Python.3.11
   ```

4. **Install Python Dependencies**
   ```powershell
   cd C:\Users\zsyed\Hybrid-IDS-MCP

   # Create virtual environment
   python -m venv venv

   # Activate it
   venv\Scripts\activate.bat

   # Install packages
   pip install numpy pandas scikit-learn pyzmq pyyaml
   ```

---

## 🔨 Build the System

### **Windows Build (MinGW)**

```bash
# Open MSYS2 MinGW 64-bit terminal
cd /c/Users/zsyed/Hybrid-IDS-MCP

# Create build directory
mkdir -p build
cd build

# Configure with CMake
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release

# Build
mingw32-make -j4

# Verify binaries
ls -lh sids.exe nids.exe
```

### **Alternative: Direct Compilation (No CMake)**

```bash
# In MSYS2 MinGW terminal
cd /c/Users/zsyed/Hybrid-IDS-MCP

# Compile S-IDS
g++ -std=c++17 -O3 -o sids.exe \
    src/nids/common/types.cpp \
    src/nids/parser/packet_parser.cpp \
    src/nids/parser/protocol_decoder.cpp \
    src/nids/rules/rule_engine.cpp \
    src/nids/features/connection_tracker.cpp \
    src/nids/features/feature_extractor.cpp \
    src/nids/ipc/zmq_publisher.cpp \
    src/nids/sids_main.cpp \
    -I./src \
    -lws2_32 -lwpcap \
    -lpthread

# Compile Complete NIDS
g++ -std=c++17 -O3 -o nids.exe \
    src/nids/common/types.cpp \
    src/nids/parser/packet_parser.cpp \
    src/nids/parser/protocol_decoder.cpp \
    src/nids/rules/rule_engine.cpp \
    src/nids/features/connection_tracker.cpp \
    src/nids/features/feature_extractor.cpp \
    src/nids/ipc/zmq_publisher.cpp \
    src/nids/nids_main.cpp \
    -I./src \
    -lws2_32 -lwpcap \
    -lpthread
```

---

## 🌐 Real-Time Monitoring Scenarios

### **Scenario 1: Monitor Your Home/Office Network**

#### **Step 1: Find Your Network Interface**

```powershell
# PowerShell - List network interfaces
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status

# Or in Command Prompt
ipconfig /all
```

Example output:
```
Name                      InterfaceDescription                    Status
----                      --------------------                    ------
Ethernet                  Intel(R) Ethernet Connection            Up
Wi-Fi                     Realtek RTL8822BE 802.11ac              Up
```

#### **Step 2: Run S-IDS on Live Traffic**

```powershell
# Run as Administrator!
# Right-click PowerShell/CMD and select "Run as administrator"

cd C:\Users\zsyed\Hybrid-IDS-MCP

# Monitor Wi-Fi interface
.\sids.exe -i "Wi-Fi"

# Or Ethernet
.\sids.exe -i "Ethernet"
```

**What You'll See:**
```
========================================
  Hybrid IDS - Signature Detection
========================================

[INFO] Loading signature rules...
[INFO] Loaded 6 signature rules
[INFO] Starting live capture on interface: Wi-Fi

Press Ctrl+C to stop...

[STATS] Packets: 150 | TCP: 120 | UDP: 25 | Alerts: 0 | Rate: 75.5 pkt/s

[2025-10-18 15:23:45] [MEDIUM] Port Scan Detection (Rule ID: 1003)
  192.168.1.105:54321 -> 192.168.1.1:22 [TCP]
  SYN packet to commonly scanned port

[STATS] Packets: 300 | TCP: 240 | UDP: 50 | Alerts: 1 | Rate: 150.2 pkt/s
```

#### **Step 3: Generate Some Test Traffic**

Open another terminal and generate traffic:

```powershell
# Test DNS
nslookup google.com

# Test HTTP (if you have curl)
curl http://example.com

# Test SSH (if you have ssh)
ssh user@somehost.com

# Or browse websites in your browser
```

You should see packets being captured in real-time!

---

### **Scenario 2: Full System with AI Detection**

#### **Terminal 1: Start AI Engine**

```powershell
cd C:\Users\zsyed\Hybrid-IDS-MCP

# Activate Python virtual environment
venv\Scripts\activate.bat

# Start AI inference engine
python src\ai\inference\zmq_subscriber.py --simulate
```

**Output:**
```
============================================================
  Hybrid IDS - AI Inference Engine
  Real-time Anomaly Detection
============================================================

[INFO] Loading models...
[INFO] Creating dummy models for testing...
[INFO] Dummy models created successfully
Waiting for feature vectors from NIDS...
Press Ctrl+C to stop
```

#### **Terminal 2: Capture Live Traffic (Future)**

Once you have the build working:

```powershell
# In Administrator PowerShell
cd C:\Users\zsyed\Hybrid-IDS-MCP

# Run NIDS with AI integration
.\nids.exe -i "Wi-Fi" --extract-features --zmq tcp://*:5555
```

---

### **Scenario 3: Capture Traffic for Later Analysis**

Instead of live monitoring, capture traffic to PCAP file:

#### **Using Windows Built-in Tools**

```powershell
# Install Wireshark (includes command-line dumpcap)
# Download from: https://www.wireshark.org/download.html

# Capture 1000 packets to file
dumpcap -i "Wi-Fi" -c 1000 -w capture.pcap

# Then analyze with your IDS
.\sids.exe -r capture.pcap
```

#### **Using PowerShell Packet Capture (Windows 10+)**

```powershell
# Start packet capture
New-NetEventSession -Name "IDSCapture" -CaptureMode SaveToFile -LocalFilePath "C:\Users\zsyed\Hybrid-IDS-MCP\live_capture.etl"
Add-NetEventPacketCaptureProvider -SessionName "IDSCapture"
Start-NetEventSession -Name "IDSCapture"

# Let it capture for a while...
# Browse websites, use apps, etc.

# Stop capture
Stop-NetEventSession -Name "IDSCapture"
Remove-NetEventSession -Name "IDSCapture"

# Convert ETL to PCAP (requires etl2pcapng)
# Download from: https://github.com/microsoft/etl2pcapng
etl2pcapng live_capture.etl live_capture.pcap

# Analyze
.\sids.exe -r live_capture.pcap
```

---

## 🧪 Testing with Real Attack Patterns

### **Test 1: Port Scan Detection**

Scan your own machine (safe test):

```powershell
# Using nmap (install from: https://nmap.org/download.html)
nmap -sS localhost

# Or using PowerShell
1..100 | ForEach-Object {
    Test-NetConnection -ComputerName localhost -Port $_ -InformationLevel Quiet
}
```

Your IDS should detect: **Port Scan Detection (Rule ID: 1003)**

### **Test 2: HTTP Traffic Analysis**

```powershell
# Generate HTTP requests
curl http://httpbin.org/get
curl http://httpbin.org/post -X POST -d "test=data"
curl http://httpbin.org/html
```

Your IDS should parse HTTP protocol and log requests.

### **Test 3: DNS Queries**

```powershell
# Generate DNS traffic
nslookup google.com
nslookup facebook.com
nslookup amazon.com
nslookup microsoft.com
```

Your IDS should detect DNS queries (Rule ID: 1005 if enabled).

---

## 📊 Real-Time Monitoring Dashboard

### **View Live Alerts**

```powershell
# In another terminal, tail the alert log
Get-Content -Path nids_alerts.log -Wait -Tail 10
```

### **View Statistics**

The NIDS prints statistics every 5 seconds:

```
========================================
  NIDS Real-time Statistics
========================================
Total Packets:    1500
Total Bytes:      1245678 (1.19 MB)

By Protocol:
  TCP:            1200
  UDP:            250
  ICMP:           10
  Other:          40

Performance:
  Packets/sec:    150.50
  Throughput:     1.23 Mbps

Alerts:
  Total:          5
  Low:            2
  Medium:         3
  High:           0
  Critical:       0
========================================
```

---

## 🔍 Common Real-World Use Cases

### **Use Case 1: Monitor Home Network for IoT Devices**

Many IoT devices have security issues. Monitor them:

```powershell
# Capture traffic from your home network
.\nids.exe -i "Wi-Fi" --extract-features --export-csv iot_traffic.csv

# Analyze the CSV for suspicious patterns
# Look for unusual ports, high packet rates, etc.
```

### **Use Case 2: Detect Malware Communication**

Monitor for suspicious outbound connections:

```powershell
# Run NIDS and watch for:
# - Connections to unusual ports
# - High-frequency DNS queries
# - Large data transfers
# - Connections to known bad IPs (add custom rules)

.\sids.exe -i "Ethernet"
```

### **Use Case 3: Network Troubleshooting**

Use the feature extraction to understand traffic patterns:

```powershell
# Capture during problem period
.\nids.exe -i "Wi-Fi" --export-csv troubleshoot.csv

# Analyze CSV:
# - Packet loss (RST flags)
# - Retransmissions
# - Connection failures
```

### **Use Case 4: Security Audit**

Capture a day's worth of traffic for analysis:

```powershell
# Morning: Start capture
.\nids.exe -i "Ethernet" --export-csv daily_audit.csv > audit.log 2>&1

# Evening: Stop with Ctrl+C
# Review audit.log and daily_audit.csv
```

---

## 🎓 Step-by-Step: First Real-Time Test

### **Complete Beginner Guide**

**Step 1: Simple PCAP Test First**

```powershell
# Generate test traffic
python scripts\generate_test_traffic.py my_test.pcap

# Analyze it
.\sids.exe -r my_test.pcap
```

**Step 2: Capture Real Traffic to File**

```powershell
# Install Wireshark if not already
# Then capture 100 packets:
dumpcap -i "Wi-Fi" -c 100 -w real_traffic.pcap

# Analyze
.\sids.exe -r real_traffic.pcap
```

**Step 3: Live Capture (Short Duration)**

```powershell
# As Administrator
.\sids.exe -i "Wi-Fi"

# Let it run for 30 seconds
# Open a browser, visit a few websites
# Press Ctrl+C to stop

# Check alerts
type nids_alerts.log
```

**Step 4: Full System with Features**

```powershell
# As Administrator
.\nids.exe -i "Wi-Fi" --extract-features --export-csv live_features.csv

# Let it run for 5 minutes
# Do various network activities
# Press Ctrl+C to stop

# Check results
notepad live_features.csv
```

---

## 📈 Performance Tuning for Real-Time

### **Optimize for High-Speed Networks**

```powershell
# Use Release build (faster)
cmake .. -DCMAKE_BUILD_TYPE=Release

# Disable features you don't need
.\nids.exe -i "Wi-Fi" --no-protocols --no-connections

# Only signatures (fastest)
.\sids.exe -i "Wi-Fi"
```

### **Reduce CPU Usage**

```powershell
# Limit packet capture
# Capture only TCP on port 80/443
.\nids.exe -i "Wi-Fi"  # Add BPF filter support later
```

---

## 🛡️ Security Considerations

### **Running as Administrator**

Windows requires admin privileges for packet capture:

```powershell
# Always run as Administrator
# Right-click PowerShell → "Run as administrator"
```

### **Firewall Configuration**

If using ZMQ:

```powershell
# Allow TCP port 5555
New-NetFirewallRule -DisplayName "Hybrid IDS ZMQ" -Direction Inbound -Protocol TCP -LocalPort 5555 -Action Allow
```

### **Privacy**

```powershell
# Be careful capturing sensitive data
# The IDS logs packet contents for HTTP
# Only run on networks you own or have permission to monitor
```

---

## 🔧 Troubleshooting Real-Time Capture

### **Issue: "No suitable device found"**

```powershell
# Solution 1: Install Npcap
# Download from: https://npcap.com/#download

# Solution 2: Check interface names
Get-NetAdapter
```

### **Issue: "Access denied" or "Permission denied"**

```powershell
# Solution: Run as Administrator
# Right-click → "Run as administrator"
```

### **Issue: No packets captured**

```powershell
# Check if interface is up
Get-NetAdapter | Where-Object {$_.Status -eq "Up"}

# Check if Npcap service is running
Get-Service npcap

# Restart Npcap service
Restart-Service npcap
```

### **Issue: Too many packets, system slow**

```powershell
# Capture fewer packets
# Use Wireshark to capture with filters:
dumpcap -i "Wi-Fi" -f "tcp port 80 or tcp port 443" -w filtered.pcap

# Then analyze
.\sids.exe -r filtered.pcap
```

---

## 📋 Quick Reference: Real-Time Commands

### **Live Monitoring**

```powershell
# Basic signature detection
.\sids.exe -i "Wi-Fi"

# Full NIDS with features
.\nids.exe -i "Ethernet" --extract-features

# Export features to CSV
.\nids.exe -i "Wi-Fi" --export-csv output.csv

# With AI (requires ZMQ)
.\nids.exe -i "Ethernet" --zmq tcp://*:5555
```

### **File Analysis**

```powershell
# Analyze PCAP
.\sids.exe -r capture.pcap

# Extract features
.\nids.exe -r capture.pcap --export-csv features.csv

# Disable certain features
.\nids.exe -r capture.pcap --no-protocols
```

---

## 🎯 Next Steps

1. **Build the system** (see build commands above)
2. **Test with PCAP** file first
3. **Capture real traffic** with Wireshark/dumpcap
4. **Analyze captured traffic** with S-IDS
5. **Try live capture** for short durations
6. **Deploy for monitoring** your network

---

## 📞 Getting Help

- **Build Issues:** See [COMPLETE_BUILD_GUIDE.md](COMPLETE_BUILD_GUIDE.md)
- **Usage Issues:** See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Windows Specific:** This document

---

**Status:** Ready for real-time deployment!
**Platform:** Windows 10/11 with Npcap
**Last Updated:** 2025-10-18
