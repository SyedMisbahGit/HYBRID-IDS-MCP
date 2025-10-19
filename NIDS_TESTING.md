# NIDS Testing Guide - Complete Testing Methodology

**Final Year B.Tech Project**
**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Department:** CSE - Cybersecurity

---

## Table of Contents
1. [Testing Overview](#testing-overview)
2. [Setting Up Test Environment](#setting-up-test-environment)
3. [Testing S-IDS (Tier 1)](#testing-s-ids-tier-1)
4. [Testing A-IDS (Tier 2)](#testing-a-ids-tier-2)
5. [Integration Testing](#integration-testing)
6. [Performance Testing](#performance-testing)
7. [Creating Custom Test Cases](#creating-custom-test-cases)

---

## Testing Overview

### Testing Objectives

1. **Functional Testing**: Verify each component works correctly
2. **Integration Testing**: Verify two-tier pipeline functions as designed
3. **Performance Testing**: Measure throughput and latency
4. **Accuracy Testing**: Measure detection rates and false positives

### Test Levels

```
Level 1: Unit Tests (Individual components)
    ↓
Level 2: Component Tests (S-IDS, A-IDS separately)
    ↓
Level 3: Integration Tests (Two-tier pipeline)
    ↓
Level 4: System Tests (NIDS + HIDS + Dashboard)
    ↓
Level 5: Performance & Stress Tests
```

---

## Setting Up Test Environment

### Prerequisites

```bash
# 1. Build the NIDS components
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j4

# 2. Verify binaries exist
ls -lh sids nids feature_extractor

# 3. Create test directories
mkdir -p test_results
mkdir -p test_pcaps
mkdir -p test_logs
```

### Download Test PCAP Files

```bash
# Create test data directory
cd test_pcaps

# Option 1: Use your own captures
sudo tcpdump -i eth0 -w normal_traffic.pcap -c 1000

# Option 2: Download public datasets
# CIC-IDS2017 sample
wget https://www.unb.ca/cic/datasets/ids-2017.html

# Option 3: Generate synthetic traffic (see below)
```

---

## Testing S-IDS (Tier 1)

### Test 1: Basic Functionality

**Objective:** Verify S-IDS can read PCAP and detect known patterns

**Command:**
```bash
cd build
./sids -r ../test.pcap
```

**Expected Output:**
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
  [1003] XSS Attack Attempt (HIGH)
  [1004] Directory Traversal (HIGH)
  [1005] Suspicious User-Agent (LOW)
  [1006] Large Payload (MEDIUM)

[INFO] Processing PCAP file: ../test.pcap

[INFO] Processing complete
Statistics:
  Total packets: 150
  Alerts generated: 3
    HIGH: 2
    MEDIUM: 1
```

**Validation:**
- ✅ All rules loaded
- ✅ PCAP file opened successfully
- ✅ Packets processed without errors
- ✅ Alerts logged to `nids_alerts.log`

---

### Test 2: SQL Injection Detection

**Create Test PCAP:**
```bash
# Generate HTTP traffic with SQL injection
curl "http://testphp.vulnweb.com/artists.php?artist=1' OR '1'='1"
```

Or create manually with `test_sql_injection.py`:
```python
from scapy.all import *

# Create packet with SQL injection in HTTP GET
ip = IP(src="192.168.1.100", dst="10.0.0.50")
tcp = TCP(sport=12345, dport=80, flags="PA")
http = "GET /page?id=1' OR '1'='1 HTTP/1.1\r\nHost: victim.com\r\n\r\n"

packet = ip/tcp/Raw(load=http)
wrpcap("sql_injection.pcap", packet)
```

**Test:**
```bash
./sids -r sql_injection.pcap
```

**Expected Alert:**
```json
{
  "timestamp": "2025-10-19T14:30:15",
  "rule_id": 1002,
  "severity": "HIGH",
  "message": "SQL Injection Attempt",
  "src_ip": "192.168.1.100",
  "src_port": 12345,
  "dst_ip": "10.0.0.50",
  "dst_port": 80,
  "protocol": "TCP",
  "matched_pattern": "' OR '1'='1"
}
```

**Validation:**
- ✅ Check `nids_alerts.log` contains SQL injection alert
- ✅ Verify rule_id is 1002
- ✅ Severity is HIGH
- ✅ Source and destination IPs are correct

---

### Test 3: Port Scan Detection

**Generate Port Scan:**
```bash
# Using nmap
nmap -sS -p 1-100 192.168.1.1

# Or capture existing scan
sudo tcpdump -i eth0 -w port_scan.pcap 'tcp[tcpflags] == tcp-syn'
```

**Test:**
```bash
./sids -r port_scan.pcap
```

**Expected Behavior:**
- Detects multiple SYN packets to different ports
- Triggers Rule 1001 (Port Scan Detection)
- Alert includes number of ports scanned

---

### Test 4: XSS Attack Detection

**Create XSS Test:**
```python
from scapy.all import *

ip = IP(src="192.168.1.100", dst="10.0.0.50")
tcp = TCP(sport=12345, dport=80, flags="PA")
http = "GET /search?q=<script>alert('XSS')</script> HTTP/1.1\r\nHost: victim.com\r\n\r\n"

packet = ip/tcp/Raw(load=http)
wrpcap("xss_attack.pcap", packet)
```

**Test:**
```bash
./sids -r xss_attack.pcap
```

**Expected Alert:**
- Rule ID: 1003
- Message: "XSS Attack Attempt"
- Matched pattern: "<script>"

---

### Test 5: Directory Traversal

**Create Test:**
```python
from scapy.all import *

ip = IP(src="192.168.1.100", dst="10.0.0.50")
tcp = TCP(sport=12345, dport=80, flags="PA")
http = "GET /../../../../etc/passwd HTTP/1.1\r\nHost: victim.com\r\n\r\n"

packet = ip/tcp/Raw(load=http)
wrpcap("dir_traversal.pcap", packet)
```

**Test & Validate:**
```bash
./sids -r dir_traversal.pcap
# Check for Rule 1004 alert
grep "1004" nids_alerts.log
```

---

### Test 6: Multiple Attacks in One PCAP

**Create Combined Test:**
```python
from scapy.all import *

packets = []

# SQL Injection
packets.append(IP(dst="10.0.0.50")/TCP(dport=80)/Raw(load="GET /page?id=' OR 1=1-- HTTP/1.1\r\n\r\n"))

# XSS
packets.append(IP(dst="10.0.0.50")/TCP(dport=80)/Raw(load="GET /search?q=<script>alert(1)</script> HTTP/1.1\r\n\r\n"))

# Port Scan (multiple SYN packets)
for port in range(1, 101):
    packets.append(IP(dst="10.0.0.50")/TCP(dport=port, flags="S"))

# Directory Traversal
packets.append(IP(dst="10.0.0.50")/TCP(dport=80)/Raw(load="GET /../../etc/passwd HTTP/1.1\r\n\r\n"))

wrpcap("combined_attacks.pcap", packets)
```

**Test:**
```bash
./sids -r combined_attacks.pcap
```

**Expected:**
- Multiple alerts in log
- Different severity levels
- All 4 attack types detected

---

## Testing A-IDS (Tier 2)

### Test 7: Feature Extraction

**Objective:** Verify feature extractor generates 78 features correctly

**Command:**
```bash
./nids -r test.pcap --extract-features --export-csv features.csv
```

**Validation:**
```bash
# Check CSV was created
ls -lh features.csv

# Count columns (should be 78 + metadata)
head -1 features.csv | tr ',' '\n' | wc -l

# Check for valid values (no NaN or Inf)
grep -c "NaN\|Inf" features.csv
# Should be 0

# View sample
head -5 features.csv | column -t -s,
```

**Expected features.csv structure:**
```csv
flow_id,duration,fwd_packets,bwd_packets,fwd_bytes,bwd_bytes,...
192.168.1.1:12345-10.0.0.50:80,120.5,50,45,15000,12000,...
192.168.1.2:54321-10.0.0.50:443,85.2,30,28,9500,8200,...
```

---

### Test 8: Flow Tracking

**Objective:** Verify bidirectional flow tracking

**Create Test with Bidirectional Traffic:**
```python
from scapy.all import *

packets = []

# Forward packets (client → server)
for i in range(10):
    packets.append(IP(src="192.168.1.100", dst="10.0.0.50")/
                   TCP(sport=12345, dport=80, seq=i*100)/
                   Raw(load="X"*100))

# Backward packets (server → client)
for i in range(8):
    packets.append(IP(src="10.0.0.50", dst="192.168.1.100")/
                   TCP(sport=80, dport=12345, seq=i*100)/
                   Raw(load="Y"*150))

wrpcap("bidirectional_flow.pcap", packets)
```

**Test:**
```bash
./nids -r bidirectional_flow.pcap --extract-features --export-csv flow_test.csv
```

**Validate:**
```bash
# Check flow features
cat flow_test.csv

# Expected:
# - fwd_packets: 10
# - bwd_packets: 8
# - fwd_bytes: ~1000
# - bwd_bytes: ~1200
```

---

### Test 9: ML Integration (ZeroMQ)

**Objective:** Test feature publishing to AI engine

**Terminal 1 - Start AI Engine:**
```bash
cd src/ai/inference
python zmq_subscriber.py --model-dir ../../../models
```

**Terminal 2 - Start NIDS:**
```bash
cd build
./nids -i eth0 --extract-features --zmq tcp://localhost:5555
```

**Validation:**
- AI engine receives features
- Features are processed by ML models
- Anomalies logged to `ai_alerts.log`

---

## Integration Testing

### Test 10: Two-Tier Pipeline

**Objective:** Verify complete S-IDS → A-IDS flow

**Setup:**
```bash
# Terminal 1: AI Engine
python src/ai/inference/zmq_subscriber.py --model-dir models/

# Terminal 2: Full NIDS
./build/nids -r test_pcaps/mixed_traffic.pcap --extract-features
```

**Test Scenario:**
1. PCAP contains both known attacks and anomalous traffic
2. S-IDS should catch known attacks → `nids_alerts.log`
3. Unknown traffic → A-IDS → `ai_alerts.log`

**Validation:**
```bash
# Count S-IDS alerts
wc -l nids_alerts.log

# Count A-IDS alerts
wc -l ai_alerts.log

# Verify no overlap (same packet not in both logs)
```

---

### Test 11: Live Capture Test

**Objective:** Test real-time detection on live network

**Preparation:**
```bash
# Get interface name
ip addr show  # Linux
./nids --list-interfaces  # or use tool
```

**Test (requires root/admin):**
```bash
# Linux
sudo ./sids -i eth0

# Windows (run as Administrator)
./sids.exe -i "Ethernet"
```

**Generate Test Traffic:**
```bash
# In another terminal
curl "http://testphp.vulnweb.com/artists.php?artist=1' OR '1'='1"
nmap -sS -p 80,443 scanme.nmap.org
```

**Validation:**
- Alerts appear in real-time
- Timestamps are current
- No packet drops (check statistics)

---

## Performance Testing

### Test 12: Throughput Measurement

**Objective:** Measure packets/second processing rate

**Generate High-Volume PCAP:**
```bash
# Capture large traffic sample
sudo tcpdump -i eth0 -w large_traffic.pcap -c 100000
```

**Test with Statistics:**
```bash
time ./sids -r large_traffic.pcap --stats
```

**Calculate Throughput:**
```
Throughput = Total Packets / Time Elapsed
Target: >50,000 packets/second
```

---

### Test 13: Latency Measurement

**Objective:** Measure per-packet processing time

**Method:**
```bash
# Run with profiling
./sids -r test.pcap --profile

# Or use time command
time ./sids -r test.pcap

# Calculate average
# Avg Latency = Total Time / Packet Count
```

**Targets:**
- S-IDS: <1ms per packet
- Feature Extraction: <5ms per flow

---

### Test 14: Memory Usage

**Objective:** Monitor memory consumption

**Linux:**
```bash
# Run in background
./nids -r large_traffic.pcap &
PID=$!

# Monitor memory
while kill -0 $PID 2>/dev/null; do
    ps -p $PID -o rss,vsz,cmd
    sleep 1
done
```

**Windows:**
```powershell
# Task Manager or
Get-Process sids | Select-Object WorkingSet, VirtualMemorySize
```

**Target:** <500MB for normal operation

---

## Creating Custom Test Cases

### Test Case Template

```yaml
test_name: "Custom SQL Injection Test"
category: "S-IDS"
attack_type: "SQL Injection"
expected_rule: 1002
severity: "HIGH"

steps:
  1. Create PCAP with SQL injection payload
  2. Run: ./sids -r test.pcap
  3. Verify alert in nids_alerts.log
  4. Check alert matches expected pattern

validation:
  - Alert generated: true
  - Rule ID: 1002
  - Severity: HIGH
  - No false positives: true
```

---

### Generating Synthetic Traffic

**Using Scapy:**
```python
#!/usr/bin/env python3
from scapy.all import *
import random

def generate_normal_traffic(count=100):
    """Generate normal HTTP traffic"""
    packets = []
    for i in range(count):
        src_ip = f"192.168.1.{random.randint(1, 254)}"
        dst_ip = "10.0.0.50"
        src_port = random.randint(10000, 65000)

        pkt = (IP(src=src_ip, dst=dst_ip)/
               TCP(sport=src_port, dport=80, flags="PA")/
               Raw(load=f"GET /page{i}.html HTTP/1.1\r\nHost: example.com\r\n\r\n"))
        packets.append(pkt)

    return packets

def generate_sql_injection():
    """Generate SQL injection attack"""
    payloads = [
        "' OR '1'='1",
        "' UNION SELECT * FROM users--",
        "'; DROP TABLE users--",
        "1' AND 1=1--"
    ]

    packets = []
    for payload in payloads:
        pkt = (IP(src="192.168.1.100", dst="10.0.0.50")/
               TCP(sport=12345, dport=80, flags="PA")/
               Raw(load=f"GET /search?q={payload} HTTP/1.1\r\nHost: victim.com\r\n\r\n"))
        packets.append(pkt)

    return packets

def generate_port_scan():
    """Generate port scan"""
    packets = []
    for port in range(1, 1001):  # Scan ports 1-1000
        pkt = (IP(src="192.168.1.100", dst="10.0.0.50")/
               TCP(sport=54321, dport=port, flags="S"))  # SYN scan
        packets.append(pkt)

    return packets

# Generate complete test set
all_packets = []
all_packets.extend(generate_normal_traffic(100))
all_packets.extend(generate_sql_injection())
all_packets.extend(generate_port_scan())

# Shuffle to mix normal and attack traffic
random.shuffle(all_packets)

# Write to PCAP
wrpcap("comprehensive_test.pcap", all_packets)
print(f"Generated {len(all_packets)} packets")
```

---

## Test Results Documentation

### Results Template

```markdown
# NIDS Test Results

**Date:** 2025-10-19
**Tester:** Syed Misbah Uddin
**Version:** NIDS v1.0.0

## Test Summary

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| T01 | Basic Functionality | ✅ PASS | All rules loaded |
| T02 | SQL Injection | ✅ PASS | Detected correctly |
| T03 | Port Scan | ✅ PASS | Alert generated |
| T04 | XSS Attack | ✅ PASS | Pattern matched |
| T05 | Directory Traversal | ✅ PASS | High severity alert |
| T06 | Multiple Attacks | ✅ PASS | All detected |
| T07 | Feature Extraction | ✅ PASS | 78 features correct |
| T08 | Flow Tracking | ✅ PASS | Bidirectional flows |
| T09 | ML Integration | ✅ PASS | ZMQ working |
| T10 | Two-Tier Pipeline | ✅ PASS | No overlaps |
| T11 | Live Capture | ✅ PASS | Real-time detection |
| T12 | Throughput | ✅ PASS | 75,000 pkt/s |
| T13 | Latency | ✅ PASS | <1ms avg |
| T14 | Memory Usage | ✅ PASS | 320MB peak |

## Performance Metrics

- **Throughput:** 75,000 packets/second
- **Latency:** 0.8ms average
- **Memory:** 320MB peak usage
- **Detection Rate:** 95% (known attacks)
- **False Positive Rate:** 2.5%

## Issues Found

None

## Recommendations

1. Increase rule set for broader coverage
2. Optimize flow timeout for better performance
3. Add more protocol parsers (DNS, SMTP)
```

---

## Troubleshooting Common Issues

### Issue: "Permission denied" when capturing

**Solution:**
```bash
# Linux: Add capabilities
sudo setcap cap_net_raw,cap_net_admin=eip ./nids

# Or run with sudo
sudo ./nids -i eth0
```

### Issue: "No packets captured"

**Solution:**
```bash
# Check interface is correct
./nids --list-interfaces

# Check interface is up
ip link show eth0

# Try different interface
./nids -i wlan0
```

### Issue: Features CSV has NaN values

**Solution:**
- Check for zero-duration flows
- Verify packet timestamps are correct
- Ensure division by zero is handled in feature calculation

### Issue: ZMQ connection failed

**Solution:**
```bash
# Check AI engine is running
ps aux | grep zmq_subscriber

# Check port is available
netstat -an | grep 5555

# Restart AI engine first, then NIDS
```

---

## Automated Testing Script

**File:** `scripts/run_nids_tests.sh`

```bash
#!/bin/bash

echo "NIDS Automated Test Suite"
echo "========================="

RESULTS_DIR="test_results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# Test 1: S-IDS with SQL injection
echo "[TEST 1] SQL Injection Detection"
./build/sids -r test_pcaps/sql_injection.pcap > "$RESULTS_DIR/test1.log" 2>&1
grep "1002" nids_alerts.log && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: Port Scan
echo "[TEST 2] Port Scan Detection"
./build/sids -r test_pcaps/port_scan.pcap > "$RESULTS_DIR/test2.log" 2>&1
grep "1001" nids_alerts.log && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Feature Extraction
echo "[TEST 3] Feature Extraction"
./build/nids -r test_pcaps/normal_traffic.pcap --export-csv features.csv > "$RESULTS_DIR/test3.log" 2>&1
[ -f features.csv ] && echo "✅ PASS" || echo "❌ FAIL"

# Add more tests...

echo ""
echo "Results saved to: $RESULTS_DIR"
```

---

**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Project:** Final Year B.Tech - Hybrid IDS
**Last Updated:** October 2025
**Document Purpose:** Comprehensive testing methodology for NIDS component
