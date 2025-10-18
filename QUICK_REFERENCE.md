# 🚀 Hybrid IDS - Quick Reference Card

**Version:** 1.0.0 | **Date:** 2025-10-18

---

## ⚡ Quick Commands

### **Build System**

```bash
# Build everything
cmake .. && make

# Build S-IDS only
make sids

# Build Complete NIDS
make nids

# Direct compilation (no CMake)
g++ -std=c++17 -O3 src/nids/**/*.cpp src/nids/sids_main.cpp -o sids -lpcap -lpthread
```

### **Generate Test Traffic**

```bash
python scripts/generate_test_traffic.py test.pcap
```

### **Run S-IDS (Signature Detection Only)**

```bash
# From PCAP file
./sids -r test.pcap

# Live capture (requires sudo)
sudo ./sids -i eth0
```

### **Run Complete NIDS (All Features)**

```bash
# Basic usage
./nids -r test.pcap

# With feature extraction
./nids -r test.pcap --extract-features --export-csv features.csv

# With AI integration
./nids -r test.pcap --zmq tcp://*:5555 --extract-features

# Live capture with all features
sudo ./nids -i eth0 --extract-features --zmq tcp://*:5555
```

### **Run AI Engine**

```bash
# Standalone test
python src/ai/inference/anomaly_detector.py

# Simulation mode (no NIDS connection)
python src/ai/inference/zmq_subscriber.py --simulate

# Connect to NIDS
python src/ai/inference/zmq_subscriber.py --endpoint tcp://localhost:5555
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `README.md` | Main documentation |
| `FINAL_PROJECT_SUMMARY.md` | Complete project overview |
| `COMPLETE_BUILD_GUIDE.md` | Detailed build instructions |
| `QUICKSTART.md` | 5-minute quick start |
| `MCP_MASTER_PLAN.md` | Technical blueprint |

---

## 🔧 Command-Line Options

### **S-IDS**

```
./sids [options]
  -i <interface>    Live capture
  -r <file>         PCAP file
  -h, --help        Help
```

### **Complete NIDS**

```
./nids [options]
  -i <interface>      Live capture
  -r <file>           PCAP file
  --extract-features  Enable feature extraction
  --export-csv <file> Export features to CSV
  --no-signatures     Disable signatures
  --no-connections    Disable tracking
  --no-protocols      Disable decoding
  --zmq <endpoint>    Enable ZMQ (e.g., tcp://*:5555)
  -h, --help          Help
```

### **AI Engine**

```
python src/ai/inference/zmq_subscriber.py [options]
  --endpoint <addr>   ZMQ endpoint (default: tcp://localhost:5555)
  --topic <name>      Topic (default: features)
  --simulate          Simulation mode
```

---

## 📊 Output Files

| File | Description |
|------|-------------|
| `nids_alerts.log` | JSON alerts from signatures |
| `ai_alerts.log` | JSON alerts from AI |
| `features.csv` | Extracted ML features (78 columns) |

---

## 🎯 Common Use Cases

### **1. Test Signature Detection**

```bash
python scripts/generate_test_traffic.py attacks.pcap
./sids -r attacks.pcap
# Check: nids_alerts.log
```

### **2. Extract Features for ML Training**

```bash
./nids -r dataset.pcap --export-csv training_features.csv
# Result: CSV with 78 features per flow
```

### **3. Real-Time AI Detection**

Terminal 1:
```bash
python src/ai/inference/zmq_subscriber.py
```

Terminal 2:
```bash
./nids -r traffic.pcap --zmq tcp://*:5555
```

### **4. Live Network Monitoring**

```bash
sudo ./nids -i eth0 --extract-features --zmq tcp://*:5555
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `pcap_open_live failed` | Use `sudo` or run as Administrator |
| `cmake: command not found` | Use direct `g++` compilation |
| No packets captured | Check interface name, use `ip link` |
| ZMQ not receiving | Start AI engine first, check firewall |
| Module not found | Activate venv: `source venv/bin/activate` |

---

## 📈 Performance Targets

| Metric | S-IDS | Complete NIDS | AI Engine |
|--------|-------|---------------|-----------|
| Throughput | 500+ Mbps | 400+ Mbps | - |
| Packet Rate | 50k+ pkt/s | 40k+ pkt/s | - |
| Latency | <1ms | <5ms | <5ms |
| Memory | <50MB | <200MB | <500MB |

---

## 🏗️ System Architecture (Simplified)

```
Network Traffic
       ↓
  [NIDS Engine]
   • Parse packets
   • Track flows
   • Extract features
   • Match signatures
       ↓
    ┌──┴──┐
    ↓     ↓
[Alerts] [ZMQ]
           ↓
      [AI Engine]
       • Detect anomalies
       • Generate alerts
```

---

## 📚 Documentation

- **User Guide:** [README.md](README.md)
- **Build Guide:** [COMPLETE_BUILD_GUIDE.md](COMPLETE_BUILD_GUIDE.md)
- **Full Summary:** [FINAL_PROJECT_SUMMARY.md](FINAL_PROJECT_SUMMARY.md)
- **Architecture:** [docs/architecture/SYSTEM_ARCHITECTURE.md](docs/architecture/SYSTEM_ARCHITECTURE.md)

---

## 🔍 Example Outputs

### **S-IDS Alert**

```
[2025-10-18 14:32:10] [HIGH] SQL Injection Attempt (Rule ID: 1002)
  10.0.0.50:52342 -> 192.168.1.10:80 [TCP]
  Possible SQL injection in HTTP request
  Matched: or 1=1
```

### **Feature CSV**

```csv
duration,total_fwd_packets,total_bwd_packets,total_fwd_bytes,...
1.523,10,8,4500,3200,1500,64,890,245,...
```

### **AI Alert JSON**

```json
{
  "timestamp": "2025-10-18 14:32:11",
  "flow_id": 42,
  "type": "ANOMALY",
  "confidence": 0.873,
  "details": {
    "ensemble_score": 0.873,
    "inference_time_ms": 3.21
  }
}
```

---

## 🎓 Key Features

- ✅ 6 Signature detection rules
- ✅ 78 ML features (industry-standard)
- ✅ 6 Supported protocols (Ethernet, IP, TCP, UDP, HTTP, DNS)
- ✅ Stateful connection tracking
- ✅ Real-time AI anomaly detection
- ✅ Multi-platform (Linux, Windows, macOS)

---

## 📦 Project Stats

- **Total Files:** 40+
- **Total Code:** 15,000+ lines
- **C++ Code:** 3,850+ lines
- **Python Code:** 520+ lines
- **Documentation:** 10,000+ lines

---

## ✅ Quick Health Check

```bash
# 1. Build system works?
make sids && echo "✅ Build OK"

# 2. Can generate traffic?
python scripts/generate_test_traffic.py test.pcap && echo "✅ Traffic OK"

# 3. S-IDS runs?
./sids -r test.pcap && echo "✅ S-IDS OK"

# 4. Features extract?
./nids -r test.pcap --export-csv test.csv && wc -l test.csv

# 5. AI works?
python src/ai/inference/anomaly_detector.py && echo "✅ AI OK"
```

---

## 🚀 Next Steps

1. **Build:** `cmake .. && make`
2. **Test:** `./sids -r test.pcap`
3. **Deploy:** See [COMPLETE_BUILD_GUIDE.md](COMPLETE_BUILD_GUIDE.md)
4. **Customize:** Train your own ML models
5. **Integrate:** Connect to SIEM/dashboard

---

**Status:** ✅ Production-Ready
**Version:** 1.0.0
**License:** MIT

**Get Started:** `make sids && ./sids -r test.pcap` 🎯
