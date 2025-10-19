# Hybrid IDS - Complete Integration Guide

**Final Year B.Tech Project**
**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Department:** CSE - Cybersecurity

---

## Overview

This guide walks you through deploying my **Hybrid IDS system** with its unique two-tier architecture:
- **S-IDS (Tier 1)** - Signature-based detection of known threats
- **A-IDS (Tier 2)** - ML-based anomaly detection for zero-day attacks
- **Feedback Loop** - Manual review system to update signatures
- **HIDS** (Parallel) - Host-based monitoring of files/processes/logs
- **ELK Central Dashboard** - Unified visualization and correlation hub

**Estimated setup time:** ~45-60 minutes
**Project Type:** Final Year B.Tech Major Project
**Academic Year:** 2024-2025

---

## System Architecture - Two-Tier Detection Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│                      NETWORK TRAFFIC                            │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │ TIER 1: Signature IDS  │  ◄──────┐
           │    (S-IDS/C++)         │         │
           │  - Known Patterns      │         │ FEEDBACK LOOP
           │  - Rule Matching       │         │ (Rule Updates)
           │  - Fast Detection      │         │
           └──┬──────────────────┬──┘         │
              │                  │            │
       MALICIOUS              BENIGN          │
       (Known)              (or Unknown)      │
              │                  │            │
              ▼                  ▼            │
    ┌─────────────────┐  ┌──────────────────────┐
    │  S-IDS Alert    │  │ TIER 2: Anomaly IDS  │
    │  nids_alerts    │  │    (A-IDS/Python)    │
    │     .log        │  │  - ML Models (RF+IF) │
    └────────┬────────┘  │  - 78 Features       │
             │           │  - Zero-day Detection│
             │           └──┬───────────────┬───┘
             │              │               │
             │        BENIGN│         MALICIOUS
             │      (Safe)  │         (Anomaly)
             │              │               │
             │              │               ├────────┬────────┐
             │              │               │        │        │
             │              │               ▼        │        ▼
             │              │     ┌────────────┐     │  ┌─────────────┐
             │              │     │ Dashboard  │     │  │   Manual    │
             │              │     │   Alert    │     │  │   Review    │
             │              │     │ ai_alerts  │     │  │   System    │
             │              │     │   .log     │     │  │  (Analyst)  │
             │              │     └────────────┘     │  └──────┬──────┘
             │              │                        │         │
             │              │                        │    CONFIRMED
             │              │                        │         │
             │              │                        └─────────┘
             │              │
             ├──────────────┼────────────────────────────┐
             │              │                            │
             ▼              ▼                            ▼
    ┌────────────┐  ┌─────────────┐           ┌──────────────────┐
    │   HIDS     │  │  Logstash   │           │  Central ELK     │
    │ (Parallel) │  │  Pipeline   │           │    Dashboard     │
    │ - File Mon.│  │  - Parse    │           │                  │
    │ - Logs     │  │  - Enrich   │           │ - Correlation    │
    │ - Process  │  │  - GeoIP    │           │ - Analytics      │
    └─────┬──────┘  └──────┬──────┘           │ - Visualization  │
          │                │                   │ - Manual Review  │
          │ hids_alerts.log│                   └──────────────────┘
          │                │
          └────────────────┴───────────────────────▶
```

### Architecture Highlights

**🔄 Two-Tier Detection:**
1. **S-IDS (Tier 1)**: Fast signature matching catches known threats
2. **A-IDS (Tier 2)**: ML models analyze benign traffic for anomalies
3. **Feedback Loop**: Validated anomalies update S-IDS rules

**🎯 Adaptive Learning:**
- Human analyst reviews A-IDS anomalies in dashboard
- Confirmed threats → New signatures added to S-IDS
- System continuously evolves and improves

**🏠 Parallel HIDS:**
- Monitors host-level events independently
- Correlates with NIDS alerts in central dashboard

---

## Prerequisites

### Software Requirements

#### Windows
- **MSYS2/MinGW** (for C++ compilation)
- **Python 3.10+**
- **Docker Desktop** (for ELK Stack)
- **Npcap** (for packet capture)

#### Linux
- **GCC 9+** or **Clang 10+**
- **Python 3.10+**
- **Docker** and **Docker Compose**
- **libpcap-dev**

### Hardware Requirements (Student/Lab Environment)
- **CPU:** 2+ cores (4 cores recommended)
- **RAM:** 6 GB minimum (8 GB recommended)
- **Disk:** 10 GB free space
- **Network:** Admin/root privileges for packet capture (can use PCAP files if privileges unavailable)

---

## Part 1: Environment Setup

### Windows Setup

```powershell
# 1. Install MSYS2
# Download from: https://www.msys2.org/
# Install to: C:\msys64

# 2. Open MSYS2 MINGW64 terminal and install dependencies
pacman -Syu
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake mingw-w64-x86_64-make
pacman -S mingw-w64-x86_64-boost mingw-w64-x86_64-pcre

# 3. Install Npcap
# Download from: https://npcap.com/
# Install with "WinPcap API-compatible Mode" enabled

# 4. Install Python dependencies
pip install numpy pandas scikit-learn psutil elasticsearch python-magic

# 5. Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop/
```

### Linux Setup

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y build-essential cmake libpcap-dev libboost-all-dev libpcre3-dev
sudo apt install -y python3 python3-pip docker.io docker-compose

# Install Python dependencies
pip3 install numpy pandas scikit-learn psutil elasticsearch python-magic

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

---

## Part 2: Build NIDS Engine

### Build C++ Components

```bash
# Navigate to project root
cd Hybrid-IDS-MCP

# Create build directory
mkdir -p build
cd build

# Configure with CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build (use -j4 for parallel build)
cmake --build . --config Release -j4

# Verify executables
ls -lh nids sids feature_extractor  # Linux
ls -lh nids.exe sids.exe feature_extractor.exe  # Windows
```

**Expected output:**
```
nids              (or nids.exe)          - Full NIDS with AI integration
sids              (or sids.exe)          - Signature-only IDS
feature_extractor (or feature_extractor.exe) - Feature extraction tool
```

### Test NIDS Engine

```bash
# Test with sample PCAP (signature detection)
./sids -r ../test_data/sample.pcap

# Test with feature extraction
./nids -r ../test_data/sample.pcap --extract-features --export-csv features.csv

# Verify output
cat nids_alerts.log
cat features.csv
```

---

## Part 3: Setup AI Engine

### Train ML Models (One-time)

```bash
cd src/ai/training

# Train models on CIC-IDS2017 dataset
python train_models.py --dataset ../../../datasets/cicids2017_sample.csv \
                       --output ../../../models

# Verify models created
ls -lh ../../../models/
# Expected files:
# - random_forest_model.pkl
# - isolation_forest_model.pkl
# - scaler.pkl
```

### Test AI Engine

```bash
cd src/ai/inference

# Test standalone anomaly detection
python anomaly_detector.py --model-dir ../../../models \
                           --test-csv ../../../test_data/test_features.csv

# Expected output:
# [INFO] Loaded models: Random Forest, Isolation Forest
# [INFO] Processed 100 flows: 12 anomalies detected (12.0%)
```

---

## Part 4: Setup HIDS

### Configure HIDS Monitoring

Edit configuration: `src/hids/config/hids_config.json`

```json
{
  "file_monitor": {
    "enabled": true,
    "scan_interval": 60,
    "critical_paths": [
      "C:\\Windows\\System32\\drivers\\etc\\hosts",
      "C:\\Windows\\System32\\config\\SAM",
      "/etc/passwd",
      "/etc/shadow",
      "/etc/sudoers"
    ]
  },
  "log_analyzer": {
    "enabled": true,
    "scan_interval": 300,
    "log_paths": {
      "windows": [
        "C:\\Windows\\System32\\winevt\\Logs\\Security.evtx",
        "C:\\Windows\\System32\\winevt\\Logs\\System.evtx"
      ],
      "linux": [
        "/var/log/auth.log",
        "/var/log/syslog",
        "/var/log/secure"
      ]
    }
  },
  "process_monitor": {
    "enabled": true,
    "scan_interval": 60,
    "suspicious_names": [
      "nc", "netcat", "nmap", "metasploit", "mimikatz",
      "psexec", "powershell_empire", "cobalt"
    ]
  }
}
```

### Initialize HIDS Baseline

```bash
cd src/hids

# Create baseline for file integrity monitoring
python file_monitor.py --create-baseline

# Verify baseline created
cat baseline.json
# Shows SHA256 hashes of all monitored files
```

### Test HIDS Components

```bash
# Test file integrity monitoring
python file_monitor.py --check

# Test log analysis
python log_analyzer.py --scan

# Test process monitoring
python process_monitor.py --scan

# Run full HIDS
python hids_main.py --config config/hids_config.json
```

---

## Part 5: Deploy ELK Stack

### Start ELK Stack

```bash
cd elk

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# NAME                    STATUS              PORTS
# elasticsearch           Up (healthy)        9200->9200
# logstash                Up                  5000-5001->5000-5001
# kibana                  Up                  5601->5601
# filebeat                Up                  -
```

### Wait for Services

```bash
# Wait for Elasticsearch (takes ~2 minutes)
curl http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=300s

# Verify Kibana is ready
curl http://localhost:5601/api/status
```

### Create Index Patterns

```bash
# Option 1: Use Python exporter to create templates
cd ../src/exporters
python elasticsearch_exporter.py

# Option 2: Manual creation via Kibana UI
# Open http://localhost:5601
# Go to: Stack Management > Index Patterns > Create index pattern
# Pattern: hybrid-ids-nids-alerts-*
# Time field: @timestamp
# Repeat for: ai-alerts-*, hids-alerts-*, network-features-*
```

---

## Part 6: Integrate All Components

### Create Log Directories

```bash
# Create shared log directory
mkdir -p /var/log/hybrid-ids  # Linux
mkdir -p C:\var\log\hybrid-ids  # Windows (as Administrator)

# Set permissions (Linux)
sudo chmod 777 /var/log/hybrid-ids
```

### Update Docker Compose Volumes

Ensure `elk/docker-compose.yml` has correct log paths:

```yaml
logstash:
  volumes:
    # Windows paths
    - C:/Users/zsyed/Hybrid-IDS-MCP/nids_alerts.log:/var/log/hybrid-ids/nids_alerts.log
    - C:/Users/zsyed/Hybrid-IDS-MCP/ai_alerts.log:/var/log/hybrid-ids/ai_alerts.log
    - C:/Users/zsyed/Hybrid-IDS-MCP/hids_alerts.log:/var/log/hybrid-ids/hids_alerts.log

    # Linux paths
    # - /var/log/hybrid-ids/nids_alerts.log:/var/log/hybrid-ids/nids_alerts.log
    # - /var/log/hybrid-ids/ai_alerts.log:/var/log/hybrid-ids/ai_alerts.log
    # - /var/log/hybrid-ids/hids_alerts.log:/var/log/hybrid-ids/hids_alerts.log
```

### Start All Systems (Two-Tier Pipeline)

**Terminal 1: S-IDS (Signature-Based - Tier 1)**
```bash
cd build
# Start signature detection on network interface
./sids -i eth0  # Linux
./sids -i "Ethernet"  # Windows

# Known threats → ../nids_alerts.log
# Benign traffic → passed to A-IDS
```

**Terminal 2: A-IDS (Anomaly-Based - Tier 2)**
```bash
cd build
# Start full NIDS with ML feature extraction
./nids -i eth0 --extract-features --export-json  # Linux
./nids -i "Ethernet" --extract-features  # Windows

# Features sent to AI engine for analysis
```

**Terminal 3: AI Engine (A-IDS Backend)**
```bash
cd src/ai/inference
python zmq_subscriber.py --model-dir ../../../models

# Anomalies → ../../../ai_alerts.log
# For manual review in dashboard
```

**Terminal 4: HIDS (Parallel Monitoring)**
```bash
cd src/hids
python hids_main.py --config config/hids_config.json

# Host alerts → ../../hids_alerts.log
```

**Terminal 5: Monitor All Logs**
```bash
# Watch the two-tier pipeline in action
tail -f nids_alerts.log ai_alerts.log hids_alerts.log
```

---

## Part 7: Access Dashboard

### Open Kibana

```
URL: http://localhost:5601
Username: elastic (default)
Password: changeme (default - configure in docker-compose.yml)
```

### Import Unified Dashboard

1. **Navigate to**: Stack Management > Saved Objects
2. **Click**: Import
3. **Select file**: `elk/kibana/dashboards/unified-security-dashboard.ndjson`
4. **Click**: Import
5. **Navigate to**: Dashboard > Hybrid IDS - Unified Security Dashboard

### Dashboard Sections

The unified dashboard showcases the **two-tier detection pipeline**:

**Row 1: Key Metrics (5 panels)**
- S-IDS Detections (Tier 1 - Known threats)
- A-IDS Anomalies (Tier 2 - Unknown threats)
- HIDS Alerts (Parallel monitoring)
- Pending Manual Review (A-IDS alerts awaiting validation)
- Critical Threats Count

**Row 2: Two-Tier Pipeline Analysis (2 panels)**
- Alert Timeline by Source (S-IDS vs A-IDS vs HIDS over time)
- Detection Tier Distribution (Pie: Tier 1 vs Tier 2 vs HIDS)

**Row 3: Threat Intelligence (3 panels)**
- Top Attack Sources (Geographic Map)
- MITRE ATT&CK Techniques (Bar chart)
- A-IDS Confidence Distribution (Histogram for Tier 2)

**Row 4: Manual Review Queue (2 panels)** - *Feedback Loop Implementation*
- A-IDS Anomalies Awaiting Review (Table - for analyst validation)
- Recently Confirmed Anomalies (Validated threats ready for signature creation)

> **Note for Students**: The manual review system is dashboard-based. In a university project, you can:
> - Manually review A-IDS anomalies in the Kibana dashboard
> - Document which anomalies you would convert to signatures
> - (Optional) Create a simple script to add new rules to S-IDS based on confirmed patterns

**Row 5: HIDS Details (2 panels)**
- File Integrity Alerts (Table)
- Suspicious Processes (Table)

**Row 6: Network Analysis (3 panels)**
- Network Protocol Distribution (Pie)
- Top Targeted Ports (Bar)
- ML Inference Performance (Line - A-IDS latency)

**Row 7: Recent Events (1 panel)**
- Recent Security Events (Data table with all detection sources)

---

## Part 8: Verification & Testing

### Test NIDS Detection

```bash
# Generate SQL injection signature alert
curl "http://testserver.com/page?id=1' OR '1'='1"

# Check NIDS log
grep "SQL Injection" nids_alerts.log

# Verify in Kibana
# Query: rule_id:1002 AND severity:HIGH
```

### Test AI Anomaly Detection

```bash
# Generate unusual traffic pattern
# (e.g., port scan, high packet rate)
nmap -sS -p 1-1000 target_ip

# Check AI log
grep "ANOMALY" ai_alerts.log

# Verify in Kibana
# Query: type:ANOMALY AND confidence > 0.8
```

### Test HIDS Detection

**File Integrity:**
```bash
# Modify monitored file
echo "# test" >> /etc/hosts  # Linux
echo "# test" >> C:\Windows\System32\drivers\etc\hosts  # Windows

# Wait 60 seconds (scan interval)
# Check HIDS log
grep "file_integrity" hids_alerts.log
```

**Process Monitoring:**
```bash
# Run suspicious process
nc -l 4444  # Netcat listener

# Check HIDS log
grep "process_monitoring" hids_alerts.log
```

**Log Analysis:**
```bash
# Generate failed login (Linux)
ssh nonexistent@localhost  # Enter wrong password 3+ times

# Check HIDS log
grep "POSSIBLE_BRUTE_FORCE" hids_alerts.log
```

---

## Part 9: Testing & Demonstration (Academic Use)

### Simple Testing for Demonstrations

**1. Basic Security Testing**

For university demonstrations, you can use:
```bash
# Test with sample PCAP files (no special privileges needed)
./nids -r test_data/sample.pcap

# Use small time windows for testing
# Run each component for 5-10 minutes for demo
```

**2. Resource-Conscious Configuration**

For student laptops/lab computers, edit `elk/docker-compose.yml`:
```yaml
environment:
  - "ES_JAVA_OPTS=-Xms2g -Xmx2g"  # Reduced memory for student machines
```

**3. Simple Monitoring**

**Check System is Working:**

```bash
# Verify logs are being generated
tail -f nids_alerts.log ai_alerts.log hids_alerts.log

# Simple health check
curl http://localhost:9200/_cluster/health?pretty

# Count alerts for your report
curl "http://localhost:9200/hybrid-ids-*-alerts-*/_count?pretty"
```

### Academic Testing Tips

**For Project Reports/Presentations:**

1. **Capture screenshots** of the Kibana dashboard showing alerts
2. **Document test scenarios** (e.g., "Tested port scan detection")
3. **Record metrics** (detection rate, false positives) for analysis
4. **Create a demo video** showing the system in action (optional)

---

## Part 10: Troubleshooting

### NIDS Issues

**Problem: "Permission denied" when capturing packets**

**Solution:**
```bash
# Linux: Run with sudo or set capabilities
sudo ./nids -i eth0
# OR
sudo setcap cap_net_raw,cap_net_admin=eip ./nids

# Windows: Run as Administrator
```

**Problem: "No suitable interface found"**

**Solution:**
```bash
# List available interfaces
./nids --list-interfaces

# Use exact interface name
./nids -i "Ethernet 2"  # Windows
./nids -i enp0s3         # Linux
```

### AI Engine Issues

**Problem: "Model file not found"**

**Solution:**
```bash
# Verify model files exist
ls -lh models/
# Should see: random_forest_model.pkl, isolation_forest_model.pkl, scaler.pkl

# If missing, train models:
cd src/ai/training
python train_models.py --dataset ../../datasets/cicids2017_sample.csv
```

**Problem: "Array dimension mismatch"**

**Solution:**
This was fixed in `src/ai/inference/anomaly_detector.py`. Verify you have the latest version:
```bash
grep "reshape(1, -1)" src/ai/inference/anomaly_detector.py
# Should show: features_2d = features.reshape(1, -1)
```

### HIDS Issues

**Problem: "Access denied" reading log files**

**Solution:**
```bash
# Linux: Add user to adm group
sudo usermod -aG adm $USER

# Windows: Run as Administrator
```

**Problem: High CPU usage**

**Solution:**
Increase scan intervals in `config/hids_config.json`:
```json
{
  "file_monitor": { "scan_interval": 300 },  // 5 minutes
  "process_monitor": { "scan_interval": 120 }  // 2 minutes
}
```

### ELK Stack Issues

**Problem: Elasticsearch won't start (memory error)**

**Solution:**
```bash
# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory > 8 GB

# OR reduce Elasticsearch heap
# elk/docker-compose.yml:
ES_JAVA_OPTS=-Xms2g -Xmx2g
```

**Problem: Logstash not processing logs**

**Solution:**
```bash
# Check Logstash logs
docker-compose logs logstash

# Verify file permissions
ls -lh /var/log/hybrid-ids/*.log

# Manually test pipeline
cat nids_alerts.log | docker-compose exec -T logstash /usr/share/logstash/bin/logstash -f /usr/share/logstash/pipeline/nids-alerts.conf
```

**Problem: No data in Kibana**

**Solution:**
```bash
# Verify indices exist
curl http://localhost:9200/_cat/indices?v | grep hybrid-ids

# Check document count
curl http://localhost:9200/hybrid-ids-nids-alerts-*/_count?pretty

# Refresh index patterns in Kibana
# Stack Management > Index Patterns > [Your Pattern] > Refresh
```

---

## Part 11: Project Cleanup (After Demonstration)

### Stopping All Services

```bash
# Stop Docker containers
cd elk
docker-compose down

# Stop NIDS/AI/HIDS (Ctrl+C in respective terminals)

# Optional: Clean up Docker volumes to free space
docker-compose down -v
```

### Saving Results for Report

```bash
# Archive your logs for analysis
mkdir project_results
cp nids_alerts.log ai_alerts.log hids_alerts.log project_results/

# Export dashboard screenshots from Kibana
# (Use browser screenshot tools)

# Optional: Export sample alerts as JSON for report
curl "http://localhost:9200/hybrid-ids-*-alerts-*/_search?size=50" > project_results/sample_alerts.json
```

### Optional: Model Training Exercise

If you want to experiment with ML model training:
```bash
cd src/ai/training

# Train models on sample dataset (for learning purposes)
python train_models.py --dataset ../../../datasets/sample_data.csv --output ../../../models

# Note: Full training on large datasets is optional and resource-intensive
```

---

## Part 12: Performance Metrics

### Expected Performance

**NIDS Engine:**
- Packet processing: 50,000-100,000 packets/second
- Feature extraction: 1,000-5,000 flows/second
- Memory usage: 200-500 MB
- CPU usage: 20-40% (single core)

**AI Engine:**
- Inference latency: <5ms per flow
- Throughput: 5,000-10,000 predictions/second
- Memory usage: 500 MB - 1 GB
- CPU usage: 10-30%

**HIDS:**
- File scan: 1,000-5,000 files/minute
- Process scan: 100-500 processes/second
- Log parsing: 10,000-50,000 lines/minute
- Memory usage: 100-300 MB

**ELK Stack:**
- Ingestion rate: 10,000-50,000 events/second
- Query latency: 50-200ms
- Memory usage: 4-8 GB (Elasticsearch)
- Disk usage: ~500 MB/day (compressed)

---

## Summary

You now have a **functional Hybrid IDS for your university project** with:

✅ **NIDS** - Signature-based network intrusion detection
✅ **AI Engine** - Machine learning anomaly detection
✅ **HIDS** - Host-based security monitoring
✅ **ELK Stack** - Unified security dashboard
✅ **Educational value** - Hands-on cybersecurity learning

**For Your Project Report/Presentation:**
1. Take screenshots of the dashboard showing detected threats
2. Document at least 3 test scenarios you ran
3. Analyze false positive/negative rates
4. Discuss the strengths and limitations you observed
5. Suggest improvements or future enhancements

**Academic Learning Outcomes:**
- Understanding of multi-layer intrusion detection
- Hands-on experience with machine learning in security
- Knowledge of ELK Stack for log analysis
- Practical skills in cybersecurity tools

---

## Additional Resources

- **NIDS Documentation**: `docs/nids/README.md`
- **AI Engine Guide**: `docs/ai/ML_INTEGRATION.md`
- **HIDS Manual**: `src/hids/README.md`
- **ELK Configuration**: `ELK_DASHBOARD_GUIDE.md`
- **Windows Deployment**: `REAL_TIME_DEPLOYMENT.md`
- **Bug Fixes**: `BUGFIX_AI_ENGINE.md`

**Support:**
- GitHub Issues: https://github.com/SyedMisbahGit/HYBRID-IDS-MCP/issues
- Documentation Index: `INDEX.md`

---

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Author:** Claude (Anthropic AI Assistant)
