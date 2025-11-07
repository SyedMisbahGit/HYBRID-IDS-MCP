# Hybrid IDS - Windows Quick Start Guide

## Overview
This guide will help you run the Hybrid IDS project on Windows. The system consists of three main components:

1. **HIDS (Host-based IDS)** - Python-based, monitors files, processes, and logs
2. **NIDS (Network-based IDS)** - C++-based, monitors network traffic (requires compilation)
3. **AI/ML Engine** - Python-based, performs anomaly detection

## Current Status on Windows

### ✅ Working Components (No Build Required)
- **HIDS (Host-based IDS)** - Fully functional
  - File Integrity Monitoring
  - Process Monitoring
  - Log Analysis (Windows Event Logs)
  - All Python dependencies installed

### ⚠️ Requires Build (Optional)
- **NIDS (Network-based IDS)** - Requires CMake and C++ compiler
- **AI/ML Engine** - Requires trained models

## Quick Start - HIDS Only

### Option 1: Run Test Demo (Recommended First)
```powershell
python test_hids.py
```

This will:
- Display system information
- Create a process baseline
- Scan for suspicious processes
- Check network connections
- Show statistics

### Option 2: Run Full HIDS System
```powershell
python src\hids\hids_main.py --config config\hids\hids_config.yaml --no-logs
```

This will:
- Monitor file integrity in critical directories
- Monitor running processes
- Detect suspicious activities
- Generate alerts in `logs/hids_alerts.log`

Press `Ctrl+C` to stop.

### Option 3: Use the Launcher Script
```powershell
run_hids.bat
```

This provides a menu-driven interface to:
1. Run full HIDS
2. Run HIDS without log monitoring
3. Run quick test
4. Exit

## What HIDS Monitors

### File Integrity Monitoring
- **Windows System32** - Critical system files
- **Windows SysWOW64** - 32-bit system files
- **Program Files** - Installed applications
- Detects: File modifications, deletions, new files

### Process Monitoring
- All running processes
- CPU and memory usage
- Network connections
- Detects: Suspicious process names, unusual behavior, new processes

### Log Analysis (Optional)
- Windows Security Event Log
- Windows System Event Log
- Windows Application Event Log
- Detects: Failed logins, privilege escalation, system changes

## Configuration

The HIDS configuration is in `config/hids/hids_config.yaml`:

```yaml
# Enable/disable components
file_monitoring: true
process_monitoring: true
log_monitoring: true  # Set to false if you don't want log monitoring

# Check intervals
check_interval: 60  # File/process checks every 60 seconds
log_check_interval: 300  # Log checks every 5 minutes

# Elasticsearch (optional)
elasticsearch_enabled: false  # Set to true if you have ELK stack running
```

## Output and Alerts

### Alert Log
All alerts are written to: `logs/hids_alerts.log`

Example alert:
```json
{
  "timestamp": "2025-11-01T10:58:53",
  "alert_type": "process_monitoring",
  "severity": "MEDIUM",
  "message": "Suspicious process detected",
  "details": {
    "pid": 8776,
    "name": "powershell.exe",
    "reason": "New process since baseline"
  }
}
```

### Baseline Files
- **Process baseline**: Created automatically on first run
- **File baseline**: `data/hids_baseline.json` (created automatically)

## Command Line Options

```powershell
# Full HIDS with all monitoring
python src\hids\hids_main.py --config config\hids\hids_config.yaml

# Disable specific components
python src\hids\hids_main.py --no-files      # No file monitoring
python src\hids\hids_main.py --no-processes  # No process monitoring
python src\hids\hids_main.py --no-logs       # No log monitoring

# Enable Elasticsearch export
python src\hids\hids_main.py --elasticsearch --es-host http://localhost:9200

# Custom baseline file
python src\hids\hids_main.py --baseline my_baseline.json
```

## Building NIDS (Optional - Advanced)

To build the C++ NIDS components, you need:

### Prerequisites
1. **CMake** - Download from https://cmake.org/download/
2. **Visual Studio Build Tools** or **MinGW-w64**
3. **Npcap** - Download from https://npcap.com/

### Build Steps
```powershell
# Create build directory
mkdir build
cd build

# Configure with CMake
cmake .. -G "Visual Studio 17 2022"
# OR for MinGW:
# cmake .. -G "MinGW Makefiles"

# Build
cmake --build . --config Release

# Run NIDS
.\Release\sids.exe -i <network_interface>
```

## Troubleshooting

### "Permission Denied" Errors
- Run PowerShell as Administrator
- Some system files require elevated privileges

### "Module Not Found" Errors
```powershell
pip install -r requirements.txt
```

### High CPU Usage
- Reduce check frequency in `config/hids/hids_config.yaml`
- Disable file monitoring for large directories
- Use `--no-files` flag

### Windows Defender Interference
- Add project directory to Windows Defender exclusions
- The HIDS may be flagged as suspicious due to process monitoring

### File Monitoring Errors
The HIDS automatically skips:
- Symbolic links and reparse points
- WindowsApps directory
- Temporary files
- Log files

## Performance Considerations

### Recommended Settings for Testing
```yaml
check_interval: 120  # Check every 2 minutes instead of 1
max_files_per_scan: 5000  # Limit files scanned per cycle
file_monitoring: true
process_monitoring: true
log_monitoring: false  # Disable for initial testing
```

### System Requirements
- **RAM**: 2GB minimum, 4GB recommended
- **CPU**: Any modern processor
- **Disk**: 1GB free space for logs and baselines
- **OS**: Windows 10/11 (64-bit)

## What's Working vs What's Not

### ✅ Fully Working
- Process monitoring and detection
- System information gathering
- Network connection monitoring
- Suspicious process detection
- Alert generation and logging

### ✅ Working (Requires Admin)
- File integrity monitoring
- Windows Event Log analysis

### ⚠️ Not Built Yet
- C++ NIDS components (requires CMake)
- AI/ML anomaly detection (requires trained models)
- ELK Stack integration (requires Docker)

## Next Steps

1. **Test HIDS**: Run `python test_hids.py`
2. **Monitor Your System**: Run `run_hids.bat` and choose option 2
3. **Review Alerts**: Check `logs/hids_alerts.log`
4. **Build NIDS** (optional): Follow build instructions above
5. **Train ML Models** (optional): See `src/ai/training/`

## Support

For issues or questions:
- Check `HIDS_BUGFIX_WINDOWS.md` for known issues
- Review `VALIDATION_CHECKLIST.md` for troubleshooting
- See `COMPLETE_INTEGRATION_GUIDE.md` for full setup

## Summary

The HIDS component is **fully functional on Windows** and can:
- Monitor your system for suspicious activities
- Detect file modifications
- Track process behavior
- Generate security alerts

No compilation required - just Python!

---

**Last Updated**: November 2025  
**Status**: HIDS Fully Operational on Windows  
**Author**: Syed Misbah Uddin
