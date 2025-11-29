# Hybrid IDS - ML Demo Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STREAMLIT DASHBOARD                         │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ Tab 1: NIDS  │  │ Tab 2: HIDS  │  │ Tab 3: System Alerts     │ │
│  │              │  │              │  │                          │ │
│  │ • SIDS Chart │  │ • Sequence   │  │ • Alert Timeline         │ │
│  │ • A-IDS Chart│  │   Analysis   │  │ • Severity Distribution  │ │
│  │ • Metrics    │  │ • Metrics    │  │ • Recent Alerts Table    │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
│                                                                     │
│  Sidebar: Model Status | Simulation Mode | Configuration          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PREDICTION ENGINE                              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ load_all() → Load NIDS SIDS, NIDS A-IDS, HIDS models        │  │
│  │ predict_nids(features) → SIDS + A-IDS predictions            │  │
│  │ predict_hids(sequence) → LSTM anomaly detection              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                    │                                    │
        ┌───────────┴───────────┐         ┌─────────────┴──────────┐
        ▼                       ▼         ▼                        ▼
┌──────────────┐      ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  NIDS SIDS   │      │  NIDS A-IDS  │   │  HIDS LSTM   │   │   Scalers    │
│              │      │              │   │              │   │   Encoders   │
│ Random       │      │ Isolation    │   │ Autoencoder  │   │   Metadata   │
│ Forest       │      │ Forest       │   │              │   │              │
│              │      │              │   │              │   │              │
│ • 100 trees  │      │ • Benign     │   │ • Embedding  │   │ • Standard   │
│ • 6+ classes │      │   baseline   │   │ • LSTM       │   │   Scaler     │
│ • >90% acc   │      │ • >0.85 AUC  │   │ • >85% acc   │   │ • Label Enc  │
└──────────────┘      └──────────────┘   └──────────────┘   └──────────────┘
        ▲                       ▲                 ▲
        │                       │                 │
┌───────┴───────┐      ┌────────┴────────┐   ┌───┴──────────┐
│ SIDS Trainer  │      │ A-IDS Trainer   │   │ HIDS Trainer │
│               │      │                 │   │              │
│ • Load data   │      │ • Load benign   │   │ • Load traces│
│ • Extract     │      │   only          │   │ • Create     │
│   features    │      │ • Train IF      │   │   sequences  │
│ • Train RF    │      │ • Calc thresh   │   │ • Train LSTM │
│ • Evaluate    │      │ • Evaluate      │   │ • Evaluate   │
│ • Save model  │      │ • Save model    │   │ • Save model │
└───────────────┘      └─────────────────┘   └──────────────┘
        ▲                       ▲                 ▲
        │                       │                 │
        └───────────────────────┴─────────────────┘
                                │
                        ┌───────┴────────┐
                        │  Data Loaders  │
                        │                │
                        │ • CIC-IDS2017  │
                        │ • ADFA-LD      │
                        └────────────────┘
                                │
                        ┌───────┴────────┐
                        │   Datasets     │
                        │                │
                        │ CIC-IDS2017:   │
                        │ • 2.8M flows   │
                        │ • 78 features  │
                        │ • 15+ attacks  │
                        │                │
                        │ ADFA-LD:       │
                        │ • 833 normal   │
                        │ • 746 attacks  │
                        │ • Syscalls     │
                        └────────────────┘
```

## Data Flow

### Training Phase

```
Datasets → Data Loaders → Trainers → Models → Saved to disk
```

### Inference Phase

```
Input Data → Prediction Engine → Models → Predictions → Dashboard
```

### Simulation Mode

```
Sample CSV → Dashboard → Prediction Engine → Real-time Charts
```

## Technology Stack

| Component       | Technology                 |
| --------------- | -------------------------- |
| Dashboard       | Streamlit 1.29             |
| Visualization   | Plotly 5.18                |
| ML Framework    | scikit-learn 1.3.2         |
| Deep Learning   | TensorFlow 2.15            |
| Data Processing | pandas 2.1.4, NumPy 1.24.3 |

## Model Details

### NIDS SIDS (Supervised)

- **Algorithm**: Random Forest
- **Input**: 78 CIC flow features
- **Output**: Attack type (Benign, DoS, DDoS, PortScan, BruteForce, WebAttack)
- **Performance**: >90% accuracy

### NIDS A-IDS (Anomaly)

- **Algorithm**: Isolation Forest
- **Training**: Benign traffic only
- **Output**: Anomaly score + binary classification
- **Performance**: >0.85 ROC-AUC

### HIDS (Sequence)

- **Algorithm**: LSTM Autoencoder
- **Input**: 100 system call sequence
- **Output**: Reconstruction error + binary classification
- **Performance**: >85% accuracy
