# Hybrid IDS Integration Guide

Complete guide for the integrated NIDS + HIDS system with unified alerting and dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Installation](#installation)
- [Configuration](#configuration)
- [Starting the System](#starting-the-system)
- [Dashboard Access](#dashboard-access)
- [Alert Management](#alert-management)
- [Event Correlation](#event-correlation)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## Overview

The Hybrid IDS integrates Network-based (NIDS) and Host-based (HIDS) intrusion detection systems into a unified platform with:

- **Unified Alert Management**: Single interface for all security alerts
- **Event Correlation**: Cross-system correlation to detect multi-stage attacks
- **Real-time Dashboard**: Kibana-based visualization of security events
- **Machine Learning Integration**: Anomaly detection and attack classification
- **Automated Response**: Configurable response actions for detected threats

### Key Features

✅ **Comprehensive Coverage**
- Network traffic analysis (NIDS)
- Host-based monitoring (HIDS)
- File integrity monitoring
- Process monitoring
- Log analysis

✅ **Advanced Detection**
- Signature-based detection (30+ rules)
- ML-based anomaly detection
- Cross-system event correlation (10+ correlation rules)
- MITRE ATT&CK mapping

✅ **Unified Dashboard**
- Real-time alert visualization
- Geographic threat maps
- Attack timeline analysis
- Severity-based filtering

✅ **Scalable Architecture**
- Multi-threaded processing
- Queue-based alert handling
- ZeroMQ inter-process communication
- Elasticsearch for data storage

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Hybrid IDS                            │
│                                                               │
│  ┌──────────┐                              ┌──────────┐     │
│  │   NIDS   │                              │   HIDS   │     │
│  │  (C++)   │                              │ (Python) │     │
│  │          │                              │          │     │
│  │ • S-IDS  │                              │ • File   │     │
│  │ • A-IDS  │                              │ • Process│     │
│  │ • Rules  │                              │ • Logs   │     │
│  └────┬─────┘                              └────┬─────┘     │
│       │                                         │            │
│       │ ZMQ (5556)                  ZMQ (5557) │            │
│       │                                         │            │
│       └─────────────┬───────────────────────────┘            │
│                     │                                        │
│            ┌────────▼────────┐                               │
│            │ Unified Alert   │                               │
│            │    Manager      │                               │
│            └────────┬────────┘                               │
│                     │                                        │
│            ┌────────▼────────┐                               │
│            │     Event       │                               │
│            │  Correlator     │                               │
│            └────────┬────────┘                               │
│                     │                                        │
│         ┌───────────┼───────────┐                            │
│         │           │           │                            │
│    ┌────▼───┐  ┌───▼────┐  ┌──▼─────┐                      │
│    │Console │  │  File  │  │  ELK   │                      │
│    │        │  │        │  │ Stack  │                      │
│    └────────┘  └────────┘  └───┬────┘                      │
│                                 │                            │
└─────────────────────────────────┼────────────────────────────┘
                                  │
                         ┌────────▼────────┐
                         │     Kibana      │
                         │   Dashboard     │
                         └─────────────────┘
```

### Data Flow

1. **Detection Layer**
   - NIDS captures network packets → Analyzes with signatures/ML → Generates alerts
   - HIDS monitors host → File/Process/Log analysis → Generates alerts

2. **Integration Layer**
   - Alerts published via ZeroMQ (NIDS: port 5556, HIDS: port 5557)
   - Unified Alert Manager subscribes to both sources
   - Normalizes alerts into common format

3. **Correlation Layer**
   - Event Correlator receives normalized alerts
   - Applies 10+ correlation rules
   - Detects multi-stage attacks (e.g., scan → exploit → lateral movement)

4. **Output Layer**
   - Console: Real-time alert display
   - File: JSON logs for archival
   - Elasticsearch: Structured storage for Kibana

5. **Visualization Layer**
   - Kibana dashboards query Elasticsearch
   - Real-time charts, maps, and tables
   - Drill-down analysis capabilities

---

## Components

### 1. Unified Alert Manager

**Location**: `src/integration/unified_alert_manager.py`

**Purpose**: Central hub for all security alerts

**Features**:
- Multi-source alert ingestion (NIDS, HIDS)
- Alert normalization and enrichment
- Deduplication
- Multi-output routing (console, file, Elasticsearch)
- Queue-based processing (10,000 alert buffer)

**Configuration**:
```yaml
alert_manager:
  inputs:
    nids:
      enabled: true
      endpoint: "tcp://localhost:5556"
    hids:
      enabled: true
      endpoint: "tcp://localhost:5557"

  outputs:
    console:
      enabled: true
      verbose: true
    file:
      enabled: true
      directory: "logs/alerts"
    elasticsearch:
      enabled: true
      host: "http://localhost:9200"
```

### 2. Event Correlator

**Location**: `src/integration/event_correlator.py`

**Purpose**: Detect complex, multi-stage attacks

**Correlation Rules**:

| Rule ID | Name | Description | Time Window |
|---------|------|-------------|-------------|
| CR001 | Port Scan to Exploitation | Port scan followed by exploit | 10 min |
| CR002 | Network to Process Compromise | Network attack → suspicious process | 5 min |
| CR003 | Brute Force to Lateral Movement | Brute force → lateral movement | 30 min |
| CR004 | Network Attack to File Modification | Web attack → file changes | 10 min |
| CR005 | Multi-Vector Attack (APT) | Multiple attack types from same IP | 1 hour |
| CR006 | DNS Tunneling and Exfiltration | DNS tunnel + file access | 15 min |
| CR007 | Privilege Escalation Chain | Network compromise → privilege esc | 10 min |
| CR008 | DDoS Smokescreen Attack | DDoS + reconnaissance | 30 min |
| CR009 | Malware Installation Chain | Download → execution → file creation | 5 min |
| CR010 | ML-Detected APT Pattern | ML anomalies across network + host | 30 min |

**Features**:
- Sliding time window (configurable)
- IP-based correlation
- Hostname-based correlation
- Pattern matching with regex
- Automatic MITRE ATT&CK mapping

### 3. Integration Controller

**Location**: `src/integration/hybrid_ids.py`

**Purpose**: Main orchestration of all components

**Responsibilities**:
- Initialize all subsystems
- Manage component lifecycle
- Coordinate HIDS and alert manager
- Monitor system health
- Report statistics

**Usage**:
```bash
python hybrid_ids.py -c config/hybrid_ids_config.yaml
```

### 4. ELK Stack Integration

**Components**:
- **Elasticsearch**: Alert storage and indexing
- **Logstash**: Log processing pipeline
- **Kibana**: Visualization and dashboards

**Indices**:
- `hybrid-ids-alerts-YYYY.MM.DD`: All alerts
- `hybrid-ids-critical-YYYY.MM.DD`: Critical alerts only
- `hybrid-ids-correlated-YYYY.MM.DD`: Correlated events

**Dashboards**:
- **Main Dashboard**: Alert overview, severity distribution
- **Threat Analysis**: Attack patterns, MITRE mapping
- **Network Traffic**: Geographic analysis, source/dest analysis
- **Host Activity**: File/process/log events

---

## Installation

### Prerequisites

**Software**:
- Python 3.10+
- CMake 3.15+
- GCC/Clang (Linux) or MSVC (Windows)
- Docker + Docker Compose (optional, for ELK)
- libpcap-dev (Linux) or Npcap (Windows)

**Python Packages**:
```bash
pip install -r requirements.txt
```

Required packages:
- pyyaml
- pyzmq
- elasticsearch
- psutil
- watchdog
- numpy
- pandas
- scikit-learn

### Installation Steps

#### Linux/macOS

```bash
# 1. Clone repository
git clone https://github.com/SyedMisbahGit/HYBRID-IDS-MCP.git
cd HYBRID-IDS-MCP

# 2. Install system dependencies
# Ubuntu/Debian:
sudo apt update
sudo apt install build-essential cmake libpcap-dev python3 python3-pip

# macOS:
brew install cmake libpcap python3

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Build NIDS
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . -j$(nproc)
cd ..

# 5. (Optional) Start ELK Stack
cd elk
docker-compose up -d
cd ..

# 6. Done! Ready to run
```

#### Windows

```batch
REM 1. Install prerequisites
REM - Install Python 3.10+ from python.org
REM - Install Visual Studio 2022 with C++ tools
REM - Install CMake from cmake.org
REM - Install Npcap from npcap.com

REM 2. Clone repository
git clone https://github.com/SyedMisbahGit/HYBRID-IDS-MCP.git
cd HYBRID-IDS-MCP

REM 3. Install Python dependencies
pip install -r requirements.txt

REM 4. Build NIDS
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release
cd ..

REM 5. (Optional) Start ELK Stack
cd elk
docker-compose up -d
cd ..

REM 6. Done! Ready to run
```

---

## Configuration

### Main Configuration File

**Location**: `config/hybrid_ids_config.yaml`

**Key Sections**:

#### General Settings
```yaml
general:
  name: "Hybrid-IDS"
  version: "1.0.0"
  environment: "production"
```

#### Component Enable/Disable
```yaml
hids:
  enabled: true
  config_path: "config/hids/hids_config.yaml"

nids:
  enabled: true
  config_path: "config/nids/nids_config.yaml"
```

#### Alert Manager
```yaml
alert_manager:
  outputs:
    console:
      enabled: true
      verbose: true
    elasticsearch:
      enabled: true
      host: "http://localhost:9200"
```

#### Event Correlation
```yaml
correlation:
  enabled: true
  window_seconds: 600  # 10 minutes
  max_events: 10000
```

#### Notifications
```yaml
notifications:
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    to_addresses:
      - "security-team@example.com"
    min_severity: "HIGH"

  slack:
    enabled: false
    webhook_url: ""
    min_severity: "HIGH"
```

---

## Starting the System

### Quick Start (Recommended)

#### Linux/macOS
```bash
sudo ./scripts/start_hybrid_ids.sh
```

#### Windows
```batch
REM Run as Administrator
scripts\start_hybrid_ids.bat
```

The startup script will:
1. Check prerequisites
2. Load configuration
3. Optionally start ELK stack
4. Let you select components to run
5. Select network interface (for NIDS)
6. Build NIDS if needed
7. Start selected components
8. Display access URLs and logs

### Component Selection

The script offers 4 modes:

1. **Complete Hybrid IDS** (Recommended)
   - Starts NIDS + HIDS + Integration
   - Full correlation and unified alerting
   - Best for production deployment

2. **HIDS Only**
   - Only host-based monitoring
   - No network traffic analysis
   - Good for servers without network access

3. **NIDS Only**
   - Only network traffic analysis
   - No host monitoring
   - Good for network appliances

4. **Integration Layer Only**
   - Only alert aggregation and correlation
   - Requires NIDS/HIDS started separately
   - Good for distributed deployments

### Manual Start

If you prefer manual control:

#### Start NIDS
```bash
cd build
sudo ./sids -i eth0  # Replace eth0 with your interface
```

#### Start HIDS (in another terminal)
```bash
cd src/hids
python3 hids_main.py -c ../../config/hids/hids_config.yaml
```

#### Start Integration Layer (in another terminal)
```bash
cd src/integration
python3 hybrid_ids.py -c ../../config/hybrid_ids_config.yaml
```

---

## Dashboard Access

### Kibana Dashboard

Once the ELK stack is running:

1. **Open Kibana**: http://localhost:5601

2. **Import Dashboards**:
   - Go to **Management** → **Stack Management** → **Saved Objects**
   - Click **Import**
   - Select `elk/kibana/dashboards/hybrid-ids-main-dashboard.ndjson`
   - Click **Import**

3. **View Dashboard**:
   - Go to **Dashboard**
   - Select **"Hybrid IDS - Main Dashboard"**

### Dashboard Components

#### Alert Timeline
- Line chart showing alerts over time
- Color-coded by severity
- 24-hour default view

#### Severity Distribution
- Pie chart of alert severities
- Shows CRITICAL, HIGH, MEDIUM, LOW, INFO breakdown

#### Recent Alerts Table
- Real-time table of latest alerts
- Columns: Timestamp, Severity, Source, Title, Description
- Sortable and filterable

#### Source Breakdown
- Pie chart showing alert sources
- NIDS vs HIDS breakdown
- Subcategories (signature, anomaly, file, process, log)

#### Top Attack Types
- Horizontal bar chart
- Top 10 most common attack types
- Click to drill down

#### Geographic Distribution
- World map showing source IPs
- Heat map of attack origins
- Requires GeoIP enrichment

### Creating Index Patterns

If not auto-created:

1. Go to **Stack Management** → **Index Patterns**
2. Click **Create index pattern**
3. Enter pattern: `hybrid-ids-alerts-*`
4. Select time field: `@timestamp`
5. Click **Create**

---

## Alert Management

### Alert Structure

All alerts follow this unified schema:

```json
{
  "alert_id": "nids_signature_1698765432000000",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "source": "nids_signature",
  "severity": "HIGH",
  "title": "SQL Injection Attempt",
  "description": "Potential SQL injection detected in HTTP request",
  "metadata": {
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.50",
    "src_port": 54321,
    "dst_port": 80,
    "protocol": "TCP",
    "rule_id": "1001",
    "mitre_attack": "T1190",
    "confidence": 0.95
  }
}
```

### Alert Sources

- `nids_signature`: NIDS signature-based detection
- `nids_anomaly`: NIDS ML-based anomaly detection
- `hids_file`: HIDS file integrity monitoring
- `hids_process`: HIDS process monitoring
- `hids_log`: HIDS log analysis
- `correlation`: Multi-source correlation

### Alert Severities

- **CRITICAL**: Immediate action required (e.g., active exploit)
- **HIGH**: Important security event (e.g., successful scan)
- **MEDIUM**: Suspicious activity (e.g., policy violation)
- **LOW**: Informational (e.g., unusual but benign)
- **INFO**: General information

### Querying Alerts

#### Via Elasticsearch API

```bash
# Get all critical alerts from today
curl -X GET "localhost:9200/hybrid-ids-alerts-$(date +%Y.%m.%d)/_search" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"term": {"severity": "CRITICAL"}}}'

# Get alerts from specific IP
curl -X GET "localhost:9200/hybrid-ids-alerts-*/_search" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"term": {"metadata.src_ip": "192.168.1.100"}}}'
```

#### Via Kibana Discover

1. Go to **Discover**
2. Select index pattern: `hybrid-ids-alerts-*`
3. Add filters:
   - `severity: CRITICAL`
   - `source: nids_signature`
   - `metadata.mitre_attack: T1190`
4. Save search for later use

### Alert File Logs

Alerts are also written to: `logs/alerts/unified_alerts.jsonl`

```bash
# View recent alerts
tail -f logs/alerts/unified_alerts.jsonl | jq .

# Filter by severity
cat logs/alerts/unified_alerts.jsonl | jq 'select(.severity=="CRITICAL")'

# Count alerts by source
cat logs/alerts/unified_alerts.jsonl | jq -r '.source' | sort | uniq -c
```

---

## Event Correlation

### How It Works

The Event Correlator maintains a sliding window of recent events and applies correlation rules to detect multi-stage attacks.

**Example Scenario**:

1. **10:00:00** - NIDS detects port scan from 192.168.1.100 → Alert A
2. **10:05:30** - NIDS detects SQL injection from 192.168.1.100 → Alert B
3. **Correlation**: Rule CR001 triggers (Port Scan → Exploitation)
4. **Output**: Correlated alert with CRITICAL severity

### Correlation Rule Format

```python
CorrelationRule(
    rule_id="CR001",
    name="Port Scan to Exploitation",
    description="Port scanning activity followed by successful exploitation attempt",
    severity=AlertSeverity.CRITICAL,
    time_window=600,  # 10 minutes
    required_events=[
        {'source': 'nids_signature', 'pattern': 'port.*scan'},
        {'source': 'nids_signature', 'pattern': '(exploit|injection|overflow)'}
    ],
    same_ip=True  # Must be from same IP
)
```

### Viewing Correlated Alerts

Correlated alerts have:
- `source: correlation`
- Metadata includes `correlation_rule_id`, `related_alert_ids`
- Separate Elasticsearch index: `hybrid-ids-correlated-*`

Query in Kibana:
```
source: "correlation"
```

### Adding Custom Rules

Edit `src/integration/event_correlator.py`:

```python
self.correlation_rules.append(CorrelationRule(
    rule_id="CR011",
    name="My Custom Rule",
    description="Description of what this detects",
    severity=AlertSeverity.HIGH,
    time_window=300,  # 5 minutes
    required_events=[
        {'source': 'nids_signature', 'pattern': 'my_pattern'},
        {'source': 'hids_process', 'pattern': 'suspicious'}
    ],
    same_ip=True
))
```

---

## Troubleshooting

### Common Issues

#### 1. NIDS Not Capturing Traffic

**Symptoms**: No NIDS alerts appearing

**Solutions**:
```bash
# Check interface is correct
ip link show  # Linux
ifconfig -a   # macOS

# Check permissions
sudo ./sids -i eth0  # Must run as root

# Check packet capture
sudo tcpdump -i eth0  # Should show packets

# Check NIDS logs
tail -f logs/nids/sids.log
```

#### 2. HIDS Not Starting

**Symptoms**: HIDS crashes or doesn't initialize

**Solutions**:
```bash
# Check Python version
python3 --version  # Must be 3.10+

# Check dependencies
pip3 install -r requirements.txt

# Check permissions for file monitoring
# HIDS needs read access to monitored paths

# Check config
python3 -c "import yaml; yaml.safe_load(open('config/hids/hids_config.yaml'))"
```

#### 3. No Alerts in Elasticsearch

**Symptoms**: Dashboard is empty

**Solutions**:
```bash
# Check Elasticsearch is running
curl http://localhost:9200

# Check Logstash is processing
docker logs elk_logstash_1

# Check index exists
curl http://localhost:9200/_cat/indices

# Manually send test alert
cd src/integration
python3 -c "
from unified_alert_manager import *
manager = UnifiedAlertManager(config)
manager.initialize()
# Send test alert
"
```

#### 4. ZMQ Connection Errors

**Symptoms**: "Connection refused" or "Address already in use"

**Solutions**:
```bash
# Check ports are not in use
netstat -tuln | grep 5556
netstat -tuln | grep 5557

# Check firewall
sudo ufw allow 5556
sudo ufw allow 5557

# Restart components in correct order:
# 1. NIDS/HIDS first (publishers)
# 2. Integration layer second (subscriber)
```

#### 5. High CPU/Memory Usage

**Symptoms**: System slowdown

**Solutions**:
```yaml
# Reduce worker threads in config/hybrid_ids_config.yaml
performance:
  threads:
    alert_processor: 2  # Reduce from 4
    event_correlator: 1  # Reduce from 2

# Reduce queue sizes
  queues:
    alert_queue: 5000  # Reduce from 10000

# Disable correlation if not needed
correlation:
  enabled: false
```

### Debug Mode

Enable detailed logging:

```yaml
# config/hybrid_ids_config.yaml
logging:
  level: "DEBUG"

  components:
    hids: "DEBUG"
    nids: "DEBUG"
    alert_manager: "DEBUG"
    correlator: "DEBUG"
```

Run with verbose output:
```bash
python3 hybrid_ids.py -c config/hybrid_ids_config.yaml --verbose
```

### Logs Location

- **Hybrid IDS**: `logs/hybrid_ids.log`
- **NIDS**: `logs/nids/sids.log`
- **HIDS**: `logs/hids/*.log`
- **Alerts**: `logs/alerts/unified_alerts.jsonl`

### Getting Help

1. Check logs in `logs/` directory
2. Review configuration files
3. Test components individually
4. Check GitHub issues: https://github.com/SyedMisbahGit/HYBRID-IDS-MCP/issues

---

## API Reference

### UnifiedAlertManager API

```python
from unified_alert_manager import UnifiedAlertManager, UnifiedAlert, AlertSource, AlertSeverity

# Initialize
config = {...}
manager = UnifiedAlertManager(config)
manager.initialize()
manager.start()

# Create custom alert
alert = UnifiedAlert(
    source=AlertSource.HIDS_PROCESS,
    severity=AlertSeverity.HIGH,
    title="Custom Alert",
    description="Something suspicious detected",
    metadata={'key': 'value'}
)

# Send alert
manager.add_alert(alert)

# Get statistics
stats = manager.get_stats()
print(f"Total alerts: {stats['total_alerts']}")

# Stop
manager.stop()
```

### EventCorrelator API

```python
from event_correlator import EventCorrelator

# Initialize
config = {'correlation': {'window_seconds': 600}}
correlator = EventCorrelator(config)
correlator.start()

# Process alert (returns correlated alerts if any)
correlated = correlator.process_alert(alert)
if correlated:
    print(f"Correlation detected: {correlated[0].title}")

# Get statistics
stats = correlator.get_stats()
print(f"Correlations found: {stats['correlations_detected']}")

# Stop
correlator.stop()
```

### HybridIDS API

```python
from hybrid_ids import HybridIDS

# Initialize
hybrid_ids = HybridIDS('config/hybrid_ids_config.yaml')
hybrid_ids.initialize()

# Start
hybrid_ids.start()

# Get statistics
hybrid_ids.print_stats()

# Stop
hybrid_ids.stop()
```

---

## Production Deployment

### Recommendations

1. **Hardware Requirements**:
   - CPU: 4+ cores
   - RAM: 8+ GB
   - Disk: 100+ GB for logs/indices
   - Network: Dedicated monitoring interface for NIDS

2. **Security Hardening**:
   - Run components with minimal privileges
   - Enable SSL for Elasticsearch/Kibana
   - Use API keys for authentication
   - Enable alert signing

3. **High Availability**:
   - Deploy Elasticsearch cluster (3+ nodes)
   - Use load balancer for Kibana
   - Run multiple HIDS instances on different hosts
   - Implement alert failover

4. **Performance Tuning**:
   - Adjust worker thread counts based on CPU
   - Tune queue sizes based on alert rate
   - Configure Elasticsearch shard/replica counts
   - Enable batch processing

5. **Monitoring**:
   - Monitor Hybrid IDS health checks
   - Set up alerting for system failures
   - Track alert processing latency
   - Monitor disk space for logs/indices

6. **Backup and Recovery**:
   - Backup Elasticsearch indices regularly
   - Version control configuration files
   - Document custom correlation rules
   - Test disaster recovery procedures

---

## Next Steps

- [HIDS Guide](HIDS_GUIDE.md) - Detailed HIDS documentation
- [NIDS Complete](NIDS_COMPLETE.md) - Detailed NIDS documentation
- [Dashboard Customization](elk/kibana/README.md) - Customize Kibana dashboards
- [Contributing](CONTRIBUTING.md) - Contribute to the project

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Author**: Hybrid IDS Team
