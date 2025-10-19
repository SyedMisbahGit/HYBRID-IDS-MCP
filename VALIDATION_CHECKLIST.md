# Hybrid IDS - Testing & Validation Checklist

**Final Year B.Tech Project**
**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Department:** CSE - Cybersecurity

---

## Overview

This checklist helps verify that all components of my Hybrid IDS system are working correctly for project demonstration and viva voce. It covers minimum viable implementation as well as advanced features.

---

## Phase 1: Build Verification

### ✅ NIDS Engine Build

- [ ] C++ build completes without errors
  ```bash
  cd build
  cmake .. -DCMAKE_BUILD_TYPE=Release
  cmake --build . --config Release -j4
  ```
  **Expected**: Build succeeds with 0 errors

- [ ] Executables created
  ```bash
  ls -lh nids sids feature_extractor  # Linux
  ls -lh nids.exe sids.exe feature_extractor.exe  # Windows
  ```
  **Expected**: All 3 executables present

- [ ] Version check
  ```bash
  ./nids --version
  ```
  **Expected**: Shows version information

- [ ] Interface listing
  ```bash
  ./nids --list-interfaces
  ```
  **Expected**: Shows available network interfaces

---

## Phase 2: Component Testing

### ✅ NIDS Signature Detection

**Test 1: PCAP File Analysis**
```bash
cd build
./sids -r ../test_data/sample.pcap
```

**Validation:**
- [ ] No errors during PCAP processing
- [ ] `nids_alerts.log` file created
- [ ] Log contains JSON-formatted alerts
- [ ] Sample alert structure:
  ```json
  {
    "timestamp": "2025-10-19T10:30:45",
    "severity": "HIGH",
    "rule_id": 1001,
    "message": "Port Scan Detected",
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.5"
  }
  ```

**Test 2: Feature Extraction**
```bash
./nids -r ../test_data/sample.pcap --extract-features --export-csv features.csv
```

**Validation:**
- [ ] `features.csv` file created
- [ ] CSV has 78 columns
- [ ] Each row represents a network flow
- [ ] No NaN or Inf values

### ✅ AI Engine

**Test 1: Model Loading**
```bash
cd ../src/ai/inference
python anomaly_detector.py --model-dir ../../../models --test-mode
```

**Validation:**
- [ ] Models load without errors
- [ ] No "Model file not found" errors
- [ ] No "Array dimension mismatch" errors
- [ ] Output shows: `[INFO] Loaded models: Random Forest, Isolation Forest`

**Test 2: Array Handling Fix**
```bash
cd ../../../scripts
python test_ai_fix.py
```

**Validation:**
- [ ] Test passes: `✓ 1D array handling works`
- [ ] Test passes: `✓ 2D array handling works`
- [ ] Test passes: `✓ Both predict() and predict_batch() work`
- [ ] No exceptions or errors

**Test 3: Real-time Inference**
```bash
cd ../src/ai/inference
python zmq_subscriber.py --model-dir ../../../models --test-mode
```

**Validation:**
- [ ] ZMQ subscriber starts without errors
- [ ] Shows: `Waiting for features...`
- [ ] No connection errors (if ZMQ server not running, should gracefully wait)

### ✅ HIDS Components

**Test 1: File Integrity Monitoring**
```bash
cd ../hids
python file_monitor.py --create-baseline
```

**Validation:**
- [ ] `baseline.json` file created
- [ ] Contains SHA256 hashes
- [ ] No permission errors
- [ ] Sample entry:
  ```json
  {
    "/etc/hosts": {
      "hash": "abc123...",
      "size": 1024,
      "modified": "2025-10-19T10:00:00"
    }
  }
  ```

**Test 2: File Change Detection**
```bash
# Modify a monitored file
echo "# test" >> /path/to/monitored/file  # Linux
echo "# test" >> C:\monitored\file.txt    # Windows

# Run check
python file_monitor.py --check
```

**Validation:**
- [ ] Detects file modification
- [ ] Alert logged to console
- [ ] Alert includes old and new hash

**Test 3: Log Analysis**
```bash
python log_analyzer.py --scan
```

**Validation:**
- [ ] Scans system logs
- [ ] No permission errors
- [ ] If security events found, shows alert
- [ ] No crashes or exceptions

**Test 4: Process Monitoring**
```bash
python process_monitor.py --scan
```

**Validation:**
- [ ] Lists running processes
- [ ] Detects network connections
- [ ] No errors accessing process information

**Test 5: Integrated HIDS**
```bash
python hids_main.py --config config/hids_config.json --test-mode
```

**Validation:**
- [ ] All 3 modules initialize
- [ ] `hids_alerts.log` file created
- [ ] Runs for 60 seconds without crashing
- [ ] Press Ctrl+C to stop gracefully

---

## Phase 3: ELK Stack Deployment

### ✅ Docker Services

**Start ELK Stack:**
```bash
cd ../../elk
docker-compose up -d
```

**Validation:**
- [ ] All containers start: `docker-compose ps`
  - [ ] elasticsearch (healthy)
  - [ ] logstash (up)
  - [ ] kibana (up)
  - [ ] filebeat (up)

**Test 1: Elasticsearch Health**
```bash
curl http://localhost:9200/_cluster/health?pretty
```

**Expected Output:**
```json
{
  "cluster_name": "hybrid-ids-cluster",
  "status": "yellow",  // or "green"
  "number_of_nodes": 1
}
```

**Validation:**
- [ ] Status is "yellow" or "green" (NOT "red")
- [ ] Cluster name matches configuration

**Test 2: Elasticsearch Indices**
```bash
curl http://localhost:9200/_cat/indices?v
```

**Validation:**
- [ ] Command succeeds (may show no indices yet - that's OK)
- [ ] No connection errors

**Test 3: Logstash Pipeline**
```bash
docker-compose logs logstash | grep "Pipeline started"
```

**Validation:**
- [ ] Shows: `Pipeline started {"pipeline.id"=>"main"}`
- [ ] No pipeline errors
- [ ] All 4 pipelines loaded:
  - [ ] nids-alerts.conf
  - [ ] ai-alerts.conf
  - [ ] hids-alerts.conf
  - [ ] network-features.conf

**Test 4: Kibana Access**
```bash
curl http://localhost:5601/api/status
```

**Validation:**
- [ ] Returns JSON status
- [ ] `"state": "green"`
- [ ] Can access in browser: http://localhost:5601

---

## Phase 4: Data Flow Integration

### ✅ NIDS → Elasticsearch

**Start NIDS with logging:**
```bash
cd ../build
./nids -i eth0 --extract-features &  # Linux
./nids -i "Ethernet" --extract-features &  # Windows

# Let it run for 1 minute to capture traffic
sleep 60
```

**Validation:**
- [ ] `nids_alerts.log` file exists and growing
- [ ] File contains JSON alerts
- [ ] No errors in NIDS output

**Check Elasticsearch ingestion:**
```bash
# Wait for Logstash to process (30 seconds)
sleep 30

# Check for NIDS alerts in Elasticsearch
curl "http://localhost:9200/hybrid-ids-nids-alerts-*/_count?pretty"
```

**Validation:**
- [ ] Count > 0 (alerts were ingested)
- [ ] If count = 0:
  - Check `nids_alerts.log` has content
  - Check Logstash logs: `docker-compose logs logstash`
  - Verify file paths in `docker-compose.yml` volumes

### ✅ AI Engine → Elasticsearch

**Start AI Engine:**
```bash
cd ../src/ai/inference
python zmq_subscriber.py --model-dir ../../../models &

# Let it run for 1 minute
sleep 60
```

**Validation:**
- [ ] `ai_alerts.log` file exists
- [ ] No errors in AI engine output

**Check Elasticsearch ingestion:**
```bash
curl "http://localhost:9200/hybrid-ids-ai-alerts-*/_count?pretty"
```

**Validation:**
- [ ] Count > 0 (if anomalies detected)
- [ ] If no anomalies, that's OK - depends on traffic

### ✅ HIDS → Elasticsearch

**Start HIDS:**
```bash
cd ../hids
python hids_main.py --config config/hids_config.json &

# Let it run for 2 minutes (to complete one scan cycle)
sleep 120
```

**Validation:**
- [ ] `hids_alerts.log` file exists
- [ ] No errors in HIDS output

**Trigger file integrity alert:**
```bash
# Modify a monitored file
echo "# test alert" >> /path/to/monitored/file

# Wait for next scan cycle (60 seconds)
sleep 60
```

**Check Elasticsearch ingestion:**
```bash
curl "http://localhost:9200/hybrid-ids-hids-alerts-*/_count?pretty"
```

**Validation:**
- [ ] Count > 0 (HIDS alerts were ingested)
- [ ] Should see file integrity alert

---

## Phase 5: Dashboard Visualization

### ✅ Index Patterns

**Open Kibana:** http://localhost:5601

**Navigate to:** Stack Management > Index Patterns

**Create index patterns:**
1. [ ] Pattern: `hybrid-ids-nids-alerts-*`, Time field: `@timestamp`
2. [ ] Pattern: `hybrid-ids-ai-alerts-*`, Time field: `@timestamp`
3. [ ] Pattern: `hybrid-ids-hids-alerts-*`, Time field: `@timestamp`
4. [ ] Pattern: `hybrid-ids-network-features-*`, Time field: `@timestamp`

**Validation:**
- [ ] All patterns show document count > 0
- [ ] Field list shows expected fields (severity, src_ip, etc.)

### ✅ Import Dashboard

**Navigate to:** Stack Management > Saved Objects > Import

**Import file:** `elk/kibana/dashboards/unified-security-dashboard.ndjson`

**Validation:**
- [ ] Import succeeds
- [ ] No conflicts or errors
- [ ] Dashboard appears in Dashboard list

### ✅ View Dashboard

**Navigate to:** Dashboard > Hybrid IDS - Unified Security Dashboard

**Validation:**
- [ ] Dashboard loads without errors
- [ ] All 15 panels display (may show "No data" if insufficient data)
- [ ] Panels with data:
  - [ ] Total NIDS Alerts (metric)
  - [ ] AI Anomalies Detected (metric)
  - [ ] HIDS Alerts (metric)
  - [ ] Alert Timeline (area chart)
  - [ ] Threat Severity Distribution (pie chart)

### ✅ Test Queries

**Navigate to:** Discover

**Test queries:**

1. **All NIDS alerts:**
   ```kql
   _index:hybrid-ids-nids-alerts-*
   ```
   - [ ] Shows results

2. **High severity alerts:**
   ```kql
   severity:HIGH OR severity:CRITICAL
   ```
   - [ ] Shows only high/critical alerts

3. **HIDS file integrity alerts:**
   ```kql
   alert_type:file_integrity
   ```
   - [ ] Shows file integrity alerts

4. **AI anomalies with high confidence:**
   ```kql
   type:ANOMALY AND confidence >= 0.8
   ```
   - [ ] Shows high-confidence anomalies

---

## Phase 6: End-to-End Testing

### ✅ Generate Test Traffic

**Test 1: Port Scan (NIDS Detection)**
```bash
# Generate port scan
nmap -sS -p 1-1000 <target_ip>
```

**Validation:**
- [ ] NIDS detects port scan
- [ ] `nids_alerts.log` contains port scan alert
- [ ] Alert appears in Kibana within 1 minute
- [ ] Alert shows: `rule_id: 1001`, `message: "Port Scan Detected"`

**Test 2: SQL Injection Pattern (NIDS Detection)**
```bash
# Simulate SQL injection in HTTP traffic
curl "http://testserver.com/page?id=1' OR '1'='1"
```

**Validation:**
- [ ] NIDS detects SQL injection pattern
- [ ] Alert shows: `rule_id: 1002`, `severity: HIGH`

**Test 3: File Modification (HIDS Detection)**
```bash
# Modify system file
echo "# test" >> /etc/hosts  # Linux
echo "# test" >> C:\Windows\System32\drivers\etc\hosts  # Windows (as Admin)

# Wait for HIDS scan (60 seconds)
sleep 60
```

**Validation:**
- [ ] HIDS detects file modification
- [ ] Alert appears in `hids_alerts.log`
- [ ] Alert shows: `alert_type: file_integrity`, `severity: HIGH`
- [ ] Alert appears in Kibana dashboard

**Test 4: Suspicious Process (HIDS Detection)**
```bash
# Run netcat listener (suspicious)
nc -l 4444 &
```

**Validation:**
- [ ] HIDS detects suspicious process
- [ ] Alert shows: `alert_type: process_monitoring`
- [ ] Process name "nc" or "netcat" in alert

**Test 5: Anomalous Traffic (AI Detection)**
```bash
# Generate unusual traffic pattern (requires actual network activity)
# E.g., high packet rate, unusual ports, etc.
```

**Validation:**
- [ ] AI engine processes features
- [ ] If anomaly detected:
  - [ ] Alert in `ai_alerts.log`
  - [ ] Confidence score provided
  - [ ] Alert appears in Kibana

---

## Phase 7: Performance Validation

### ✅ NIDS Performance

**Run performance test:**
```bash
cd build
./nids -r ../test_data/large_traffic.pcap --stats
```

**Expected Performance:**
- [ ] Packet processing: 50,000-100,000 packets/sec
- [ ] No packet drops
- [ ] Memory usage < 500 MB
- [ ] CPU usage < 50% (single core)

### ✅ AI Engine Performance

**Check inference latency:**
```bash
grep "inference_time_ms" ../ai_alerts.log | tail -20
```

**Expected Performance:**
- [ ] Inference time < 5ms per flow
- [ ] No timeouts or errors
- [ ] Memory usage < 1 GB

### ✅ HIDS Performance

**Check scan performance:**
```bash
grep "Scan completed" ../hids_alerts.log | tail -10
```

**Expected Performance:**
- [ ] File scan: 1,000+ files/minute
- [ ] Process scan: 100+ processes/second
- [ ] No scan failures

### ✅ ELK Performance

**Check ingestion rate:**
```bash
curl "http://localhost:9200/_cat/indices?v&s=docs.count:desc"
```

**Expected Performance:**
- [ ] Document count growing
- [ ] Index size < 1 GB/day
- [ ] Query response < 200ms

---

## Phase 8: Documentation for Your Report

### ✅ Capture Evidence for Your Project

- [ ] Take screenshots of Kibana dashboard showing:
  - [ ] NIDS alerts
  - [ ] AI anomaly detections
  - [ ] HIDS file integrity alerts
  - [ ] Alert timeline visualization

- [ ] Document your test scenarios
  - [ ] What attacks did you simulate?
  - [ ] What was detected?
  - [ ] Any false positives?

- [ ] Save sample data for analysis
  ```bash
  # Create results folder
  mkdir project_results

  # Copy logs
  cp nids_alerts.log ai_alerts.log hids_alerts.log project_results/

  # Export sample alerts from Elasticsearch
  curl "http://localhost:9200/hybrid-ids-*/_search?size=50&pretty" > project_results/alerts.json
  ```

### ✅ Performance Observations (Optional)

- [ ] Note resource usage during testing
  - [ ] CPU usage
  - [ ] Memory consumption
  - [ ] Disk space used

- [ ] Record detection metrics
  - [ ] How many alerts generated?
  - [ ] Detection time/latency
  - [ ] Any missed detections?

---

## Phase 9: Documentation Verification

### ✅ Documentation Completeness

- [ ] README.md updated with HIDS information
- [ ] COMPLETE_INTEGRATION_GUIDE.md reviewed
- [ ] All component READMEs accurate
- [ ] Troubleshooting guides available

### ✅ Code Quality

- [ ] No critical bugs reported
- [ ] AI engine array bug fixed (verify with `test_ai_fix.py`)
- [ ] All scripts executable
- [ ] Configuration files valid

---

## Phase 10: Project Completion

### ✅ Minimum Working Demo (For Passing Grade)

**At least these components running:**
- [ ] NIDS engine analyzing traffic (can use PCAP files)
- [ ] HIDS monitoring files/processes
- [ ] Kibana dashboard accessible and showing some data

**Basic functionality demonstrated:**
- [ ] At least ONE type of attack detected (e.g., port scan or SQL injection)
- [ ] Alerts visible in log files
- [ ] Dashboard displays at least some visualizations

### ✅ Full Implementation (For Higher Grades)

**All processes working:**
- [ ] NIDS engine capturing live traffic
- [ ] AI engine performing anomaly detection
- [ ] HIDS monitoring host activity
- [ ] All three components sending data to Kibana
- [ ] Dashboard showing real-time updates

**Multiple test scenarios:**
- [ ] Tested at least 3 different attack types
- [ ] Documented detection accuracy
- [ ] Analyzed false positives/negatives
- [ ] Compared different detection methods

### ✅ Report Preparation

- [ ] Screenshots captured
- [ ] Test results documented
- [ ] Performance metrics noted (optional)
- [ ] Limitations and improvements discussed
- [ ] Code understanding demonstrated (be prepared to explain how it works!)

---

## Troubleshooting Quick Reference

### Common Issues

**Issue: No alerts in Elasticsearch**
- **Check:** Logstash logs: `docker-compose logs logstash`
- **Fix:** Verify file paths in `docker-compose.yml` volumes
- **Fix:** Check log file permissions

**Issue: NIDS "Permission denied"**
- **Fix:** Run with sudo or set capabilities
  ```bash
  sudo setcap cap_net_raw,cap_net_admin=eip ./nids
  ```

**Issue: AI Engine "Array dimension mismatch"**
- **Fix:** Verify fix applied in `anomaly_detector.py`
- **Test:** Run `python scripts/test_ai_fix.py`

**Issue: Elasticsearch "Out of memory"**
- **Fix:** Increase Docker memory limit (8 GB)
- **Fix:** Reduce Elasticsearch heap size in `docker-compose.yml`

**Issue: Kibana not loading dashboard**
- **Fix:** Clear browser cache
- **Fix:** Re-import dashboard NDJSON
- **Fix:** Recreate index patterns

---

## Completion Checklist

### All Phases Completed

- [ ] Phase 1: Build Verification ✓
- [ ] Phase 2: Component Testing ✓
- [ ] Phase 3: ELK Stack Deployment ✓
- [ ] Phase 4: Data Flow Integration ✓
- [ ] Phase 5: Dashboard Visualization ✓
- [ ] Phase 6: End-to-End Testing ✓
- [ ] Phase 7: Performance Validation ✓
- [ ] Phase 8: Security & Production Readiness ✓
- [ ] Phase 9: Documentation Verification ✓
- [ ] Phase 10: Final Acceptance ✓

### Student Sign-Off

- [ ] Core functionality working for demonstration
- [ ] Screenshots and evidence collected
- [ ] Understand the architecture and can explain it
- [ ] Report/presentation prepared

**Project Completed Date:** _________________

**Student Name:** _________________

**Tested Components:** ☐ NIDS  ☐ HIDS  ☐ AI Engine  ☐ ELK Dashboard

---

## After Your Project Submission

### Cleanup (Free up disk space)

```bash
# Stop all Docker containers
cd elk
docker-compose down

# Optional: Remove Docker volumes to free space
docker-compose down -v

# Optional: Remove Docker images
docker system prune -a
```

### If You Want to Continue Learning

1. **Try advanced features:**
   - Train ML models on different datasets
   - Create custom detection rules
   - Build additional Kibana visualizations

2. **Extend the project:**
   - Add new protocol parsers
   - Implement additional ML algorithms
   - Create a web interface for configuration

3. **Contribute back:**
   - Share your improvements on GitHub
   - Help other students with issues
   - Document interesting findings

**Great job completing your cybersecurity project!**

---

**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Department:** CSE - Cybersecurity
**Project:** Final Year B.Tech - Hybrid IDS
**Academic Year:** 2024-2025
**Document Version:** 1.0
**Last Updated:** October 2025
