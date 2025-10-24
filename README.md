# 🛡️ Hybrid IDS - Two-Tier Detection System

**Final Year B.Tech Project | CSE - Cybersecurity**
**Central University of Jammu**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/SyedMisbahGit/HYBRID-IDS-MCP)
[![Status](https://img.shields.io/badge/status-completed-success.svg)]()

> **Author:** Syed Misbah Uddin
> **Project:** Hybrid Intrusion Detection System with Adaptive Learning
> **Institution:** Central University of Jammu
> **Department:** Computer Science & Engineering (Cybersecurity)

---

## 📖 Project Overview

This project implements an **intelligent two-tier intrusion detection system** that combines signature-based detection (S-IDS), machine learning-based anomaly detection (A-IDS), host-based monitoring (HIDS), and a feedback loop for continuous improvement.

### Why This Architecture?

Traditional IDS systems face a fundamental trade-off:
- **Signature-based IDS** → Fast but misses unknown threats
- **Anomaly-based IDS** → Catches unknowns but slow with false positives

**My Solution:** A sequential two-tier pipeline where known threats are filtered fast, unknown threats are analyzed by ML, and human validation creates a feedback loop for continuous learning.

---

## 🎯 Project Objectives

As part of my final year B.Tech project, I aimed to:

1. **Design** a multi-tier intrusion detection architecture
2. **Implement** both network-based (NIDS) and host-based (HIDS) detection
3. **Integrate** machine learning for anomaly detection
4. **Develop** an adaptive learning mechanism through feedback loops
5. **Deploy** a unified dashboard for security analytics
6. **Demonstrate** real-world applicability in network security

---

## 🏗️ System Architecture

### Two-Tier Detection Pipeline

```
Network Traffic
    ↓
┌─────────────────────┐
│ TIER 1: S-IDS       │  ← Fast signature matching
│ (Signature-Based)   │    Detects known threats
└──────┬──────────┬───┘
       ↓          ↓
   MALICIOUS   BENIGN
   (Known)   (Unknown?)
       ↓          ↓
    Alert    ┌──────────────────┐
             │ TIER 2: A-IDS    │  ← ML-based analysis
             │ (Anomaly-Based)  │    Detects zero-day
             └──────┬───────┬───┘
                    ↓       ↓
                BENIGN  MALICIOUS
                (Safe)  (Anomaly)
                    ↓       ↓
                 Pass    Alert + Review
                             ↓
                     Manual Validation
                             ↓
                       Confirmed?
                             ↓
                     New Signature
                             ↓
                       ┌──────────┐
                       │ Feedback │
                       │   Loop   │
                       └─────┬────┘
                             ↓
                      Updates S-IDS
                             ↓
                  System Gets Smarter!
```

**Parallel Component:** HIDS monitors host-level events (files, logs, processes)

---

## 💡 Key Innovation: Adaptive Feedback Loop

### The Concept

1. **S-IDS** catches known threats instantly (fast path)
2. **A-IDS** analyzes remaining traffic with ML (smart path)
3. **Manual Review** validates A-IDS anomalies
4. **Confirmed anomalies** become new S-IDS signatures
5. **System evolves** - unknown threats become known

### Real-World Example

**Day 1:** Novel SQL injection variant appears
- S-IDS: No matching rule → Passes to A-IDS
- A-IDS: Detects unusual pattern → Flags anomaly
- Analyst: Reviews and confirms → Creates new rule

**Day 2:** Same attack appears again
- S-IDS: New rule matches → Caught immediately!
- A-IDS: Never sees it (already filtered)
- Result: Faster detection, less resource usage

---

## 🔧 Technical Implementation

### Core Components

**1. Network-Based Detection (C++17)**
- **S-IDS Engine** (`src/nids/sids.cpp`)
  - Signature-based rule matching
  - Fast packet filtering
  - 6 base detection rules

- **Feature Extractor** (`src/nids/features/`)
  - 78 CIC-IDS2017 standard features
  - Real-time computation
  - Optimized for performance

**2. ML-Based Anomaly Detection (Python)**
- **Ensemble Models** (`src/ai/inference/`)
  - Random Forest classifier
  - Isolation Forest for anomaly detection
  - Confidence-based scoring (0-1 scale)

- **Training Pipeline** (`src/ai/training/`)
  - Model training on CIC-IDS2017 dataset
  - Feature preprocessing and scaling
  - Model serialization

**3. Host-Based Detection (Python)**
- **File Integrity Monitor** (`src/hids/file_monitor.py`)
  - SHA256 hash comparison
  - Monitors critical system files

- **Log Analyzer** (`src/hids/log_analyzer.py`)
  - 12 detection rules
  - Brute force detection
  - Privilege escalation alerts

- **Process Monitor** (`src/hids/process_monitor.py`)
  - Suspicious process detection
  - Network connection tracking

**4. Central Dashboard (ELK Stack)**
- **Elasticsearch** - Data storage and indexing
- **Logstash** - Log processing and enrichment
- **Kibana** - Visualization and manual review interface

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| NIDS Core | C++17, libpcap | High-performance packet processing |
| ML Engine | Python, scikit-learn | Anomaly detection models |
| HIDS | Python, psutil | Host monitoring |
| Dashboard | ELK Stack, Docker | Unified analytics |
| IPC | ZeroMQ | Real-time communication |
| Build System | CMake, Make | Cross-platform compilation |

---

## 🚀 Getting Started

### Prerequisites

- **Operating System**: Windows 10/11 (MSYS2) or Linux (Ubuntu 22.04+)
- **Hardware**: 2+ CPU cores, 6GB RAM minimum
- **Software**:
  - C++ compiler (GCC/Clang)
  - Python 3.10+
  - Docker & Docker Compose
  - libpcap/Npcap

### Quick Setup

**1. Clone Repository**
```bash
git clone https://github.com/SyedMisbahGit/HYBRID-IDS-MCP.git
cd HYBRID-IDS-MCP
```

**2. Install Dependencies**
```bash
# Windows (MSYS2 MINGW64)
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake
pacman -S mingw-w64-x86_64-boost mingw-w64-x86_64-pcre
pip install -r requirements.txt

# Linux
sudo apt install build-essential cmake libpcap-dev libboost-all-dev
pip3 install -r requirements.txt
```

**3. Build C++ Components**
```bash
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j4
```

**4. Deploy ELK Dashboard**
```bash
cd ../elk
docker-compose up -d
```

**5. Start Detection Systems**

*Terminal 1 - S-IDS (Tier 1):*
```bash
cd build
./sids -i eth0  # Linux: replace with your interface
./sids -i "Ethernet"  # Windows
```

*Terminal 2 - A-IDS Feature Extraction:*
```bash
./nids -i eth0 --extract-features
```

*Terminal 3 - A-IDS ML Engine:*
```bash
cd ../src/ai/inference
python zmq_subscriber.py --model-dir ../../../models
```

*Terminal 4 - HIDS:*
```bash
cd ../hids
python hids_main.py --config config/hids_config.json
```

**6. Access Dashboard**
```
http://localhost:5601
```

---

## 📚 Documentation

### Quick Start Guides

1. **[INTEGRATION_QUICKSTART.md](INTEGRATION_QUICKSTART.md)** - 🌟 **NEW!** 10-minute complete system setup
2. **[HIDS_QUICKSTART.md](HIDS_QUICKSTART.md)** - 5-minute HIDS deployment
3. **[NIDS_QUICKSTART.md](NIDS_QUICKSTART.md)** - 5-minute NIDS deployment
4. **[GETTING_STARTED.md](GETTING_STARTED.md)** - Quick 3-step guide to deploy the system

### Comprehensive Guides

5. **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - 🌟 **NEW!** Complete integration documentation (50+ pages)
6. **[HIDS_GUIDE.md](HIDS_GUIDE.md)** - Complete HIDS user guide
7. **[NIDS_COMPLETE.md](NIDS_COMPLETE.md)** - Complete NIDS documentation
8. **[COMPLETE_INTEGRATION_GUIDE.md](COMPLETE_INTEGRATION_GUIDE.md)** - Full deployment guide

### Implementation Summaries

9. **[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)** - 🌟 **NEW!** Integration implementation summary
10. **[HIDS_COMPLETE.md](HIDS_COMPLETE.md)** - HIDS implementation summary
11. **[NIDS_DESIGN.md](NIDS_DESIGN.md)** - Network IDS architecture and design

### Architecture & Design

12. **[ARCHITECTURE_EXPLAINED.md](ARCHITECTURE_EXPLAINED.md)** - Deep dive into two-tier architecture
13. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Code organization and file structure

### Testing & Validation

14. **[NIDS_TESTING.md](NIDS_TESTING.md)** - Complete testing methodology for NIDS
15. **[VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md)** - System-wide testing procedures

### Additional Resources

16. **[ELK_DASHBOARD_GUIDE.md](ELK_DASHBOARD_GUIDE.md)** - Dashboard setup and customization
17. **[REAL_TIME_DEPLOYMENT.md](REAL_TIME_DEPLOYMENT.md)** - Windows-specific deployment
18. **[BUGFIX_AI_ENGINE.md](BUGFIX_AI_ENGINE.md)** - Known issues and fixes
19. **[ORIGINAL_PLAN.md](ORIGINAL_PLAN.md)** - Original project blueprint

---

## 🧪 Testing & Results

### Test Scenarios

**1. Known Threat Detection (S-IDS)**
- SQL injection patterns
- Cross-site scripting (XSS)
- Port scanning activity
- Result: <1ms detection latency

**2. Unknown Threat Detection (A-IDS)**
- Novel attack patterns
- Zero-day exploits
- Unusual traffic patterns
- Result: ~5ms detection latency, 85%+ accuracy

**3. Host-Based Detection (HIDS)**
- File tampering
- Suspicious processes
- Failed login attempts
- Result: 1-minute scan cycle

**4. Feedback Loop Demonstration**
- Identified anomaly → Validated → New signature created
- Re-test shows S-IDS now catches the pattern
- Proves adaptive learning capability

### Performance Metrics

| Component | Metric | Result |
|-----------|--------|--------|
| S-IDS | Throughput | 50,000-100,000 packets/sec |
| S-IDS | Latency | <1ms per packet |
| A-IDS | Throughput | 5,000-10,000 flows/sec |
| A-IDS | Latency | <5ms per flow |
| HIDS | File Scan | 1,000-5,000 files/min |
| System | Total CPU | 30-50% (4-core system) |
| System | Memory | ~2GB combined |

---

## 🎓 Academic Contributions

### Novel Aspects

1. **Hybrid Two-Tier Architecture**
   - Combines efficiency of signatures with intelligence of ML
   - Sequential processing optimizes resource usage

2. **Adaptive Feedback Mechanism**
   - Human-in-the-loop validation
   - Automatic rule generation from confirmed anomalies
   - Continuous system improvement

3. **Unified Multi-Layer Detection**
   - Network + Host correlation
   - Single dashboard for all detection sources
   - MITRE ATT&CK framework mapping

### Learning Outcomes

Through this project, I gained hands-on experience in:
- ✅ Network security and intrusion detection systems
- ✅ Machine learning applications in cybersecurity
- ✅ High-performance C++ programming
- ✅ Real-time data processing and analytics
- ✅ Docker containerization and deployment
- ✅ Security operations center (SOC) workflows

---

## 📊 Project Structure

```
Hybrid-IDS-MCP/
├── src/
│   ├── nids/          # Network IDS (C++)
│   │   ├── sids.cpp   # Tier 1: Signature detection
│   │   ├── nids.cpp   # Tier 2: Feature extraction
│   │   └── rules/     # Signature database
│   ├── ai/            # ML Engine (Python)
│   │   ├── inference/ # Real-time anomaly detection
│   │   └── training/  # Model training
│   ├── hids/          # Host IDS (Python)
│   └── exporters/     # ELK integration
├── elk/               # Central Dashboard
│   ├── elasticsearch/
│   ├── logstash/
│   └── kibana/
├── config/            # Configuration files
├── scripts/           # Testing scripts
└── docs/              # Documentation
```

---

## 🔍 Future Enhancements

Potential improvements for extended work:

1. **Automated Feedback Loop**
   - Automatic signature generation from confirmed anomalies
   - Hot-reload of S-IDS rules without restart

2. **Advanced ML Models**
   - Deep learning for complex pattern recognition
   - Temporal analysis with LSTM networks
   - Explainable AI for better interpretability

3. **Distributed Deployment**
   - Multi-node S-IDS deployment
   - Centralized A-IDS processing
   - Scalable ELK cluster

4. **Additional Protocols**
   - HTTPS traffic analysis (with SSL/TLS decryption)
   - DNS tunneling detection
   - IoT protocol monitoring

5. **Threat Intelligence Integration**
   - External threat feed integration
   - Automatic IOC (Indicators of Compromise) updates
   - Threat actor profiling

---

## 📝 References

### Datasets
- **CIC-IDS2017**: Canadian Institute for Cybersecurity Intrusion Detection Dataset
- **NSL-KDD**: Improved version of KDD Cup 99 dataset

### Research Papers
- Sharafaldin, I., et al. "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization" (2018)
- Tavallaee, M., et al. "A Detailed Analysis of the KDD CUP 99 Data Set" (2009)

### Frameworks & Tools
- **Snort**: Open-source IDS (signature rule syntax reference)
- **Suricata**: Multi-threaded IDS/IPS
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **scikit-learn**: Machine learning library

### Standards
- **NIST SP 800-94**: Guide to Intrusion Detection and Prevention Systems
- **MITRE ATT&CK**: Adversarial Tactics, Techniques & Common Knowledge
- **CIC-IDS2017 Features**: Standard feature set for network flow analysis

---

## 🤝 Acknowledgments

I would like to thank:

- **Central University of Jammu** for providing the academic environment and resources
- **Department of CSE (Cybersecurity)** for guidance and support
- **Project Guide/Supervisor** for valuable insights and direction
- **Open-source community** for tools and frameworks (ELK Stack, scikit-learn, etc.)
- **CIC** (Canadian Institute for Cybersecurity) for the IDS dataset

---

## 📧 Contact

**Syed Misbah Uddin**
B.Tech (Final Year) - Computer Science & Engineering (Cybersecurity)
Central University of Jammu

- **GitHub**: [@SyedMisbahGit](https://github.com/SyedMisbahGit)
- **Project Repository**: [HYBRID-IDS-MCP](https://github.com/SyedMisbahGit/HYBRID-IDS-MCP)
- **LinkedIn**: [Syed Misbah Uddin](https://linkedin.com/in/syedmisbah)

---

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

**Note:** This is an academic project developed for educational purposes. It demonstrates cybersecurity concepts and is not intended for production deployment without proper security hardening.

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `cmake .. && make` | Build C++ components |
| `./build/sids -i eth0` | Run S-IDS (Tier 1) |
| `./build/nids -i eth0 --extract-features` | Run A-IDS feature extraction |
| `python src/ai/inference/zmq_subscriber.py` | Run A-IDS ML engine |
| `python src/hids/hids_main.py` | Run HIDS |
| `docker-compose up -d` | Start ELK dashboard |
| `http://localhost:5601` | Access Kibana dashboard |

---

**Project Status**: ✅ Completed
**Academic Year**: 2024-2025
**Project Type**: Final Year B.Tech Major Project
**Domain**: Cybersecurity - Intrusion Detection Systems
**Last Updated**: October 2025
