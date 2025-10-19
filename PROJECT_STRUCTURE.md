# Hybrid IDS - Project Structure

**Final Year B.Tech Project**
**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Department:** CSE - Cybersecurity

---

## Overview
This document maps my project structure to the two-tier detection architecture implemented in this Hybrid IDS system.

---

## Directory Structure

```
Hybrid-IDS-MCP/
│
├── 📄 Documentation (Root Level)
│   ├── README.md                      ⭐ Main entry point
│   ├── ARCHITECTURE_EXPLAINED.md      🌟 Two-tier architecture details
│   ├── COMPLETE_INTEGRATION_GUIDE.md  📚 Full setup guide
│   ├── VALIDATION_CHECKLIST.md        ✅ Testing checklist
│   ├── ELK_DASHBOARD_GUIDE.md         📊 Dashboard setup
│   ├── REAL_TIME_DEPLOYMENT.md        🪟 Windows deployment
│   ├── BUGFIX_AI_ENGINE.md            🐛 Known fixes
│   └── ORIGINAL_PLAN.md               📋 Original blueprint
│
├── 🔧 Source Code (src/)
│   │
│   ├── nids/                          🌐 Network-based IDS (C++)
│   │   ├── sids.cpp                   ⚡ TIER 1: Signature IDS
│   │   ├── nids.cpp                   🧠 TIER 2: Feature extractor
│   │   ├── capture/                   📡 Packet capture engine
│   │   ├── parser/                    🔍 Protocol parsers
│   │   ├── rules/                     📜 Signature database
│   │   ├── features/                  📊 78-feature extraction
│   │   ├── ipc/                       🔌 ZeroMQ communication
│   │   └── common/                    🛠️ Shared utilities
│   │
│   ├── ai/                            🤖 A-IDS ML Engine (Python)
│   │   ├── inference/                 ⚙️ Real-time detection
│   │   │   ├── anomaly_detector.py    🎯 TIER 2: ML models
│   │   │   └── zmq_subscriber.py      📨 Feature receiver
│   │   ├── training/                  🎓 Model training
│   │   │   └── train_models.py        📈 RF + Isolation Forest
│   │   └── models/                    💾 Saved models
│   │       ├── random_forest_model.pkl
│   │       ├── isolation_forest_model.pkl
│   │       └── scaler.pkl
│   │
│   ├── hids/                          🏠 Host-based IDS (Python)
│   │   ├── hids_main.py               🎮 Main orchestrator
│   │   ├── file_monitor.py            📁 File integrity monitoring
│   │   ├── log_analyzer.py            📝 Log analysis (12 rules)
│   │   ├── process_monitor.py         ⚙️ Process monitoring
│   │   └── config/                    ⚙️ Configuration
│   │       └── hids_config.json
│   │
│   └── exporters/                     📤 ELK integration
│       └── elasticsearch_exporter.py  📊 Alert export
│
├── 📊 Central Dashboard (elk/)
│   ├── docker-compose.yml             🐳 ELK Stack deployment
│   ├── elasticsearch/                 💾 Data storage
│   │   └── config/
│   ├── logstash/                      🔧 Log processing
│   │   ├── config/
│   │   └── pipeline/
│   │       ├── nids-alerts.conf       ⚡ S-IDS alerts
│   │       ├── ai-alerts.conf         🧠 A-IDS alerts
│   │       ├── hids-alerts.conf       🏠 HIDS alerts
│   │       └── features.conf          📊 Network features
│   └── kibana/                        📈 Visualization
│       └── dashboards/
│           └── unified-security-dashboard.ndjson
│
├── ⚙️ Configuration (config/)
│   ├── nids.yaml                      🌐 NIDS configuration
│   └── ai_engine.yaml                 🤖 AI engine configuration
│
├── 📜 Scripts (scripts/)
│   ├── test_ai_fix.py                 🧪 AI engine tests
│   └── test_real_time.ps1             🪟 Windows testing
│
├── 🧪 Tests (tests/)
│   └── test.pcap                      📦 Sample packet capture
│
├── 📚 Additional Docs (docs/)
│   ├── architecture/                  🏗️ Architecture details
│   ├── nids/                          🌐 NIDS documentation
│   └── ai/                            🤖 AI/ML documentation
│
└── 🔨 Build System
    ├── CMakeLists.txt                 🏗️ C++ build configuration
    ├── Makefile                       🔧 Build shortcuts
    └── build/                         📦 Compiled binaries
        ├── sids                       ⚡ TIER 1 executable
        ├── nids                       🧠 TIER 2 executable
        └── feature_extractor          📊 Feature tool
```

---

## Architecture Mapping

### Two-Tier Pipeline

**TIER 1: Signature-Based Detection (S-IDS)**
- **Code**: `src/nids/sids.cpp`
- **Executable**: `build/sids`
- **Rules**: `src/nids/rules/`
- **Log Output**: `nids_alerts.log`
- **Dashboard Index**: `hybrid-ids-nids-alerts-*`

**TIER 2: Anomaly-Based Detection (A-IDS)**
- **Feature Extraction**: `src/nids/features/` (C++)
- **Executable**: `build/nids`
- **ML Engine**: `src/ai/inference/anomaly_detector.py` (Python)
- **Models**: `src/ai/models/*.pkl`
- **Log Output**: `ai_alerts.log`
- **Dashboard Index**: `hybrid-ids-ai-alerts-*`

**Parallel: Host-Based Detection (HIDS)**
- **Code**: `src/hids/*.py`
- **Main**: `src/hids/hids_main.py`
- **Log Output**: `hids_alerts.log`
- **Dashboard Index**: `hybrid-ids-hids-alerts-*`

**Central Dashboard**
- **Platform**: ELK Stack (Elasticsearch + Logstash + Kibana)
- **Location**: `elk/`
- **Access**: http://localhost:5601
- **Features**:
  - Alert correlation
  - Manual review queue (for feedback loop)
  - Real-time visualization
  - MITRE ATT&CK mapping

### Feedback Loop Implementation

**Manual Review**
- **Interface**: Kibana dashboard
- **Queue**: Custom visualization showing A-IDS anomalies
- **Validation**: Analyst reviews in dashboard

**Rule Updates**
- **Current**: Manual update to `src/nids/rules/`
- **Future**: Automated rule generation from confirmed anomalies

---

## Key Files by Role

### For Developers

**Building the System:**
- `CMakeLists.txt` - C++ build configuration
- `requirements.txt` - Python dependencies
- `elk/docker-compose.yml` - ELK Stack deployment

**Core Engines:**
- `src/nids/sids.cpp` - Tier 1: Signature matching
- `src/nids/nids.cpp` - Tier 2: Feature extraction
- `src/ai/inference/anomaly_detector.py` - Tier 2: ML detection
- `src/hids/hids_main.py` - Host monitoring

### For Users

**Setup & Deployment:**
- `README.md` - Quick start guide
- `COMPLETE_INTEGRATION_GUIDE.md` - Full deployment
- `REAL_TIME_DEPLOYMENT.md` - Windows specific

**Understanding the System:**
- `ARCHITECTURE_EXPLAINED.md` - Two-tier architecture
- `ORIGINAL_PLAN.md` - Original design blueprint

**Testing & Validation:**
- `VALIDATION_CHECKLIST.md` - Testing procedures
- `scripts/test_ai_fix.py` - Component tests

### For Reporting

**Project Documentation:**
- `ARCHITECTURE_EXPLAINED.md` - Architecture explanation
- `VALIDATION_CHECKLIST.md` - Test results template
- `ELK_DASHBOARD_GUIDE.md` - Dashboard screenshots

---

## Log Files (Generated at Runtime)

```
Hybrid-IDS-MCP/
├── nids_alerts.log       ⚡ S-IDS (Tier 1) detections
├── ai_alerts.log         🧠 A-IDS (Tier 2) anomalies
├── hids_alerts.log       🏠 HIDS host events
└── features.csv          📊 Extracted features (optional)
```

---

## Data Flow Through Structure

```
1. Network Traffic
   ↓
2. src/nids/sids.cpp (Tier 1)
   ├─ Known threat → nids_alerts.log
   └─ Unknown → Pass to Tier 2
              ↓
3. src/nids/features/ (Feature extraction)
   ↓
4. src/ai/inference/anomaly_detector.py (Tier 2)
   ├─ Benign → Pass
   └─ Anomaly → ai_alerts.log
              ↓
5. elk/logstash/ (Processing)
   ↓
6. elk/elasticsearch/ (Storage)
   ↓
7. elk/kibana/ (Visualization)
   ↓
8. Manual Review Queue
   ↓
9. Confirmed Anomalies
   ↓
10. src/nids/rules/ (New signatures)
    ↓
   Feedback Loop Closes!
```

**Parallel:** `src/hids/` monitors host → `hids_alerts.log` → ELK → Dashboard

---

## Clean Structure Philosophy

### What We Removed

❌ Redundant documentation (START_HERE, QUICKSTART, etc.)
❌ Empty placeholder directories (mcp/, dashboard/, data/)
❌ Duplicate summaries and completion reports
❌ Unnecessary abstractions

### What We Kept

✅ Essential documentation only
✅ Clear two-tier architecture mapping
✅ University project scope
✅ All functional code components
✅ Complete ELK integration

---

**Last Updated:** 2025-10-19
**Purpose:** Clear mapping of project structure to two-tier architecture

---

**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Project:** Final Year B.Tech - Hybrid IDS
**Academic Year:** 2024-2025
**Last Updated:** October 2025
**Purpose:** Documentation of project structure and architecture mapping
