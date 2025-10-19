# Hybrid IDS Integration - Quick Start Guide

Get the integrated NIDS + HIDS system running in 10 minutes.

---

## Prerequisites Check

```bash
# Check Python version (need 3.10+)
python3 --version

# Check CMake (need 3.15+)
cmake --version

# Check Docker (optional, for ELK)
docker --version
docker-compose --version
```

---

## Installation (5 minutes)

### Linux/macOS

```bash
# 1. Clone and navigate
git clone https://github.com/SyedMisbahGit/HYBRID-IDS-MCP.git
cd HYBRID-IDS-MCP

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Build NIDS
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j4
cd ..

# 4. Start ELK (optional but recommended)
cd elk && docker-compose up -d && cd ..

# Done! Ready to run.
```

### Windows

```batch
REM 1. Clone and navigate
git clone https://github.com/SyedMisbahGit/HYBRID-IDS-MCP.git
cd HYBRID-IDS-MCP

REM 2. Install Python dependencies
pip install -r requirements.txt

REM 3. Build NIDS
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release
cd ..

REM 4. Start ELK (optional but recommended)
cd elk
docker-compose up -d
cd ..

REM Done! Ready to run.
```

---

## Quick Start (2 minutes)

### Option 1: Automated Startup (Recommended)

```bash
# Linux/macOS
sudo ./scripts/start_hybrid_ids.sh
```

```batch
REM Windows (Run as Administrator)
scripts\start_hybrid_ids.bat
```

The script will guide you through:
1. Component selection (choose #1 for complete system)
2. Network interface selection
3. Automatic startup of all components

### Option 2: Manual Startup

```bash
# Terminal 1: Start NIDS
cd build
sudo ./sids -i eth0  # Replace eth0 with your interface

# Terminal 2: Start Hybrid IDS (includes HIDS)
cd src/integration
python3 hybrid_ids.py -c ../../config/hybrid_ids_config.yaml
```

---

## Verify It's Working (1 minute)

### Check Console Output

You should see:
```
========================================
  HYBRID IDS - Network and Host Intrusion Detection System
========================================
[INFO] Initializing Unified Alert Manager...
[INFO] Alert Manager initialized
[INFO] Initializing Event Correlator...
[INFO] Event Correlator initialized
[INFO] Initializing HIDS...
[INFO] HIDS initialized
========================================
  Hybrid IDS is now running
========================================
```

### Check Logs

```bash
# View unified alerts
tail -f logs/alerts/unified_alerts.jsonl

# View HIDS logs
tail -f logs/hids/*.log

# View NIDS logs
tail -f logs/nids/sids.log
```

### Check Dashboard

1. Open browser: http://localhost:5601
2. Go to **Dashboard**
3. Select **"Hybrid IDS - Main Dashboard"**

If you don't see the dashboard:
- Go to **Management** → **Saved Objects** → **Import**
- Import `elk/kibana/dashboards/hybrid-ids-main-dashboard.ndjson`

---

## Generate Test Traffic (1 minute)

### Test NIDS Detection

```bash
# SQL injection attempt (will trigger alert)
curl "http://192.168.1.1/test?id=1' OR '1'='1"

# Port scan (will trigger alert)
nmap -sS 192.168.1.1

# XSS attempt (will trigger alert)
curl "http://192.168.1.1/test?name=<script>alert('xss')</script>"
```

### Test HIDS Detection

```bash
# Create suspicious file (will trigger alert)
touch /tmp/suspicious_file.sh
echo "rm -rf /" > /tmp/suspicious_file.sh

# Simulate process activity
for i in {1..10}; do sleep 1 & done
```

### Test Correlation

```bash
# 1. Port scan
nmap -sS 192.168.1.1

# 2. Within 10 minutes, attempt SQL injection
curl "http://192.168.1.1/test?id=1' OR '1'='1"

# This should trigger correlation rule CR001: Port Scan to Exploitation
```

---

## View Alerts (1 minute)

### Console

Alerts appear in real-time on the console:
```
[HIGH] [nids_signature] SQL Injection Attempt
  Description: Potential SQL injection detected in HTTP request
  Time: 2025-10-20T12:34:56
  ID: nids_signature_1698765432000000
```

### File

```bash
# View all alerts
cat logs/alerts/unified_alerts.jsonl | jq .

# Filter by severity
cat logs/alerts/unified_alerts.jsonl | jq 'select(.severity=="CRITICAL")'

# Count alerts by source
cat logs/alerts/unified_alerts.jsonl | jq -r '.source' | sort | uniq -c
```

### Kibana Dashboard

1. Go to http://localhost:5601
2. Navigate to **Dashboard** → **"Hybrid IDS - Main Dashboard"**
3. See visualizations:
   - Alert Timeline (last 24 hours)
   - Severity Distribution
   - Source Breakdown
   - Top Attack Types
   - Geographic Distribution

### Elasticsearch

```bash
# Query all alerts from today
curl "localhost:9200/hybrid-ids-alerts-$(date +%Y.%m.%d)/_search?pretty"

# Get count of critical alerts
curl "localhost:9200/hybrid-ids-alerts-*/_count?q=severity:CRITICAL"

# Search for SQL injection alerts
curl -X POST "localhost:9200/hybrid-ids-alerts-*/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"match": {"title": "SQL Injection"}}}'
```

---

## Configuration (Optional)

### Quick Config Changes

Edit `config/hybrid_ids_config.yaml`:

```yaml
# Enable/disable components
hids:
  enabled: true
nids:
  enabled: true

# Adjust alert outputs
alert_manager:
  outputs:
    console:
      enabled: true
      verbose: true  # Set false for less output
    elasticsearch:
      enabled: true

# Email notifications
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    to_addresses:
      - "security-team@example.com"
    min_severity: "HIGH"  # Only email HIGH and CRITICAL
```

### HIDS Configuration

Edit `config/hids/hids_config.yaml`:

```yaml
file_monitor:
  enabled: true
  paths:
    - /etc
    - /var/www
    - /home  # Add paths to monitor

process_monitor:
  scan_interval: 30  # Scan every 30 seconds

log_analyzer:
  log_files:
    - /var/log/auth.log  # Add logs to analyze
    - /var/log/syslog
```

### NIDS Configuration

Edit `config/nids/nids_config.yaml`:

```yaml
capture:
  interface: "eth0"  # Your network interface
  capture_filter: "tcp or udp"  # Packet filter

threading:
  thread_count: 4  # Adjust based on CPU cores

aids:
  enabled: true
  confidence_threshold: 0.85  # ML confidence threshold
```

---

## Common Commands

### Start/Stop

```bash
# Start complete system
sudo ./scripts/start_hybrid_ids.sh

# Stop (Ctrl+C in the terminal)

# Restart ELK stack
cd elk && docker-compose restart && cd ..
```

### View Status

```bash
# Check processes
ps aux | grep -E "(sids|hids|hybrid_ids)"

# Check ports
netstat -tuln | grep -E "(5556|5557|9200|5601)"

# Check disk space
du -sh logs/
```

### Maintenance

```bash
# Clear old logs (keep last 7 days)
find logs/ -name "*.log" -mtime +7 -delete

# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz config/

# Export dashboard
cd elk/kibana/dashboards
# Import new dashboards via Kibana UI
```

---

## Troubleshooting

### NIDS Not Working

```bash
# Check interface exists
ip link show
# or
ifconfig -a

# Run with sudo
sudo ./build/sids -i eth0

# Check libpcap
ldd build/sids | grep pcap
```

### HIDS Not Working

```bash
# Check Python version
python3 --version  # Must be 3.10+

# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall

# Check config syntax
python3 -c "import yaml; print(yaml.safe_load(open('config/hids/hids_config.yaml')))"
```

### No Alerts in Dashboard

```bash
# Check Elasticsearch
curl http://localhost:9200

# Check if index exists
curl "http://localhost:9200/_cat/indices?v" | grep hybrid-ids

# Restart Logstash
docker-compose -f elk/docker-compose.yml restart logstash

# Check Logstash pipeline
docker logs elk_logstash_1
```

### High CPU Usage

```yaml
# Edit config/hybrid_ids_config.yaml
performance:
  threads:
    alert_processor: 2  # Reduce from 4
    event_correlator: 1  # Reduce from 2

  queues:
    alert_queue: 5000  # Reduce from 10000
```

---

## What's Next?

### Learn More

- **Full Integration Guide**: See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **HIDS Details**: See [HIDS_GUIDE.md](HIDS_GUIDE.md)
- **NIDS Details**: See [NIDS_COMPLETE.md](NIDS_COMPLETE.md)

### Customize

- Add custom NIDS detection rules in `config/nids/rules/`
- Add custom HIDS patterns in `config/hids/hids_config.yaml`
- Create custom correlation rules in `src/integration/event_correlator.py`
- Build custom Kibana dashboards

### Production Deployment

- Enable SSL for Elasticsearch/Kibana
- Set up email/Slack notifications
- Configure log rotation
- Implement backup procedures
- Deploy on dedicated hardware
- Set up monitoring and alerting

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Start system | `sudo ./scripts/start_hybrid_ids.sh` |
| View alerts | `tail -f logs/alerts/unified_alerts.jsonl` |
| View dashboard | http://localhost:5601 |
| Query alerts | `curl localhost:9200/hybrid-ids-alerts-*/_search` |
| Stop system | `Ctrl+C` |
| Check status | `ps aux \| grep hybrid` |
| View logs | `tail -f logs/hybrid_ids.log` |

---

## Support

- **Documentation**: See `docs/` directory
- **Issues**: https://github.com/SyedMisbahGit/HYBRID-IDS-MCP/issues
- **Configuration**: `config/` directory
- **Logs**: `logs/` directory

---

**You're all set! The Hybrid IDS is now protecting your network and hosts.**
