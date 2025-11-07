#!/usr/bin/env python3
"""
Test script to demonstrate HIDS functionality on Windows
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'hids'))

from process_monitor import ProcessMonitor
import psutil

def test_process_monitor():
    """Test process monitoring"""
    print("="*60)
    print("  Testing HIDS - Process Monitor")
    print("="*60)
    print()
    
    monitor = ProcessMonitor()
    
    # Create baseline
    print("[1] Creating process baseline...")
    monitor.create_baseline()
    print(f"    Baseline created with {len(monitor.baseline_processes)} processes")
    print()
    
    # Scan current processes
    print("[2] Scanning current processes...")
    alerts = monitor.scan_processes()
    print(f"    Scanned {monitor.stats['processes_scanned']} processes")
    print(f"    Found {len(alerts)} suspicious processes")
    print()
    
    # Show some running processes
    print("[3] Sample of running processes:")
    for i, proc in enumerate(psutil.process_iter(['pid', 'name', 'username'])):
        try:
            print(f"    PID: {proc.info['pid']:6d} | Name: {proc.info['name'][:30]:30s} | User: {proc.info['username']}")
            if i >= 9:  # Show first 10
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    print()
    
    # Scan network connections
    print("[4] Scanning network connections...")
    conn_alerts = monitor.scan_network_connections()
    print(f"    Found {monitor.stats['network_connections']} active connections")
    print(f"    Found {len(conn_alerts)} suspicious connections")
    print()
    
    # Print statistics
    print("[5] Process Monitor Statistics:")
    monitor.print_stats()
    print()
    
    print("="*60)
    print("  HIDS Process Monitor Test Complete!")
    print("="*60)
    return True

def test_system_info():
    """Display system information"""
    print("\n" + "="*60)
    print("  System Information")
    print("="*60)
    print()
    
    print(f"CPU Count: {psutil.cpu_count()}")
    print(f"CPU Usage: {psutil.cpu_percent(interval=1)}%")
    
    mem = psutil.virtual_memory()
    print(f"Memory Total: {mem.total / (1024**3):.2f} GB")
    print(f"Memory Used: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
    
    disk = psutil.disk_usage('C:\\')
    print(f"Disk Total: {disk.total / (1024**3):.2f} GB")
    print(f"Disk Used: {disk.used / (1024**3):.2f} GB ({disk.percent}%)")
    
    print(f"Boot Time: {psutil.boot_time()}")
    print()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Hybrid IDS - HIDS Component Test")
    print("  Windows Platform")
    print("="*60)
    print()
    
    try:
        # Test system info
        test_system_info()
        
        # Test process monitor
        test_process_monitor()
        
        print("\n[SUCCESS] All HIDS tests completed successfully!")
        print("\nNote: To run the full HIDS system, use:")
        print("  python src\\hids\\hids_main.py --config config\\hids\\hids_config.yaml")
        print()
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
