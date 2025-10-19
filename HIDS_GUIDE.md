# HIDS (Host-based Intrusion Detection System) - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Testing](#testing)
8. [ELK Integration](#elk-integration)
9. [Troubleshooting](#troubleshooting)
10. [Performance Tuning](#performance-tuning)

---

## Overview

The Hybrid IDS HIDS component is a **host-based intrusion detection system** that monitors system-level activities for security threats. It operates in parallel with the network-based detection (NIDS) to provide comprehensive security coverage.

### Key Features

- **File Integrity Monitoring (FIM)**: Detects unauthorized changes to critical system files
- **Log Analysis**: Analyzes system logs for suspicious activities and security events
- **Process Monitoring**: Tracks running processes and network connections
- **Real-time Alerting**: Immediate notification of security events
- **ELK Integration**: Centralized logging and visualization via Elasticsearch/Kibana
- **Cross-platform**: Supports Windows, Linux, and macOS

### Detection Capabilities

| Category | Detection Type | Examples |
|----------|---------------|----------|
| File Integrity | New, Modified, Deleted Files | System file tampering, unauthorized executables |
| Authentication | Failed Logins, Brute Force | Password attacks, unauthorized access attempts |
| Privilege Escalation | Sudo, UAC Elevation | Lateral movement, privilege abuse |
| Account Management | User Creation/Deletion | Backdoor accounts, insider threats |
| Suspicious Activity | Malicious Commands | Netcat, Mimikatz, PowerShell exploits |
| Network Connections | Suspicious Ports | C&C communication, reverse shells |
| System Changes | Service/Firewall Mods | Persistence mechanisms |

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      HIDS Main Controller                    │
│                      (hids_main.py)                          │
└────────┬─────────────────┬────────────────┬─────────────────┘
         │                 │                │
         ▼                 ▼                ▼
┌────────────────┐ ┌──────────────┐ ┌──────────────────┐
│ File Integrity │ │ Log Analyzer │ │ Process Monitor  │
│   Monitor      │ │              │ │                  │
│                │ │              │ │                  │
│ - SHA256 Hash  │ │ - 12 Rules   │ │ - Baseline       │
│ - Baseline     │ │ - Pattern    │ │ - Suspicious     │
│ - Realtime     │ │   Matching   │ │   Processes      │
│   Detection    │ │ - Brute Force│ │ - Network Conn   │
└────────┬───────┘ └──────┬───────┘ └─────────┬────────┘
         │                │                   │
         └────────────────┼───────────────────┘
                          ▼
              ┌───────────────────────┐
              │  Alert Aggregation    │
              └───────────┬───────────┘
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
        ┌───────────────┐   ┌──────────────────┐
        │  Local Logs   │   │  Elasticsearch   │
        │ (JSON/Text)   │   │  (ELK Stack)     │
        └───────────────┘   └──────────────────┘
```

### Data Flow

1. **HIDS Main** orchestrates all monitoring components
2. Each component runs independently at configured intervals
3. Alerts are collected, enriched with metadata, and exported
4. Alerts are written to local logs AND sent to Elasticsearch (if enabled)
5. Kibana dashboards visualize all HIDS alerts in real-time

---

## Components

### 1. File Integrity Monitor ([file_monitor.py](src/hids/file_monitor.py))

**Purpose**: Detect unauthorized file system changes

**How It Works**:
1. Creates a **baseline** of critical files with SHA256 hashes
2. Periodically re-scans files and compares hashes
3. Alerts on: new files, modified files, deleted files

**Monitored Paths** (configurable):
- **Windows**: `C:\Windows\System32`, `C:\Program Files`, etc.
- **Linux**: `/etc`, `/bin`, `/sbin`, `/usr/bin`, etc.

**Key Features**:
- Cryptographic hash verification (SHA256)
- Metadata tracking (size, mtime, permissions)
- File extension filtering
- Baseline persistence (JSON)

**Example Alert**:
```json
{
  "timestamp": "2025-10-19T10:15:23",
  "type": "MODIFIED_FILE",
  "severity": "HIGH",
  "filepath": "C:\\Windows\\System32\\kernel32.dll",
  "old_hash": "abc123...",
  "new_hash": "def456..."
}
```

### 2. Log Analyzer ([log_analyzer.py](src/hids/log_analyzer.py))

**Purpose**: Detect security events from system logs

**Detection Rules** (12 built-in):
1. Failed Login Attempts
2. Successful Login After Failures (Brute Force)
3. Privilege Escalation (sudo, UAC)
4. Service Start/Stop
5. Firewall Rule Changes
6. User Account Created
7. User Account Deleted
8. Password Changes
9. Suspicious Commands (nc, mimikatz, etc.)
10. File Access Denied
11. System Reboot
12. Kernel Module Loaded

**How It Works**:
1. Reads log files line-by-line OR Windows Event Log (via pywin32)
2. Applies regex-based detection rules
3. Tracks state (e.g., failed login counters)
4. Generates alerts with context

**Brute Force Detection**:
- Tracks failed login attempts per user
- If 3+ failures followed by successful login → **CRITICAL** alert
- Automatic reset after successful login

**Example Alert**:
```json
{
  "timestamp": "2025-10-19T10:16:30",
  "rule_name": "Successful Login After Failures",
  "severity": "CRITICAL",
  "alert_type": "POSSIBLE_BRUTE_FORCE",
  "username": "admin",
  "previous_failures": 5,
  "log_source": "Windows_Security"
}
```

### 3. Process Monitor ([process_monitor.py](src/hids/process_monitor.py))

**Purpose**: Detect suspicious processes and network connections

**Monitoring Capabilities**:
- Running processes (name, PID, command line, user)
- CPU/Memory usage
- Network connections (local/remote IP:port)
- New processes since baseline

**Suspicious Indicators**:
- **Process Names**: `nc`, `netcat`, `nmap`, `mimikatz`, `meterpreter`, etc.
- **Command Line Args**: `base64`, `invoke-expression`, `-e /bin/sh`
- **Network Ports**: 1337, 4444, 31337, 6667 (IRC), etc.
- **Unusual Connections**: cmd.exe, powershell.exe making outbound connections

**Example Alert**:
```json
{
  "timestamp": "2025-10-19T10:21:45",
  "type": "SUSPICIOUS_PROCESS",
  "severity": "HIGH",
  "pid": 1234,
  "name": "nc.exe",
  "cmdline": "nc -l -p 4444 -e cmd.exe",
  "username": "SYSTEM"
}
```

---

## Installation

### Prerequisites

**Operating System**:
- Windows 10/11 (with Administrator privileges)
- Linux (Ubuntu 22.04+, CentOS 8+, etc. with root/sudo)
- macOS 12+ (with root/sudo)

**Python**: 3.10 or higher

**Dependencies**:
```bash
# Core dependencies
pip install psutil pyyaml watchdog

# Elasticsearch integration (optional)
pip install elasticsearch

# Windows Event Log (Windows only)
pip install pywin32
```

### Installation Steps

**1. Clone Repository**:
```bash
git clone https://github.com/SyedMisbahGit/HYBRID-IDS-MCP.git
cd HYBRID-IDS-MCP
```

**2. Create Virtual Environment**:
```bash
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

**3. Install Dependencies**:
```bash
pip install -r requirements.txt
```

**4. Create Required Directories**:
```bash
mkdir -p logs data
```

**5. Verify Installation**:
```bash
# Test file monitor
python src/hids/file_monitor.py

# Test log analyzer
python src/hids/log_analyzer.py

# Test process monitor
python src/hids/process_monitor.py
```

---

## Configuration

### Configuration File

Location: [`config/hids/hids_config.yaml`](config/hids/hids_config.yaml)

**Key Sections**:

#### General Settings
```yaml
hostname: "localhost"
check_interval: 60        # File/process check (seconds)
log_check_interval: 300   # Log analysis (seconds)
```

#### Component Toggles
```yaml
file_monitoring: true
process_monitoring: true
log_monitoring: true
```

#### Elasticsearch Integration
```yaml
elasticsearch_enabled: false
elasticsearch_hosts:
  - "http://localhost:9200"
```

#### File Integrity Monitoring
```yaml
file_integrity:
  baseline_file: "data/hids_baseline.json"
  hash_algorithm: "sha256"
  monitored_paths_windows:
    - "C:\\Windows\\System32"
  file_extensions:
    - ".exe"
    - ".dll"
    - ".sys"
```

#### Process Monitoring
```yaml
process_monitoring:
  cpu_threshold: 80
  memory_threshold: 50
  suspicious_patterns:
    - "nc"
    - "mimikatz"
```

#### Log Analysis
```yaml
log_analysis:
  brute_force_threshold: 3
  windows_event_logs:
    - "Security"
    - "System"
```

### Customizing Monitored Paths

**Scenario**: Monitor custom application directory

Edit `config/hids/hids_config.yaml`:
```yaml
file_integrity:
  monitored_paths_windows:
    - "C:\\Windows\\System32"
    - "C:\\MyApp"  # Add custom path
    - "D:\\CriticalData"
```

### Adjusting Detection Thresholds

**Scenario**: Reduce false positives from failed logins

```yaml
log_analysis:
  brute_force_threshold: 5  # Increase from 3 to 5
```

---

## Usage

### Starting HIDS

**Linux/macOS**:
```bash
# Using startup script (recommended)
chmod +x scripts/start_hids.sh
sudo ./scripts/start_hids.sh

# Manual start
cd src/hids
sudo python3 hids_main.py --config ../../config/hids/hids_config.yaml
```

**Windows**:
```cmd
REM Using startup script (recommended - Run as Administrator)
scripts\start_hids.bat

REM Manual start
cd src\hids
python hids_main.py --config ..\..\config\hids\hids_config.yaml
```

### Command-Line Options

```bash
python hids_main.py [OPTIONS]

Options:
  --config FILE         Configuration YAML file
  --baseline FILE       Custom baseline file path
  --no-files            Disable file monitoring
  --no-processes        Disable process monitoring
  --no-logs             Disable log monitoring
  --elasticsearch       Enable Elasticsearch export
  --es-host URL         Elasticsearch host (default: http://localhost:9200)
```

### Running Without Elasticsearch

```bash
# Default mode (local logging only)
python hids_main.py --config ../../config/hids/hids_config.yaml
```

### Running With Elasticsearch

**1. Start ELK Stack**:
```bash
cd elk
docker-compose up -d
```

**2. Enable in Config**:
```yaml
elasticsearch_enabled: true
```

**3. Start HIDS**:
```bash
python hids_main.py --config ../../config/hids/hids_config.yaml --elasticsearch
```

### Viewing Alerts

**Local Logs**:
```bash
# Real-time monitoring
tail -f logs/hids_alerts.log

# Windows
Get-Content logs\hids_alerts.log -Wait
```

**Kibana Dashboard**:
1. Open http://localhost:5601
2. Navigate to **Dashboards** → **Hybrid IDS - HIDS Alerts**
3. View real-time visualizations

---

## Testing

### Unit Tests

**Run Complete Test Suite**:
```bash
cd tests
python test_hids.py
```

**Expected Output**:
```
============================================
  HIDS Component Test Suite
============================================

test_create_baseline (TestFileIntegrityMonitor) ... ok
test_detect_modified_file (TestFileIntegrityMonitor) ... ok
test_brute_force_detection (TestLogAnalyzer) ... ok
test_suspicious_process_detection (TestProcessMonitor) ... ok

----------------------------------------------------------------------
Ran 20 tests in 3.456s

OK

============================================
  Test Summary
============================================
Tests Run:     20
Successes:     20
Failures:      0
Errors:        0
============================================
```

### Manual Testing

**Test 1: File Integrity Monitoring**
```bash
# Run standalone
python src/hids/file_monitor.py

# This will:
# 1. Create test directory
# 2. Generate baseline
# 3. Simulate file changes
# 4. Detect and report
```

**Test 2: Log Analysis**
```bash
python src/hids/log_analyzer.py

# Analyzes sample log entries
# Shows detected security events
```

**Test 3: Process Monitoring**
```bash
python src/hids/process_monitor.py

# Scans current processes
# Reports suspicious findings
```

### Integration Testing

**Simulate Attack Scenario**:

```bash
# 1. Start HIDS
python hids_main.py --config config/hids/hids_config.yaml

# 2. In another terminal, simulate suspicious activity:

# Create suspicious file
echo "backdoor" > /tmp/nc.exe

# Simulate failed logins (Linux)
for i in {1..5}; do su - testuser -c "exit" 2>/dev/null; done

# 3. Check alerts
tail -f logs/hids_alerts.log
```

---

## ELK Integration

### Index Patterns

HIDS creates the following Elasticsearch indices:

- `hybrid-ids-hids-alerts-YYYY.MM.DD` - All HIDS alerts

### Alert Schema

```json
{
  "@timestamp": "2025-10-19T10:15:23.456Z",
  "type": "file_integrity",
  "severity": "HIGH",
  "message": "File modified: /etc/passwd",
  "host": "webserver-01",
  "details": {
    "filepath": "/etc/passwd",
    "old_hash": "abc123...",
    "new_hash": "def456...",
    "type": "MODIFIED_FILE"
  }
}
```

### Creating Kibana Visualizations

**1. Alert Severity Pie Chart**:
- Visualization Type: Pie
- Metrics: Count
- Buckets: Split Slices by `severity.keyword`

**2. Alerts Over Time**:
- Visualization Type: Line
- Metrics: Count
- Buckets: X-Axis → Date Histogram on `@timestamp`

**3. Top Suspicious Processes**:
- Visualization Type: Table
- Metrics: Count
- Buckets: Split Rows by `details.name.keyword`

**4. File Changes Map**:
- Visualization Type: Tag Cloud
- Metrics: Count
- Tags: `details.filepath.keyword`

### Importing Dashboards

```bash
# Copy dashboard configuration
cp elk/kibana/dashboards/hids-dashboard.ndjson /tmp/

# Import via Kibana UI
# Management → Stack Management → Saved Objects → Import
```

---

## Troubleshooting

### Common Issues

#### Issue: Permission Denied Errors

**Symptoms**:
```
[ERROR] Failed to read /var/log/auth.log: Permission denied
[ERROR] Access denied for process PID 1234
```

**Solution**:
```bash
# Linux/macOS - Run with sudo
sudo python3 hids_main.py

# Windows - Run as Administrator
# Right-click → Run as Administrator
```

#### Issue: Baseline Not Found

**Symptoms**:
```
[WARNING] Baseline file not found: data/hids_baseline.json
```

**Solution**:
```bash
# Create new baseline
mkdir -p data
python hids_main.py --config config/hids/hids_config.yaml

# First run will automatically create baseline
```

#### Issue: Elasticsearch Connection Failed

**Symptoms**:
```
[ERROR] Failed to connect to Elasticsearch: ConnectionError
```

**Solution**:
```bash
# 1. Check if Elasticsearch is running
curl http://localhost:9200

# 2. Start ELK stack
cd elk
docker-compose up -d

# 3. Wait for startup (30-60 seconds)
docker-compose logs -f elasticsearch

# 4. Verify
curl http://localhost:9200
```

#### Issue: pywin32 Import Error (Windows)

**Symptoms**:
```python
ImportError: No module named 'win32evtlog'
```

**Solution**:
```cmd
pip install pywin32

REM Post-install script (required!)
python venv\Scripts\pywin32_postinstall.py -install
```

#### Issue: Too Many Alerts (False Positives)

**Solution**:

1. **Adjust Thresholds**:
```yaml
# config/hids/hids_config.yaml
log_analysis:
  brute_force_threshold: 5  # Increase
process_monitoring:
  cpu_threshold: 90  # Increase
```

2. **Exclude Patterns**:
```yaml
file_integrity:
  exclude_patterns:
    - "*.tmp"
    - "*.cache"
    - "/var/log/*"  # Exclude noisy paths
```

3. **Whitelist Processes**:
```python
# Edit src/hids/process_monitor.py
# Add to _load_suspicious_patterns():
# Exclude known-good processes
```

---

## Performance Tuning

### Reducing CPU Usage

**1. Increase Check Intervals**:
```yaml
check_interval: 300       # 5 minutes instead of 60 seconds
log_check_interval: 600   # 10 minutes instead of 5
```

**2. Limit File Scanning**:
```yaml
file_integrity:
  # Monitor only critical paths
  monitored_paths_linux:
    - "/etc"  # Remove less critical paths
  file_extensions:
    - ".so"   # Only monitor specific extensions
```

**3. Process Scan Optimization**:
```yaml
performance:
  max_processes: 500  # Limit scan count
```

### Reducing Memory Usage

**1. Clear Alerts Periodically**:
```python
# hids_main.py automatically clears after export
# Adjust retention if needed
```

**2. Disable Unused Components**:
```yaml
file_monitoring: false  # If not needed
process_monitoring: true
log_monitoring: true
```

### Scaling for Large Environments

**Distributed Deployment**:

```
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Host 1   │   │ Host 2   │   │ Host 3   │
│ HIDS     │   │ HIDS     │   │ HIDS     │
└────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │
     └──────────────┼──────────────┘
                    ▼
        ┌───────────────────────┐
        │  Central Elasticsearch│
        │  Cluster              │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Kibana Dashboard     │
        │  (All Hosts)          │
        └───────────────────────┘
```

**Configuration per Host**:
```yaml
hostname: "webserver-01"  # Unique per host
elasticsearch_enabled: true
elasticsearch_hosts:
  - "http://elk-cluster.internal:9200"
```

---

## Best Practices

### 1. Baseline Management

- **Initial Baseline**: Create on clean system BEFORE deployment
- **Update Baseline**: After legitimate system updates
- **Backup Baseline**: Store securely for disaster recovery

```bash
# Create baseline
python hids_main.py --config config/hids/hids_config.yaml

# Backup
cp data/hids_baseline.json data/hids_baseline_backup_$(date +%Y%m%d).json

# Restore
cp data/hids_baseline_backup_20251019.json data/hids_baseline.json
```

### 2. Alert Triage

**Priority Levels**:
1. **CRITICAL**: Brute force, suspicious commands → Investigate immediately
2. **HIGH**: File modifications, privilege escalation → Investigate within 1 hour
3. **MEDIUM**: New processes, service changes → Review daily
4. **LOW**: Informational → Review weekly

### 3. Log Retention

```yaml
alerts:
  retention_days: 30  # Keep 30 days locally

# Elasticsearch index lifecycle
# Automatically managed by ELK stack
```

### 4. Testing in Production

- **Staged Rollout**: Test on 1-2 hosts first
- **Monitor Performance**: CPU/memory impact
- **Tune Thresholds**: Adjust based on false positive rate
- **User Training**: Educate admins on alert interpretation

---

## Advanced Features

### Custom Detection Rules

**Add Custom Log Rule**:

Edit [`src/hids/log_analyzer.py`](src/hids/log_analyzer.py):

```python
def _load_detection_rules(self):
    return [
        # Existing rules...
        {
            'name': 'Cryptocurrency Mining',
            'pattern': r'(xmrig|ethminer|cgminer)',
            'severity': 'CRITICAL',
            'category': 'cryptomining'
        }
    ]
```

### Webhook Alerts

**Send alerts to Slack/Teams**:

```python
# Add to hids_main.py _export_alerts()
import requests

def send_webhook(alert):
    if alert['severity'] == 'CRITICAL':
        webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK"
        requests.post(webhook_url, json={"text": alert['message']})
```

### Email Notifications

```python
import smtplib
from email.mime.text import MIMEText

def send_email(alert):
    msg = MIMEText(json.dumps(alert, indent=2))
    msg['Subject'] = f"[HIDS] {alert['severity']} Alert"
    msg['From'] = 'hids@company.com'
    msg['To'] = 'security-team@company.com'

    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()
```

---

## Quick Reference

### Start HIDS
```bash
# Linux
sudo ./scripts/start_hids.sh

# Windows (as Admin)
scripts\start_hids.bat
```

### View Alerts
```bash
tail -f logs/hids_alerts.log
```

### Test Components
```bash
python tests/test_hids.py
```

### Elasticsearch Status
```bash
curl http://localhost:9200/_cat/indices?v | grep hybrid-ids-hids
```

### Common Directories
- **Config**: `config/hids/`
- **Logs**: `logs/`
- **Data**: `data/`
- **Source**: `src/hids/`

---

## Support

For issues, questions, or contributions:

- **GitHub Issues**: https://github.com/SyedMisbahGit/HYBRID-IDS-MCP/issues
- **Documentation**: This file + [README.md](README.md)
- **Project Guide**: [ARCHITECTURE_EXPLAINED.md](ARCHITECTURE_EXPLAINED.md)

---

**Project**: Hybrid IDS - Two-Tier Detection System
**Component**: HIDS (Host-based Intrusion Detection)
**Author**: Syed Misbah Uddin
**Institution**: Central University of Jammu
**Last Updated**: October 2025
