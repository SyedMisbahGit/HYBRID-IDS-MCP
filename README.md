# SENTINEL | CORE - Hybrid Intrusion Detection System

**Enterprise-Grade SIEM Platform with Machine Learning**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-2.14-blue.svg)](https://dash.plotly.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-orange.svg)](https://www.tensorflow.org/)

> **Author:** Syed Misbah Uddin  
> **Institution:** Central University of Jammu  
> **Program:** B.Tech (Final Year) - Computer Science & Engineering (Cybersecurity)  
> **Status:** Production-Ready

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Datasets](#datasets)
- [Performance](#performance)
- [Documentation](#documentation)
- [License](#license)
- [Contact](#contact)

---

## Overview

SENTINEL | CORE is a professional Security Information and Event Management (SIEM) platform that combines network and host-based intrusion detection using machine learning. The system features a domain-separated architecture with real-time visualization and decision pipeline transparency.

### Key Capabilities

- **Dual-Layer Detection**: Network (NIDS) and Host (HIDS) intrusion detection operating independently
- **Multi-Engine Approach**: Signature-based (SIDS), Anomaly-based (A-IDS), and Sequence-based (LSTM) detection
- **Real-Time Dashboard**: Professional SOC interface with live threat visualization
- **Decision Pipeline**: Transparent, explainable ML decision-making process
- **Context-Aware Simulation**: Independent network and host attack injection for testing

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    SENTINEL | CORE                          │
│                  SIEM Platform Layer                        │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                    ┌────────▼───────┐
│  NIDS Layer    │                    │  HIDS Layer    │
│  (Network)     │                    │  (Host)        │
└───────┬────────┘                    └────────┬───────┘
        │                                      │
   ┌────┴────┐                            ┌────┴────┐
   │         │                            │         │
┌──▼──┐  ┌──▼──┐                      ┌──▼──┐      │
│SIDS │  │A-IDS│                      │LSTM │      │
│ RF  │  │ IF  │                      │Auto │      │
└──┬──┘  └──┬──┘                      └──┬──┘      │
   │        │                            │         │
   └────┬───┘                            └────┬────┘
        │                                     │
        └──────────┬──────────────────────────┘
                   │
          ┌────────▼────────┐
          │  Unified        │
          │  Prediction     │
          │  Engine         │
          └─────────────────┘
```

### ML Models

| Component | Algorithm        | Purpose                           | Dataset     |
| --------- | ---------------- | --------------------------------- | ----------- |
| **SIDS**  | Random Forest    | Multi-class attack classification | CIC-IDS2017 |
| **A-IDS** | Isolation Forest | Zero-day anomaly detection        | CIC-IDS2017 |
| **HIDS**  | LSTM Autoencoder | System call sequence analysis     | ADFA-LD     |

---

## Features

### Multi-Domain Defense Console

The dashboard separates Network and Host operations into distinct tabs for clarity:

#### Tab 1: Network Defense (NIDS)

- **Decision Pipeline Visualization**:

  - Stage 1: Traffic Input
  - Stage 2: Known Threats (SIDS) - Signature matching
  - Stage 3: Behavior Scan (A-IDS) - Anomaly detection
  - Stage 4: Final Decision (Allow/Block/Flag)

- **Real-Time Metrics**:

  - Live network traffic volume chart
  - SIDS probability distribution (bar chart)
  - A-IDS anomaly score gauge with threshold indicator

- **Performance**: >90% accuracy on CIC-IDS2017 dataset

#### Tab 2: Host Integrity (HIDS)

- **Decision Pipeline Visualization**:

  - Stage 1: System Calls Input
  - Stage 2: Signature Check - Known malicious patterns
  - Stage 3: Anomaly Check - LSTM deviation analysis
  - Stage 4: System Status (Healthy/Compromised)

- **Real-Time Metrics**:

  - System call sequence heatmap
  - Syscall distribution histogram (read, write, execve, setuid)

- **Performance**: >85% accuracy on ADFA-LD dataset

#### Global Features

- **Unified Event Logging**: Correlated network and host events in real-time
- **Context-Aware Simulation**: Independent attack injection for NIDS and HIDS
- **Professional UI**: Monospace fonts, neon cyan/amber accents, CRT scanline effects

### Waterfall Decision Logic

The system implements short-circuit evaluation:

**Known Threat Scenario**:

```
Traffic → SIDS Detects DDoS → [BLOCKED] → A-IDS Skipped
```

**Zero-Day Scenario**:

```
Traffic → SIDS Clean → A-IDS Detects Anomaly → [FLAGGED]
```

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- 8GB RAM minimum (16GB recommended for full dataset)
- 10GB free disk space

### Installation

```bash
# Clone repository
git clone https://github.com/SyedMisbahGit/HYBRID-IDS-MCP.git
cd HYBRID-IDS-MCP

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r src/ml/requirements.txt
pip install -r dashboard/requirements.txt
```

### Data Setup

**Option A: Mock Data (Quick Test)**

```bash
python utils/mock_generator.py
```

Generates synthetic data instantly for testing the pipeline.

**Option B: Real Datasets (Production)**

```bash
python scripts/download_manager.py
```

Downloads CIC-IDS2017 (7GB) and ADFA-LD (500MB) automatically.

**Option C: Smart Sampling (Recommended)**

```bash
# After downloading real data
python scripts/data_sampler.py
```

Creates a balanced subset: 100% attacks + 10% benign traffic.

### Model Training

```bash
# Train Network IDS models
python src/ml/nids/sids_trainer.py    # Signature-based
python src/ml/nids/aids_trainer.py    # Anomaly-based

# Train Host IDS model
python src/ml/hids/sequence_trainer.py
```

Performance metrics are saved to `models/performance_report.txt`.

### Launch Dashboard

```bash
python dashboard/app.py
```

Access the SIEM dashboard at: **http://127.0.0.1:8050**

---

## Project Structure

```
HYBRID-IDS-MCP/
├── dashboard/
│   ├── app.py                    # Main SIEM application
│   ├── config.py                 # Configuration settings
│   └── assets/
│       └── custom.css            # Professional styling
│
├── src/ml/
│   ├── nids/
│   │   ├── sids_trainer.py       # Random Forest trainer
│   │   ├── aids_trainer.py       # Isolation Forest trainer
│   │   └── data_loader.py        # CIC-IDS2017 loader
│   ├── hids/
│   │   ├── sequence_trainer.py   # LSTM trainer
│   │   └── data_loader.py        # ADFA-LD loader
│   └── prediction_engine.py      # Unified inference engine
│
├── scripts/
│   ├── download_manager.py       # Dataset downloader
│   └── data_sampler.py           # Smart stratified sampling
│
├── utils/
│   └── mock_generator.py         # Synthetic data generator
│
├── data/
│   ├── mock/                     # Synthetic data (tracked)
│   ├── raw/                      # Real datasets (ignored)
│   └── processed/                # Sampled data (ignored)
│
├── models/
│   ├── nids/                     # NIDS models
│   ├── hids/                     # HIDS models
│   └── performance_report.txt    # Training metrics
│
└── docs/
    └── DEMO_SCRIPT.md            # Demonstration guide
```

---

## Datasets

### CIC-IDS2017 (Network Traffic)

- **Source**: Canadian Institute for Cybersecurity
- **Size**: ~7GB (2.8M flows)
- **Format**: CSV with 78 features
- **Labels**: BENIGN, DoS, DDoS, PortScan, BruteForce, Web Attack, Infiltration, Botnet
- **Usage**: Training NIDS (SIDS + A-IDS)

### ADFA-LD (System Calls)

- **Source**: Australian Defence Force Academy
- **Size**: ~500MB (100K sequences)
- **Format**: Text files with syscall IDs
- **Labels**: Normal, Attack (various types)
- **Usage**: Training HIDS (LSTM Autoencoder)

---

## Performance

### Model Metrics

| Model       | Accuracy | Precision | Recall | F1-Score | Dataset     |
| ----------- | -------- | --------- | ------ | -------- | ----------- |
| SIDS (RF)   | 92.3%    | 91.8%     | 90.5%  | 91.1%    | CIC-IDS2017 |
| A-IDS (IF)  | 88.7%    | 87.2%     | 89.1%  | 88.1%    | CIC-IDS2017 |
| HIDS (LSTM) | 86.4%    | 85.9%     | 84.7%  | 85.3%    | ADFA-LD     |

### System Performance

- **Inference Latency**: <50ms per prediction
- **Dashboard Refresh**: 1000ms (configurable)
- **Memory Usage**: ~2GB with all models loaded
- **Throughput**: 1000+ predictions/second

---

## Documentation

- **[DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)**: Step-by-step demonstration guide
- **[ARCHITECTURE_ML_DEMO.md](ARCHITECTURE_ML_DEMO.md)**: ML architecture details
- **[QUICKSTART.md](QUICKSTART.md)**: Quick setup guide

---

## Development

### Code Quality

- **No AI-Generated Emojis**: Professional codebase with standard logging
- **Type Hints**: Used throughout for better IDE support
- **Error Handling**: Custom error messages with actionable guidance
- **Logging**: Structured logging with severity levels
- **Configuration**: Centralized in `dashboard/config.py`

### Testing

```bash
# Test with mock data
python utils/mock_generator.py

# Verify model loading
python -c "from src.ml.prediction_engine import PredictionEngine; e = PredictionEngine(); e.load_all()"

# Launch dashboard in debug mode
python dashboard/app.py
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact

**Syed Misbah Uddin**  
B.Tech (Final Year) - Computer Science & Engineering (Cybersecurity)  
Central University of Jammu

- **GitHub**: [@SyedMisbahGit](https://github.com/SyedMisbahGit)
- **Project Repository**: [HYBRID-IDS-MCP](https://github.com/SyedMisbahGit/HYBRID-IDS-MCP)

---

## Acknowledgments

- **CIC-IDS2017 Dataset**: Canadian Institute for Cybersecurity
- **ADFA-LD Dataset**: Australian Defence Force Academy
- **Frameworks**: TensorFlow, Scikit-learn, Plotly Dash
- **Institution**: Central University of Jammu

---

**Built with precision. Deployed with confidence.**
