# Hybrid IDS - Codebase Context

**Generated**: November 7, 2025  
**Author**: Syed Misbah Uddin | Central University of Jammu  
**Project**: Final Year B.Tech - Hybrid Intrusion Detection System  
**Status**: ✅ 100% Complete

---

## 🎯 Project Overview

A **production-ready Hybrid Intrusion Detection System** combining:
- **NIDS** (Network-based IDS) - Monitors network traffic
- **HIDS** (Host-based IDS) - Monitors host system
- **ML Engine** - Anomaly detection with trained models
- **Integration Layer** - Unified alert management
- **ELK Stack** - Centralized visualization

### Two-Tier Detection Architecture
```
Traffic → Tier 1 (S-IDS) → Known threats caught fast
              ↓
         Unknown traffic
              ↓
       Tier 2 (A-IDS) → ML anomaly detection
              ↓
       Manual validation → New signatures → Feedback loop
```

---

## 📁 Key Directories

```
src/
├── nids/                  # C++ Network IDS (high-performance)
├── nids_python/           # Python Network IDS (portable)
├── hids/                  # Host IDS (file, process, log monitoring)
├── ai/                    # ML engine (trained models)
└── integration/           # Unified alert manager, correlator

elk/                       # ELK Stack (Elasticsearch, Logstash, Kibana)
models/                    # Trained ML models (✅ ready)
config/                    # Configuration files
scripts/                   # Utility scripts
```

---

## 🏗️ Architecture

### Four Layers
1. **Data Sources**: Network traffic, host activity
2. **Detection**: NIDS (C++/Python), HIDS (Python)
3. **Integration**: Alert manager, event correlator
4. **Visualization**: Kibana dashboards

### Communication (ZeroMQ)
```
NIDS (5556) ──┐
              ├──> Alert Manager ──> Correlator ──> ELK
HIDS (5557) ──┘
```

---

## 🔧 Core Components

### 1. NIDS (Network IDS)
**C++ Implementation** (`src/nids/`):
- `sids_main.cpp` - Tier 1: Signature detection
- `nids_main.cpp` - Tier 2: Feature extraction
- Performance: 50-100K pps, <1ms latency

**Python Implementation** (`src/nids_python/`):
- `nids_main.py` - Main application
- `packet_capture.py` - Scapy-based capture
- `signature_ids.py` - 10+ detection rules
- `feature_extractor.py` - 78 CIC-IDS2017 features
- Performance: 5-10K pps, ~5ms latency

### 2. HIDS (Host IDS)
**Location**: `src/hids/`
- `hids_main.py` - Main orchestrator
- `file_monitor.py` - SHA256 integrity checking
- `process_monitor.py` - Process baseline & monitoring
- `log_analyzer.py` - Windows Event Log analysis (12 rules)
- Performance: <5% CPU, 50-100 MB RAM

### 3. ML Engine (A-IDS)
**Location**: `src/ai/`
- **Models** (all trained ✅):
  - `models/random_forest_model.pkl` - Multi-class classifier
  - `models/isolation_forest_model.pkl` - Anomaly detector
  - `models/scaler.pkl` - Feature normalizer
- **Inference**: `inference/anomaly_detector.py`
- **Training**: `training/train_models.py`

### 4. Integration Layer
**Location**: `src/integration/`
- `integration_controller.py` - Master orchestrator
- `unified_alert_manager.py` - Multi-source alert normalization
- `event_correlator.py` - Multi-stage attack detection (10 rules)
- `hybrid_ids.py` - Unified interface

### 5. ELK Stack
**Location**: `elk/`
- `docker-compose.yml` - Docker deployment
- `elasticsearch/` - Alert storage (port 9200)
- `logstash/pipeline/` - Log processing pipelines
- `kibana/dashboards/` - Visualization dashboards (port 5601)

---

## 🚀 Running the System

### Quick Test
```powershell
python test_hids.py  # Test HIDS (4/4 tests)
python test_nids.py  # Test NIDS (4/4 tests)
```

### Individual Components
```powershell
# HIDS
python src\hids\hids_main.py --config config\hids\hids_config.yaml

# NIDS (Python)
python src\nids_python\nids_main.py -r test.pcap

# ML Engine
python src\ai\inference\zmq_subscriber.py --model-dir models
```

### Complete System
```powershell
# Option 1: Master launcher
run_complete_system.bat

# Option 2: Integration controller
python src\integration\integration_controller.py

# Option 3: With ELK
cd elk && docker-compose up -d
python src\integration\integration_controller.py
start http://localhost:5601
```

---

## 📊 Detection Capabilities

### NIDS (10+ Rules)
- Port scanning, SSH brute force, SQL injection
- ICMP flood, DNS tunneling, suspicious ports
- FTP/Telnet/RDP access, SMB access

### HIDS (12+ Rules)
- File tampering, suspicious processes, new processes
- High resource usage, unusual connections
- Failed logins, privilege escalation, system changes

### ML (A-IDS)
- Zero-day attacks, behavioral anomalies
- Advanced persistent threats, polymorphic malware
- Encrypted threats, insider threats, data exfiltration

---

## 🔑 Key Files

### Configuration
- `config/hids/hids_config.yaml` - HIDS settings
- `config/nids.yaml.example` - NIDS template
- `config/hybrid_ids_config.yaml` - Master config

### Build & Deploy
- `CMakeLists.txt` - C++ build configuration
- `requirements.txt` - Python dependencies
- `elk/docker-compose.yml` - ELK deployment

### Testing
- `test_hids.py` - HIDS test suite
- `test_nids.py` - NIDS test suite
- `scripts/test_ai_fix.py` - ML engine tests

### Launchers
- `run_complete_system.bat` - Master launcher
- `run_hids.bat` - HIDS launcher
- `run_nids.bat` - NIDS launcher

---

## 🔍 Code Patterns

### ZeroMQ Communication
```python
# Publisher (NIDS/HIDS)
context = zmq.Context()
publisher = context.socket(zmq.PUB)
publisher.bind("tcp://*:5556")
publisher.send_json(alert)

# Subscriber (Alert Manager)
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://localhost:5556")
subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
alert = subscriber.recv_json()
```

### Alert Schema
```json
{
  "alert_id": "nids_signature_1698765432000000",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "source": "nids_signature|nids_anomaly|hids_file|hids_process|hids_log",
  "severity": "INFO|LOW|MEDIUM|HIGH|CRITICAL",
  "title": "Attack Name",
  "description": "Details",
  "metadata": {"rule_id": 1001, "confidence": 0.95}
}
```

---

## 📚 Documentation (35+ Files)

### Essential Docs
- `README.md` - Main overview
- `ARCHITECTURE.md` - System architecture (549 lines)
- `PROJECT_STRUCTURE.md` - File organization
- `100_PERCENT_COMPLETE.md` - Completion status
- `FINAL_PROJECT_SUMMARY.md` - Project summary

### Quick Start
- `WINDOWS_QUICKSTART.md` - 5-minute setup
- `INTEGRATION_QUICKSTART.md` - 10-minute integration
- `GETTING_STARTED.md` - 3-step deployment

### Component Guides
- `NIDS_COMPLETE.md` - NIDS documentation
- `HIDS_GUIDE.md` - HIDS user guide
- `INTEGRATION_GUIDE.md` - Integration docs (50+ pages)

### Build & Deploy
- `BUILD_CPP_NIDS_WINDOWS.md` - C++ build guide
- `DEPLOY_ELK_STACK.md` - ELK deployment
- `COMPLETE_SETUP_GUIDE.md` - Complete setup

### Testing
- `NIDS_TESTING.md` - NIDS testing methodology
- `VALIDATION_CHECKLIST.md` - Testing procedures

---

## 🛠️ Technology Stack

**Languages**: C++17, Python 3.10+  
**Build**: CMake, Docker  
**Networking**: libpcap, Scapy, ZeroMQ  
**ML**: scikit-learn, PyTorch, TensorFlow  
**System**: psutil, watchdog, pywin32  
**ELK**: Elasticsearch, Logstash, Kibana  
**Data**: NumPy, Pandas, SciPy

---

## 📈 Performance Metrics

| Component | Throughput | Latency | CPU | Memory |
|-----------|-----------|---------|-----|--------|
| NIDS (C++) | 50-100K pps | <1ms | 20-40% | 20-50 MB |
| NIDS (Python) | 5-10K pps | ~5ms | 10-30% | 50-200 MB |
| HIDS | 5K files/min | ~30s | <5% | 50-100 MB |
| ML Engine | 10K flows/s | <5ms | 15-25% | 100-300 MB |
| Alert Manager | 1K alerts/s | <10ms | 5-10% | 50-100 MB |

---

## 🐛 Common Issues

1. **ZeroMQ port in use**: Change port or kill process
2. **Permission denied**: Run as Administrator
3. **Models not found**: Train with `train_models.py`
4. **Elasticsearch failed**: Start ELK with `docker-compose up -d`
5. **C++ build fails**: See `BUILD_CPP_NIDS_WINDOWS.md`

---

## 🎓 Academic Context

**Type**: Final Year B.Tech Major Project  
**Domain**: Cybersecurity - Intrusion Detection Systems  
**Institution**: Central University of Jammu  
**Department**: CSE (Cybersecurity)  
**Year**: 2024-2025

### Key Achievements
1. ✅ Complete two-tier detection (S-IDS + A-IDS)
2. ✅ Network + Host monitoring
3. ✅ Trained ML models (RF + Isolation Forest)
4. ✅ Unified integration layer
5. ✅ Production-ready ELK dashboard
6. ✅ Comprehensive testing (8/8 passed)
7. ✅ Extensive documentation (100+ pages)

---

## 📞 Quick Reference

```powershell
# Test everything
python test_hids.py && python test_nids.py

# Run complete system
run_complete_system.bat

# Train ML models
python src\ai\training\train_models.py --output-dir models

# Build C++ NIDS
mkdir build && cd build
cmake .. && cmake --build . --config Release

# Deploy ELK
cd elk && docker-compose up -d

# Access dashboard
start http://localhost:5601
```

---

**Last Updated**: November 7, 2025  
**Version**: 1.0.0 FINAL  
**Status**: ✅ 100% Complete and Operational
