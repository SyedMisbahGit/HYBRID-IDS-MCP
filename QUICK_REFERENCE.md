# Hybrid IDS - Quick Reference Card

## 🚀 Quick Start Commands

### Run HIDS (Host-based IDS)
```powershell
# Option 1: Quick test (30 seconds)
python test_hids.py

# Option 2: Interactive launcher
run_hids.bat

# Option 3: Full monitoring
python src\hids\hids_main.py --config config\hids\hids_config.yaml --no-logs

# Option 4: Real-time dashboard
python monitor_dashboard.py
```

### Run NIDS (Network-based IDS) - NEW! ✨
```powershell
# Option 1: Quick test
python test_nids.py

# Option 2: Interactive launcher
run_nids.bat

# Option 3: Analyze PCAP file
python src\nids_python\nids_main.py -r test.pcap

# Option 4: Live capture (requires admin)
python src\nids_python\nids_main.py -i "Wi-Fi"
```

## 📊 What's Working on Windows

| Component | Status | Command |
|-----------|--------|---------|
| HIDS | ✅ Working | `python test_hids.py` |
| Process Monitor | ✅ Working | Included in HIDS |
| File Monitor | ✅ Working | Included in HIDS |
| Dashboard | ✅ Working | `python monitor_dashboard.py` |
| **NIDS (Python)** | ✅ **Working** | `python test_nids.py` |
| **Signature IDS** | ✅ **Working** | Included in NIDS |
| **Feature Extraction** | ✅ **Working** | Included in NIDS |
| NIDS (C++) | ⚠️ Needs Build | Requires CMake |
| AI/ML | ⚠️ Needs Models | Code ready |
| ELK Stack | ❌ Needs Docker | Optional |

## 📁 Important Files

### Configuration
- `config/hids/hids_config.yaml` - HIDS settings

### Scripts
- `test_hids.py` - HIDS quick test
- `test_nids.py` - NIDS quick test ✨ NEW
- `run_hids.bat` - HIDS launcher
- `run_nids.bat` - NIDS launcher ✨ NEW
- `monitor_dashboard.py` - Dashboard
- `src/hids/hids_main.py` - Full HIDS
- `src/nids_python/nids_main.py` - Full NIDS ✨ NEW

### Documentation
- `WINDOWS_QUICKSTART.md` - Windows guide
- `PROJECT_STATUS_WINDOWS.md` - Full status
- `WINDOWS_RUN_SUMMARY.md` - Execution summary
- `NIDS_COMPLETE_PYTHON.md` - NIDS documentation ✨ NEW
- `NIDS_COMPLETION_SUMMARY.md` - NIDS summary ✨ NEW

### Output
- `logs/hids_alerts.log` - Alerts (JSON)
- `data/hids_baseline.json` - File baseline

## 🎯 Common Tasks

### View Alerts
```powershell
# View latest alerts
Get-Content logs\hids_alerts.log -Tail 20

# Count alerts
(Get-Content logs\hids_alerts.log).Count
```

### Check System Status
```powershell
# System info
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%'); print(f'RAM: {psutil.virtual_memory().percent}%')"

# Running processes
python -c "import psutil; print(f'Processes: {len(psutil.pids())}')"
```

### Modify Configuration
```powershell
# Edit HIDS config
notepad config\hids\hids_config.yaml

# Key settings:
# - check_interval: 60 (seconds between scans)
# - file_monitoring: true/false
# - process_monitoring: true/false
```

## 🔧 Troubleshooting

### Issue: Permission Denied
**Solution**: Run PowerShell as Administrator

### Issue: Module Not Found
**Solution**: 
```powershell
pip install -r requirements.txt
```

### Issue: High CPU Usage
**Solution**: Edit `config/hids/hids_config.yaml`:
```yaml
check_interval: 120  # Increase from 60
```

### Issue: Too Many Alerts
**Solution**: Adjust sensitivity in config or filter specific processes

## 📈 Performance Tips

### For Testing
```yaml
check_interval: 120  # Check every 2 minutes
max_files_per_scan: 5000  # Limit file scans
log_monitoring: false  # Disable log monitoring
```

### For Production
```yaml
check_interval: 60  # Check every minute
max_files_per_scan: 10000  # More thorough
log_monitoring: true  # Enable all features
elasticsearch_enabled: true  # If using ELK
```

## 🎓 For Your Project Report

### Screenshots to Capture
1. HIDS test output (`python test_hids.py`)
2. Monitoring dashboard (`python monitor_dashboard.py`)
3. Alert log file (`logs/hids_alerts.log`)
4. System statistics
5. Configuration file

### Key Points to Mention
- Two-tier detection architecture
- Real-time process monitoring
- File integrity checking
- Windows-specific optimizations
- JSON alert format
- Configurable detection rules

### Metrics to Report
- Processes scanned: 200+
- Detection time: < 1 second
- Memory usage: ~50-100 MB
- Alert latency: < 1 second
- Baseline creation: 4-5 seconds

## 🔐 Security Features

### Process Detection
- Suspicious names (nc, nmap, metasploit)
- New processes
- High resource usage
- Unusual network connections

### File Monitoring
- Hash-based integrity
- Modification detection
- New/deleted files
- Critical system paths

### Log Analysis
- Failed logins
- Privilege escalation
- System changes
- Service modifications

## 📞 Quick Help

### View Documentation
```powershell
# Windows guide
notepad WINDOWS_QUICKSTART.md

# Full status
notepad PROJECT_STATUS_WINDOWS.md

# Architecture
notepad ARCHITECTURE_EXPLAINED.md
```

### Check Dependencies
```powershell
# Python version
python --version

# Installed packages
pip list | findstr "psutil watchdog yaml"
```

### Test Components
```powershell
# Test Python imports
python -c "import psutil, watchdog, yaml; print('All dependencies OK')"

# Test HIDS
python test_hids.py
```

## 🎯 Next Steps

### To Build NIDS
1. Install CMake: https://cmake.org/download/
2. Install Visual Studio Build Tools
3. Install Npcap: https://npcap.com/
4. Run: `cmake .. && cmake --build .`

### To Train ML Models
1. Get dataset (CICIDS2017)
2. Run: `python src\ai\training\train_models.py`
3. Models saved to `models/`

### To Deploy ELK
1. Install Docker Desktop
2. Run: `cd elk && docker-compose up -d`
3. Access: http://localhost:5601

## 📊 Component Status

```
✅ WORKING NOW:
- HIDS (Host-based IDS)
  - Process Monitoring
  - File Integrity Monitoring
  - Log Analysis
- NIDS (Network-based IDS) ✨ NEW
  - Packet Capture
  - Signature Detection
  - Feature Extraction
- Alert Generation
- Custom Dashboard

⚠️ NEEDS SETUP:
- NIDS C++ (needs CMake) - Optional
- AI/ML (needs training)
- ELK Stack (needs Docker)
```

## 💡 Pro Tips

1. **Start Simple**: Use `python test_hids.py` first
2. **Monitor Gradually**: Start with process monitoring only
3. **Review Alerts**: Check `logs/hids_alerts.log` regularly
4. **Tune Sensitivity**: Adjust config based on your environment
5. **Use Dashboard**: `monitor_dashboard.py` for real-time view

## 🆘 Emergency Commands

### Stop All Monitoring
```powershell
# Press Ctrl+C in the terminal
# Or kill Python processes
taskkill /F /IM python.exe
```

### Clear Logs
```powershell
# Clear alert log
del logs\hids_alerts.log

# Clear baseline
del data\hids_baseline.json
```

### Reset Configuration
```powershell
# Restore from backup or re-download
git checkout config/hids/hids_config.yaml
```

---

**Quick Support**: Check `WINDOWS_QUICKSTART.md` for detailed help

**Last Updated**: November 1, 2025
