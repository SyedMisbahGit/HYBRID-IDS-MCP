# Hybrid IDS - Quick Start Guide

## ⚡ Fast Track

### 1. Setup

```bash
# Install dependencies
pip install -r src/ml/requirements.txt
pip install -r dashboard/requirements.txt

# Generate mock data (for instant testing)
python utils/mock_generator.py
```

### 2. Train

```bash
# Train all models (takes ~1 min with mock data)
python src/ml/nids/sids_trainer.py
python src/ml/nids/aids_trainer.py
python src/ml/hids/sequence_trainer.py
```

### 3. Run

```bash
# Launch SIEM Dashboard
python dashboard/app.py
```

**URL**: `http://127.0.0.1:8050`

---

## 📥 Real Data Setup

To use the full 7GB+ datasets:

1. Run the downloader:
   ```bash
   python scripts/download_manager.py
   ```
2. Select **Option 3 (Both)**.
3. If auto-download fails, follow the printed manual instructions.
4. Re-run training scripts (they auto-detect real data).

---

## 🛠️ Troubleshooting

- **Missing Modules**: Ensure you ran both `pip install` commands.
- **Dashboard Error**: If port 8050 is in use, edit `dashboard/app.py` line 250 to change the port.
- **Model Errors**: Ensure you ran the training scripts at least once.
