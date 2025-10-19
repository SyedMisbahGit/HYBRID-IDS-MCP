# NIDS Quick Start Guide

## 5-Minute Setup

### Prerequisites

- **Admin/Root Access**: Required for packet capture
- **Network Interface**: Active network connection
- **Build Tools**: gcc, cmake, make
- **Python**: 3.10+ with pip

---

## Step 1: Install Dependencies (2 minutes)

### Linux (Ubuntu/Debian)
```bash
# Build tools
sudo apt update
sudo apt install build-essential cmake

# libpcap for packet capture
sudo apt install libpcap-dev

# Python dependencies
pip install numpy scikit-learn pyzmq msgpack
```

### Windows (MSYS2 MINGW64)
```bash
# Build tools
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake

# libpcap (Npcap)
# Download and install Npcap from: https://npcap.com/
pacman -S mingw-w64-x86_64-libpcap

# Python dependencies
pip install numpy scikit-learn pyzmq msgpack
```

---

## Step 2: Build NIDS (2 minutes)

```bash
# Navigate to project root
cd Hybrid-IDS-MCP

# Create build directory
mkdir build && cd build

# Configure
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build (use all CPU cores)
cmake --build . --config Release -j$(nproc)

# Verify
ls -la sids nids
# Should see both executables
```

---

## Step 3: Choose Your Mode (1 minute)

### Option A: S-IDS Only (Signature Detection)

**Best for**: Quick testing, low resource usage

```bash
# Find your network interface
ip link show  # Linux
ipconfig      # Windows

# Start S-IDS
sudo ./build/sids -i eth0  # Replace eth0 with your interface
```

**Expected Output**:
```
[INFO] Hybrid IDS - S-IDS Starting
[INFO] Interface: eth0
[INFO] Loading rules from: config/nids/rules/
[INFO] Loaded 30 detection rules
[INFO] Starting packet capture...
```

### Option B: Complete Two-Tier System (S-IDS + A-IDS)

**Best for**: Full detection capabilities, production use

**Using Startup Script** (Recommended):
```bash
# Linux/macOS
sudo ./scripts/start_nids.sh
# Select option 2

# Windows (Run as Administrator)
scripts\start_nids.bat
# Select option 2
```

**Manual Start** (Advanced):
```bash
# Terminal 1: AI Engine (A-IDS)
cd src/ai/inference
python zmq_subscriber.py --model-dir ../../../models --port 5555

# Terminal 2: Feature Extractor
cd build
./nids -i eth0 --extract-features

# Terminal 3: S-IDS
cd build
sudo ./sids -i eth0
```

---

## Step 4: Generate Test Traffic & See Detections

```bash
# In another terminal
cd Hybrid-IDS-MCP

# Generate test attacks
python scripts/generate_test_traffic.py
```

**Expected Alerts**:
```
[ALERT] SQL Injection Attempt detected
  Severity: CRITICAL
  Source: 192.168.1.100:54321
  Dest: 10.0.0.5:80
  Rule: 1001

[ALERT] Port Scan detected
  Severity: MEDIUM
  Source: 10.0.0.50
  Scan Type: TCP SYN Scan
```

---

## Step 5: View Alerts

### Console Output
Alerts are printed to console in real-time

### Log File
```bash
# View alert log
tail -f logs/nids_alerts.log

# Search for specific alerts
grep "CRITICAL" logs/nids_alerts.log
```

### Kibana Dashboard (if ELK stack is running)
```
http://localhost:5601
```

---

## Common Commands

### Start NIDS

```bash
# Quick start (S-IDS only)
sudo ./build/sids -i eth0

# Complete system (script)
sudo ./scripts/start_nids.sh

# Complete system (manual)
# See Option B above
```

### Stop NIDS

```bash
# Press Ctrl+C in the terminal

# Or kill by process
pkill sids
pkill nids
pkill -f zmq_subscriber
```

### Change Network Interface

```bash
# List interfaces
ip link show              # Linux
Get-NetAdapter           # Windows PowerShell

# Use specific interface
sudo ./build/sids -i wlan0     # WiFi
sudo ./build/sids -i ens33     # VMware
sudo ./build/sids -i "Wi-Fi"   # Windows
```

### View Statistics

```bash
# S-IDS prints stats every 60 seconds
# Look for:
Packets Processed: 150000
Alerts Generated: 42
Rules Matched: 8
Avg Latency: 0.8ms
```

---

## Troubleshooting

### "Permission Denied"
```bash
# Run with sudo (Linux/macOS)
sudo ./build/sids -i eth0

# Run as Administrator (Windows)
# Right-click Command Prompt > Run as Administrator
```

### "Interface Not Found"
```bash
# List all interfaces
ip link show

# Use correct name
sudo ./build/sids -i ens33  # Not eth0
```

### "libpcap Not Found"
```bash
# Install libpcap
sudo apt install libpcap-dev  # Linux
pacman -S mingw-w64-x86_64-libpcap  # Windows MSYS2
```

### "No Alerts Appearing"
```bash
# 1. Check if traffic is being captured
#    Look for "Packets Processed" counter

# 2. Generate test traffic
python scripts/generate_test_traffic.py

# 3. Check filter
#    Edit config/nids/nids_config.yaml
#    Set capture_filter: ""  # Capture all traffic
```

### "AI Engine Not Receiving Features"
```bash
# Check if ZeroMQ port is listening
netstat -an | grep 5555

# Restart AI engine
cd src/ai/inference
python zmq_subscriber.py --port 5555
```

---

## What Each Component Does

| Component | Purpose | Required? |
|-----------|---------|-----------|
| **S-IDS** (sids) | Signature-based detection | ✅ Yes |
| **Feature Extractor** (nids) | Extract flow features | Only for A-IDS |
| **AI Engine** (zmq_subscriber.py) | ML anomaly detection | Only for A-IDS |
| **ELK Stack** | Visualization | Optional |

---

## Detection Examples

### SQL Injection
```
Traffic: GET /login?user=' OR '1'='1
Alert: [CRITICAL] SQL Injection Attempt (Rule 1001)
```

### Port Scan
```
Traffic: SYN packets to ports 1-1000 from same IP
Alert: [MEDIUM] TCP SYN Scan Detected (Rule 2001)
```

### Brute Force
```
Traffic: 10 failed SSH login attempts in 60 seconds
Alert: [HIGH] SSH Brute Force Attack (Rule 2012)
```

### Zero-Day (AI Detection)
```
Traffic: Unknown attack pattern
S-IDS: No match
A-IDS: [ANOMALY] Confidence: 0.92, Risk: HIGH
```

---

## Next Steps

After basic setup:

1. **Customize Rules**
   - Edit `config/nids/rules/*.yaml`
   - Add your organization-specific rules
   - Test with `reload_interval: 60` for quick testing

2. **Tune Configuration**
   - Edit `config/nids/nids_config.yaml`
   - Adjust thread_count for your CPU
   - Set appropriate confidence_threshold

3. **Train ML Models**
   ```bash
   cd src/ai/training
   python train_models.py --dataset path/to/CICIDS2017.csv
   ```

4. **Set Up ELK Dashboard**
   ```bash
   cd elk
   docker-compose up -d
   # Wait 1 minute
   # Open http://localhost:5601
   ```

5. **Production Deployment**
   - Run as system service (systemd/Windows Service)
   - Configure log rotation
   - Set up alerting (email, Slack, PagerDuty)
   - Enable Elasticsearch integration

---

## Performance Tips

### Low-End Systems (2 cores, 4GB RAM)
```yaml
# config/nids/nids_config.yaml
threading:
  thread_count: 1
  queue_size: 5000

limits:
  max_memory_mb: 2048
```

### High-End Systems (8+ cores, 16GB+ RAM)
```yaml
threading:
  thread_count: 7
  queue_size: 50000

limits:
  max_memory_mb: 8192

performance:
  enable_prefetch: true
```

### High Traffic Networks (1Gbps+)
```yaml
capture:
  buffer_size: 536870912  # 512 MB

threading:
  thread_count: 8

advanced:
  dpdk:
    enabled: true  # Requires DPDK compilation
```

---

## Key Files

| File | Purpose |
|------|---------|
| `build/sids` | S-IDS executable |
| `build/nids` | Feature extractor executable |
| `config/nids/nids_config.yaml` | Main configuration |
| `config/nids/rules/*.yaml` | Detection rules |
| `logs/nids_alerts.log` | Alert log |
| `scripts/start_nids.sh` | Startup script (Linux) |
| `scripts/start_nids.bat` | Startup script (Windows) |

---

## Getting Help

- **Full Documentation**: [NIDS_COMPLETE.md](NIDS_COMPLETE.md)
- **Architecture Guide**: [ARCHITECTURE_EXPLAINED.md](ARCHITECTURE_EXPLAINED.md)
- **Project README**: [README.md](README.md)
- **Issues**: https://github.com/SyedMisbahGit/HYBRID-IDS-MCP/issues

---

**Quick Start Checklist**:
- ✅ Install dependencies
- ✅ Build NIDS (`cmake .. && make`)
- ✅ Find network interface (`ip link show`)
- ✅ Start NIDS (`sudo ./build/sids -i eth0`)
- ✅ Generate test traffic
- ✅ View alerts

**You're detecting threats in 5 minutes!** 🛡️
