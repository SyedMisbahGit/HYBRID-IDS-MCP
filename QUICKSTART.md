# S-IDS Quick Start Guide

**Get your Signature-based IDS running in under 5 minutes!**

---

## Prerequisites

- Linux (Ubuntu/Debian/Kali) or macOS
- libpcap installed
- C++ compiler (g++ or clang)
- CMake 3.20+
- Python 3 (for test traffic generation)

---

## Step 1: Install Dependencies (1 minute)

### Ubuntu/Debian/Kali:
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libpcap-dev python3
```

### macOS:
```bash
brew install cmake libpcap python3
```

---

## Step 2: Build S-IDS (30 seconds)

```bash
cd /c/Users/zsyed/Hybrid-IDS-MCP
./scripts/build_sids.sh
```

Expected output:
```
========================================
  Building S-IDS
========================================
[INFO] Creating build directory...
[INFO] Configuring with CMake...
[INFO] Building S-IDS...
[SUCCESS] S-IDS built successfully!
Executable: /c/Users/zsyed/Hybrid-IDS-MCP/build/sids
```

---

## Step 3: Generate Test Traffic (5 seconds)

```bash
python3 scripts/generate_test_traffic.py test.pcap
```

This creates a PCAP file with:
- Normal HTTP traffic
- SQL injection attempts ⚠️
- Port scans ⚠️
- SSH connection attempts ⚠️
- FTP authentication ⚠️
- Telnet connections ⚠️

---

## Step 4: Run S-IDS (10 seconds)

```bash
./build/sids -r test.pcap
```

You'll see:
1. **Startup banner** with loaded rules
2. **Real-time alerts** as attacks are detected
3. **Statistics** showing packet counts and throughput
4. **Final summary** with alert breakdown

---

## Expected Output

```
========================================
  Hybrid IDS - Signature Detection
========================================

[INFO] Loaded 6 signature rules

Active Rules:
-------------
  [1001] SSH Scan Detection (MEDIUM)
  [1002] SQL Injection Attempt (HIGH)
  [1003] Port Scan Detection (MEDIUM)
  [1004] FTP Authentication Attempt (LOW)
  [1006] Telnet Connection (MEDIUM)

[INFO] Processing PCAP file: test.pcap

🚨 [HIGH] SQL Injection Attempt
  10.0.0.50:52342 -> 192.168.1.10:80 [TCP]
  Matched: or 1=1

🚨 [MEDIUM] Port Scan Detection
  10.0.0.50:12345 -> 192.168.1.100:22 [TCP]

[STATS] Packets: 30 | Alerts: 15 | Rate: 850 pkt/s

========================================
  S-IDS Statistics
========================================
Total Packets:    30
Alerts:           15
  Low:            2
  Medium:         10
  High:           3
========================================
```

---

## Next Steps

### Try Live Capture:
```bash
sudo ./build/sids -i eth0
# Replace eth0 with your network interface
```

### Check Alert Log:
```bash
cat sids_alerts.log
```

### View Documentation:
```bash
cat docs/SIDS_README.md
```

---

## Troubleshooting

### Build fails with "libpcap not found"
```bash
sudo apt-get install libpcap-dev
```

### Permission denied on live capture
```bash
sudo ./build/sids -i eth0
# Run with sudo
```

### No alerts generated
- Make sure you're using the generated test.pcap
- Check if rules are enabled (should see "Active Rules" on startup)

---

## Commands Cheat Sheet

```bash
# Build
./scripts/build_sids.sh

# Generate test traffic
python3 scripts/generate_test_traffic.py test.pcap

# Analyze PCAP
./build/sids -r test.pcap

# Live capture
sudo ./build/sids -i eth0

# View alerts
cat sids_alerts.log | jq .

# Rebuild (after code changes)
cd build && make sids
```

---

## What's Happening Under the Hood?

1. **libpcap** captures packets from file or network
2. **PacketParser** dissects Ethernet/IP/TCP/UDP headers
3. **RuleEngine** matches packets against 6 signature rules
4. **AlertGenerator** creates alerts for matches
5. **Statistics** tracks performance in real-time
6. **JSON Logger** saves alerts to `sids_alerts.log`

---

## Success Indicators

✅ You should see:
- Build completes without errors
- Test PCAP generates successfully
- S-IDS starts and loads 6 rules
- Multiple alerts are generated
- Statistics show packets processed
- `sids_alerts.log` contains JSON alerts

---

**That's it! You now have a working Intrusion Detection System!** 🎉

For more details, see [SIDS_IMPLEMENTATION_SUMMARY.md](SIDS_IMPLEMENTATION_SUMMARY.md)
