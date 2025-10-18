# 📊 ELK Stack Dashboard - Complete Deployment Guide

**Status:** Production-Ready ELK Integration
**Version:** 1.0.0
**Last Updated:** 2025-10-18

---

## 🎯 Overview

This guide shows you how to deploy a **centralized security dashboard** using the ELK Stack (Elasticsearch, Logstash, Kibana) that combines:

- ✅ **NIDS Signature Alerts** - Real-time attack detection
- ✅ **AI Anomaly Alerts** - Machine learning detections
- ✅ **Network Flow Features** - 78 statistical features
- ✅ **Geographic Visualizations** - Attack source mapping
- ✅ **Threat Intelligence** - MITRE ATT&CK mapping
- ✅ **Performance Metrics** - System health monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Hybrid IDS System                     │
├─────────────────────────────────────────────────────────┤
│  NIDS (C++)           AI Engine (Python)                │
│  └─► nids_alerts.log  └─► ai_alerts.log                 │
│  └─► features.csv                                        │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                    Logstash Pipeline                     │
├─────────────────────────────────────────────────────────┤
│  • Parse JSON alerts                                     │
│  • Enrich with GeoIP                                     │
│  • Calculate derived metrics                             │
│  • Map to MITRE ATT&CK                                   │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                    Elasticsearch                         │
├─────────────────────────────────────────────────────────┤
│  Indices:                                                │
│  • hybrid-ids-nids-alerts-YYYY.MM.DD                     │
│  • hybrid-ids-ai-alerts-YYYY.MM.DD                       │
│  • hybrid-ids-network-features-YYYY.MM.DD                │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│                       Kibana                             │
├─────────────────────────────────────────────────────────┤
│  Dashboards:                                             │
│  • Security Overview                                     │
│  • Threat Intelligence                                   │
│  • Network Analytics                                     │
│  • ML Model Performance                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### **Prerequisites**

- Docker & Docker Compose
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

### **Step 1: Start ELK Stack**

```bash
cd C:\Users\zsyed\Hybrid-IDS-MCP\elk

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Wait 2-3 minutes for all services to start.**

### **Step 2: Verify Services**

```bash
# Elasticsearch (should return cluster info)
curl http://localhost:9200

# Kibana (should return "Kibana is now available")
curl http://localhost:5601/api/status
```

### **Step 3: Access Kibana**

Open browser: **http://localhost:5601**

You should see the Kibana welcome page!

### **Step 4: Test Data Export**

```powershell
# Activate Python environment
cd C:\Users\zsyed\Hybrid-IDS-MCP
venv\Scripts\activate

# Install Elasticsearch Python client
pip install elasticsearch

# Test exporter
python src\exporters\elasticsearch_exporter.py
```

**Expected Output:**
```
============================================================
  Elasticsearch Exporter - Test Mode
============================================================

[INFO] Connecting to Elasticsearch at ['http://localhost:9200']...
[INFO] Connected to Elasticsearch 8.11.0
[INFO] Index templates created successfully
[INFO] Testing NIDS alert export...
[INFO] Testing AI alert export...
[INFO] Testing network features export...

==================================================
  Elasticsearch Export Statistics
==================================================
NIDS Alerts:    1
AI Alerts:      1
Features:       1
Errors:         0
==================================================

✓ Test completed successfully!
Open Kibana at http://localhost:5601 to view the data
```

---

## 📊 Dashboard Visualizations

### **1. Security Overview Dashboard**

**Access:** http://localhost:5601/app/dashboards

**Panels:**
1. **Alert Timeline** - Real-time alert stream
2. **Severity Distribution** - Pie chart of alert severities
3. **Top Attack Types** - Bar chart of threat techniques
4. **Geographic Heat Map** - Where attacks come from
5. **Top Source IPs** - Most active attackers
6. **Protocol Distribution** - TCP/UDP/ICMP breakdown

### **2. Threat Intelligence Dashboard**

**Panels:**
1. **MITRE ATT&CK Tactics** - Mapped attack tactics
2. **Attack Kill Chain** - Reconnaissance → Execution
3. **Threat Trends** - Time-series of attack patterns
4. **Vulnerability Exploits** - Detected exploit attempts

### **3. Network Analytics Dashboard**

**Panels:**
1. **Traffic Volume** - Bytes/packets over time
2. **Flow Duration** - Connection length distribution
3. **Port Activity** - Most active ports
4. **Protocol Statistics** - TCP flags, packet sizes
5. **Bidirectional Flows** - Upload/download ratios

### **4. ML Model Performance**

**Panels:**
1. **Confidence Distribution** - AI detection confidence
2. **Model Predictions** - Random Forest vs Isolation Forest
3. **Inference Latency** - ML performance metrics
4. **Anomaly Rate** - Detection rate over time
5. **False Positive Trend** - Model accuracy tracking

---

## 🎨 Creating Custom Visualizations

### **Step 1: Create Index Pattern**

1. Go to **Stack Management** → **Index Patterns**
2. Click **Create index pattern**
3. Index pattern: `hybrid-ids-nids-alerts-*`
4. Time field: `@timestamp`
5. Click **Create**

Repeat for:
- `hybrid-ids-ai-alerts-*`
- `hybrid-ids-network-features-*`

### **Step 2: Create Visualization**

**Example: Alert Severity Pie Chart**

1. Go to **Visualize Library**
2. Click **Create visualization**
3. Choose **Pie**
4. Select index: `hybrid-ids-nids-alerts-*`
5. Add bucket:
   - Aggregation: **Terms**
   - Field: **severity.keyword**
   - Order by: **Count**
6. Click **Update**
7. Save as "Alert Severity Distribution"

### **Step 3: Add to Dashboard**

1. Go to **Dashboard**
2. Click **Create dashboard**
3. Click **Add** → Select your visualization
4. Arrange panels
5. Save dashboard

---

## 🔧 Configuration Files

### **Logstash Pipelines**

Located in `elk/logstash/pipeline/`:

1. **[nids-alerts.conf](elk/logstash/pipeline/nids-alerts.conf)**
   - Processes NIDS signature alerts
   - Enriches with GeoIP data
   - Maps to MITRE ATT&CK

2. **[ai-alerts.conf](elk/logstash/pipeline/ai-alerts.conf)**
   - Processes AI anomaly alerts
   - Extracts ML model predictions
   - Calculates threat scores

3. **[network-features.conf](elk/logstash/pipeline/network-features.conf)**
   - Processes 78 network features
   - Calculates derived metrics
   - Categorizes traffic patterns

### **Elasticsearch Indices**

| Index Pattern | Purpose | Daily Size (est) |
|---------------|---------|------------------|
| `hybrid-ids-nids-alerts-*` | Signature alerts | ~100MB |
| `hybrid-ids-ai-alerts-*` | Anomaly alerts | ~50MB |
| `hybrid-ids-network-features-*` | Flow features | ~500MB |

### **Index Lifecycle Management**

Automatically delete old indices:

```bash
# In Kibana Dev Tools
PUT /_ilm/policy/hybrid-ids-policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {}
      },
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

---

## 🔌 Integration with Hybrid IDS

### **Real-Time Export (Python)**

Update your AI engine to export to Elasticsearch:

```python
# In src/ai/inference/zmq_subscriber.py

from exporters.elasticsearch_exporter import ElasticsearchExporter

# Initialize
exporter = ElasticsearchExporter()
exporter.connect()

# In your alert handling:
def log_alert(self, flow_id, confidence, details):
    # Existing file logging
    alert = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'flow_id': flow_id,
        'type': 'ANOMALY',
        'confidence': confidence,
        'details': details
    }

    # Also export to Elasticsearch
    exporter.export_ai_alert(alert)
```

### **Batch Export (CSV Features)**

```powershell
# Export features to Elasticsearch
python src\exporters\bulk_feature_exporter.py --input features.csv
```

### **NIDS C++ Integration** (Future)

Add Elasticsearch output to C++ NIDS:

```cpp
// Use libcurl to POST JSON to Elasticsearch
curl_easy_setopt(curl, CURLOPT_URL, "http://localhost:9200/hybrid-ids-nids-alerts/_doc");
curl_easy_setopt(curl, CURLOPT_POSTFIELDS, alert_json.c_str());
```

---

## 📈 Sample Queries

### **Discover Tab Queries (KQL)**

```
# High severity alerts in last 24 hours
severity: "HIGH" and @timestamp > now-24h

# SQL injection attempts
message: "SQL Injection"

# Anomalies with high confidence
confidence > 0.8

# Large traffic flows
total_bytes > 1000000

# Port scans
rule_id: 1003

# Multiple sources targeting same destination
destination.ip: "192.168.1.10"
```

### **Aggregation Queries (Dev Tools)**

```json
# Top 10 source IPs
GET /hybrid-ids-nids-alerts-*/_search
{
  "size": 0,
  "aggs": {
    "top_sources": {
      "terms": {
        "field": "src_ip",
        "size": 10
      }
    }
  }
}

# Alert rate per minute
GET /hybrid-ids-nids-alerts-*/_search
{
  "size": 0,
  "aggs": {
    "alerts_over_time": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "1m"
      }
    }
  }
}

# Average ML confidence
GET /hybrid-ids-ai-alerts-*/_search
{
  "size": 0,
  "aggs": {
    "avg_confidence": {
      "avg": {
        "field": "confidence"
      }
    }
  }
}
```

---

## 🎯 Example Dashboards

### **Dashboard 1: Executive Overview**

**Purpose:** High-level security status for management

**Panels:**
1. Total Alerts (Metric) - Large number
2. Critical Alerts (Metric) - Red if > 0
3. Alert Trend (Line chart) - Last 7 days
4. Top Threats (Table) - Most common attacks
5. Geographic Heat Map - Attack origins
6. Compliance Status (Gauge) - SLA adherence

### **Dashboard 2: SOC Analyst View**

**Purpose:** Detailed investigation and triage

**Panels:**
1. Real-Time Alert Feed (Data table) - Live updates
2. Alert Details (Markdown) - Drill-down view
3. Source IP Investigation (Lens) - IP analysis
4. Network Flow Diagram (Vega) - Connection mapping
5. PCAP Download (Link) - Packet capture access
6. Incident Timeline (Timeline) - Event correlation

### **Dashboard 3: Network Operations**

**Purpose:** Infrastructure and performance monitoring

**Panels:**
1. Bandwidth Usage (Area chart) - Total throughput
2. Protocol Distribution (Pie) - TCP/UDP/ICMP
3. Top Talkers (Table) - Most active hosts
4. Connection States (Bar) - SYN/FIN/RST counts
5. Packet Loss (Gauge) - Network health
6. Latency Heatmap (Heatmap) - Response times

### **Dashboard 4: ML Model Insights**

**Purpose:** AI/ML performance and tuning

**Panels:**
1. Model Accuracy (Metric) - Current precision
2. Confidence Distribution (Histogram) - Score spread
3. Model Comparison (Bar) - RF vs Isolation Forest
4. Inference Time (Line) - Performance trend
5. Feature Importance (Horizontal bar) - Top features
6. Confusion Matrix (Table) - TP/FP/TN/FN

---

## 🛡️ Security Best Practices

### **Production Deployment**

1. **Enable Security Features**
   ```yaml
   # In docker-compose.yml
   environment:
     - xpack.security.enabled=true
     - ELASTIC_PASSWORD=your_strong_password
   ```

2. **Use TLS/SSL**
   ```yaml
   - xpack.security.http.ssl.enabled=true
   - xpack.security.http.ssl.keystore.path=/path/to/keystore.p12
   ```

3. **Restrict Access**
   ```yaml
   # Only allow specific IPs
   - network.host=0.0.0.0
   - discovery.seed_hosts=["specific-ip"]
   ```

4. **Set Resource Limits**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

### **Data Retention**

```bash
# Automatically delete indices older than 30 days
curator --config curator.yml actions.yml
```

---

## 🔍 Troubleshooting

### **Issue: Elasticsearch won't start**

```bash
# Check logs
docker-compose logs elasticsearch

# Common fix: Increase vm.max_map_count (Linux)
sudo sysctl -w vm.max_map_count=262144

# Windows: WSL2 settings
wsl -d docker-desktop
sysctl -w vm.max_map_count=262144
```

### **Issue: No data in Kibana**

```bash
# Check if indices exist
curl http://localhost:9200/_cat/indices?v

# Manually create test data
python src/exporters/elasticsearch_exporter.py

# Check Logstash pipeline
docker-compose logs logstash
```

### **Issue: Slow performance**

```yaml
# Increase heap size in docker-compose.yml
environment:
  - "ES_JAVA_OPTS=-Xms4g -Xmx4g"
  - "LS_JAVA_OPTS=-Xms2g -Xmx2g"
```

---

## 📊 Performance Tuning

### **Elasticsearch Optimization**

```json
# Increase refresh interval for bulk indexing
PUT /hybrid-ids-*/_settings
{
  "index": {
    "refresh_interval": "30s",
    "number_of_replicas": 0
  }
}
```

### **Logstash Optimization**

```yaml
# In logstash.yml
pipeline.workers: 4
pipeline.batch.size: 250
pipeline.batch.delay: 50
```

---

## 📚 Additional Resources

### **Documentation**
- Elasticsearch: https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html
- Kibana: https://www.elastic.co/guide/en/kibana/current/index.html
- Logstash: https://www.elastic.co/guide/en/logstash/current/index.html

### **Tutorials**
- Creating Dashboards: https://www.elastic.co/guide/en/kibana/current/dashboard.html
- KQL Query Language: https://www.elastic.co/guide/en/kibana/current/kuery-query.html
- Visualizations: https://www.elastic.co/guide/en/kibana/current/visualize.html

---

## ✅ Checklist

- [ ] Docker and Docker Compose installed
- [ ] ELK stack started (`docker-compose up -d`)
- [ ] Elasticsearch accessible (http://localhost:9200)
- [ ] Kibana accessible (http://localhost:5601)
- [ ] Index patterns created
- [ ] Test data exported
- [ ] Visualizations created
- [ ] Dashboards configured
- [ ] Real-time export integrated

---

## 🎉 Summary

You now have a **production-ready ELK Stack dashboard** that provides:

✅ **Real-time Security Monitoring**
✅ **Geographic Attack Visualization**
✅ **Threat Intelligence Mapping**
✅ **ML Model Performance Tracking**
✅ **Network Traffic Analytics**
✅ **Customizable Dashboards**
✅ **Automated Data Retention**
✅ **Scalable Architecture**

**Access Dashboard:** http://localhost:5601

**Start ELK:** `docker-compose -f elk/docker-compose.yml up -d`

**Export Data:** `python src/exporters/elasticsearch_exporter.py`

---

**Status:** ✅ Complete & Ready to Deploy
**Version:** 1.0.0
**Last Updated:** 2025-10-18
