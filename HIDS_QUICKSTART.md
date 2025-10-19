# HIDS Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies (1 minute)

```bash
# Navigate to project
cd Hybrid-IDS-MCP

# Install Python dependencies
pip install psutil pyyaml watchdog elasticsearch

# Windows only (for Event Log monitoring)
pip install pywin32
```

### Step 2: Test Components (2 minutes)

```bash
# Test file monitor
python src/hids/file_monitor.py
# ✅ Should show: "Test completed successfully!"

# Test log analyzer
python src/hids/log_analyzer.py
# ✅ Should detect: 8 security events

# Test process monitor
python src/hids/process_monitor.py
# ✅ Should scan processes and show statistics

# Run full test suite
python tests/test_hids.py
# ✅ Should pass: 20/20 tests
```

### Step 3: Start HIDS (2 minutes)

**Linux/macOS:**
```bash
# Make script executable
chmod +x scripts/start_hids.sh

# Start HIDS (requires sudo for full monitoring)
sudo ./scripts/start_hids.sh
```

**Windows:**
```cmd
REM Run Command Prompt as Administrator
REM Then execute:
scripts\start_hids.bat
```

**Or start manually:**
```bash
cd src/hids
python hids_main.py --config ../../config/hids/hids_config.yaml
```

### Step 4: View Alerts

**Real-time monitoring:**
```bash
# Linux/macOS
tail -f logs/hids_alerts.log

# Windows PowerShell
Get-Content logs\hids_alerts.log -Wait
```

**View statistics:**
- HIDS prints stats every 5 minutes
- Press Ctrl+C to stop and see final summary

---

## Optional: Enable Elasticsearch Dashboard

### Step 1: Start ELK Stack

```bash
cd elk
docker-compose up -d

# Wait 30-60 seconds for startup
docker-compose logs -f elasticsearch
# Watch for: "started"
```

### Step 2: Enable in HIDS Config

Edit `config/hids/hids_config.yaml`:
```yaml
elasticsearch_enabled: true
```

### Step 3: Restart HIDS

```bash
# Stop HIDS (Ctrl+C)
# Start with Elasticsearch
cd src/hids
python hids_main.py --config ../../config/hids/hids_config.yaml --elasticsearch
```

### Step 4: View Dashboard

1. Open browser: http://localhost:5601
2. Navigate to: **Discover**
3. Create index pattern: `hybrid-ids-hids-alerts-*`
4. View real-time HIDS alerts!

---

## Common Commands

### Start/Stop

```bash
# Start HIDS
./scripts/start_hids.sh

# Start without file monitoring
python src/hids/hids_main.py --no-files

# Start without process monitoring
python src/hids/hids_main.py --no-processes

# Start without log monitoring
python src/hids/hids_main.py --no-logs

# Stop HIDS
# Press Ctrl+C
```

### View Logs

```bash
# Alert log
tail -f logs/hids_alerts.log

# HIDS system log (if configured)
tail -f logs/hids.log

# View alert count
wc -l logs/hids_alerts.log
```

### Manage Baseline

```bash
# View baseline
cat data/hids_baseline.json

# Backup baseline
cp data/hids_baseline.json data/hids_baseline_backup.json

# Delete baseline (will recreate on next run)
rm data/hids_baseline.json
```

### Test Specific Component

```bash
# File integrity only
python src/hids/file_monitor.py

# Log analysis only
python src/hids/log_analyzer.py

# Process monitoring only
python src/hids/process_monitor.py

# Full test suite
python tests/test_hids.py
```

---

## Configuration Quick Reference

**Location:** `config/hids/hids_config.yaml`

**Key Settings:**

```yaml
# Check intervals (seconds)
check_interval: 60          # File & process checks
log_check_interval: 300     # Log analysis

# Enable/disable components
file_monitoring: true
process_monitoring: true
log_monitoring: true

# Elasticsearch
elasticsearch_enabled: false
elasticsearch_hosts:
  - "http://localhost:9200"

# File paths to monitor
file_integrity:
  monitored_paths_windows:
    - "C:\\Windows\\System32"
  monitored_paths_linux:
    - "/etc"
    - "/bin"

# Suspicious process patterns
process_monitoring:
  suspicious_patterns:
    - "nc"
    - "mimikatz"
    - "meterpreter"

# Brute force threshold
log_analysis:
  brute_force_threshold: 3   # Failed login attempts
```

---

## Troubleshooting

### "Permission Denied"
```bash
# Run with elevated privileges
sudo python hids_main.py    # Linux
# Run as Administrator      # Windows
```

### "Baseline not found"
```
# Normal on first run - will auto-create
# Check: data/hids_baseline.json created after first run
```

### "Cannot connect to Elasticsearch"
```bash
# Make sure ELK is running
cd elk && docker-compose ps

# If not running, start it
docker-compose up -d
```

### "Too many alerts"
```yaml
# Adjust thresholds in config/hids/hids_config.yaml
check_interval: 300           # Increase interval
brute_force_threshold: 5      # Less sensitive
```

---

## Example Alert Output

```json
{
  "timestamp": "2025-10-19T10:15:23",
  "type": "MODIFIED_FILE",
  "severity": "HIGH",
  "filepath": "/etc/passwd",
  "message": "File modified: /etc/passwd",
  "old_hash": "abc123...",
  "new_hash": "def456..."
}
```

```json
{
  "timestamp": "2025-10-19T10:16:30",
  "type": "POSSIBLE_BRUTE_FORCE",
  "severity": "CRITICAL",
  "username": "admin",
  "previous_failures": 5,
  "message": "Brute force attack detected"
}
```

```json
{
  "timestamp": "2025-10-19T10:21:45",
  "type": "SUSPICIOUS_PROCESS",
  "severity": "HIGH",
  "pid": 1234,
  "name": "nc.exe",
  "message": "Suspicious process detected"
}
```

---

## Detection Capabilities

| Category | What It Detects |
|----------|-----------------|
| **File Integrity** | New files, modified files, deleted files in critical directories |
| **Authentication** | Failed logins, brute force attacks, unauthorized access |
| **Privilege Escalation** | Sudo usage, UAC elevation, permission changes |
| **Account Management** | User creation, deletion, password changes |
| **Suspicious Activity** | Netcat, Mimikatz, PowerShell exploits, malicious commands |
| **Network** | Suspicious ports (4444, 1337, etc.), unusual connections |
| **System Changes** | Service modifications, firewall changes, reboots |

---

## Performance

**Resource Usage:**
- CPU: 2-5% (4-core system)
- Memory: ~100-200 MB
- Disk I/O: Minimal

**Scalability:**
- Files: 1,000-10,000+ monitored
- Logs: 1,000-5,000 lines/minute
- Processes: 100-500 per scan

---

## Next Steps

After basic setup:

1. **Customize Monitoring**
   - Edit `config/hids/hids_config.yaml`
   - Add your critical file paths
   - Adjust detection thresholds

2. **Set Up Dashboard**
   - Enable Elasticsearch integration
   - Create Kibana visualizations
   - Build custom dashboards

3. **Production Deployment**
   - Run as system service (systemd/Windows Service)
   - Configure log rotation
   - Set up alerting (email, Slack, etc.)

4. **Read Full Documentation**
   - [HIDS_GUIDE.md](HIDS_GUIDE.md) - Complete guide
   - [HIDS_COMPLETE.md](HIDS_COMPLETE.md) - Implementation summary

---

**Need Help?**
- See: [HIDS_GUIDE.md](HIDS_GUIDE.md#troubleshooting)
- Issues: https://github.com/SyedMisbahGit/HYBRID-IDS-MCP/issues

**Happy Monitoring! 🛡️**
