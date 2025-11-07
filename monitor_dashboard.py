#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard for Hybrid IDS
Displays live statistics from HIDS components
"""

import sys
import time
import os
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'hids'))

try:
    from process_monitor import ProcessMonitor
    import psutil
except ImportError as e:
    print(f"[ERROR] Missing dependencies: {e}")
    print("Install with: pip install psutil")
    sys.exit(1)


class MonitoringDashboard:
    """Real-time monitoring dashboard"""
    
    def __init__(self):
        self.process_monitor = ProcessMonitor()
        self.start_time = time.time()
        self.alert_count = 0
        self.scan_count = 0
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_system_stats(self):
        """Get current system statistics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\' if os.name == 'nt' else '/')
        
        return {
            'cpu': cpu_percent,
            'memory': mem.percent,
            'disk': disk.percent,
            'processes': len(psutil.pids())
        }
    
    def get_network_stats(self):
        """Get network statistics"""
        net_io = psutil.net_io_counters()
        connections = len(psutil.net_connections())
        
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'connections': connections
        }
    
    def format_bytes(self, bytes_val):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"
    
    def format_uptime(self, seconds):
        """Format uptime"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def draw_bar(self, value, max_val=100, width=30):
        """Draw a progress bar"""
        filled = int((value / max_val) * width)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {value:.1f}%"
    
    def display_dashboard(self):
        """Display the monitoring dashboard"""
        self.clear_screen()
        
        # Header
        print("=" * 80)
        print(" " * 20 + "HYBRID IDS - MONITORING DASHBOARD")
        print("=" * 80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | " +
              f"Uptime: {self.format_uptime(time.time() - self.start_time)}")
        print("=" * 80)
        print()
        
        # System Resources
        sys_stats = self.get_system_stats()
        print("┌─ SYSTEM RESOURCES " + "─" * 59 + "┐")
        print(f"│ CPU Usage:    {self.draw_bar(sys_stats['cpu'])} │")
        print(f"│ Memory Usage: {self.draw_bar(sys_stats['memory'])} │")
        print(f"│ Disk Usage:   {self.draw_bar(sys_stats['disk'])} │")
        print(f"│ Processes:    {sys_stats['processes']:>4} running" + " " * 50 + "│")
        print("└" + "─" * 78 + "┘")
        print()
        
        # Network Statistics
        net_stats = self.get_network_stats()
        print("┌─ NETWORK ACTIVITY " + "─" * 59 + "┐")
        print(f"│ Bytes Sent:     {self.format_bytes(net_stats['bytes_sent']):>15}" + " " * 44 + "│")
        print(f"│ Bytes Received: {self.format_bytes(net_stats['bytes_recv']):>15}" + " " * 44 + "│")
        print(f"│ Connections:    {net_stats['connections']:>15}" + " " * 44 + "│")
        print("└" + "─" * 78 + "┘")
        print()
        
        # Process Monitor Stats
        pm_stats = self.process_monitor.stats
        print("┌─ PROCESS MONITORING " + "─" * 57 + "┐")
        print(f"│ Total Scans:          {self.scan_count:>6}" + " " * 45 + "│")
        print(f"│ Processes Scanned:    {pm_stats['processes_scanned']:>6}" + " " * 45 + "│")
        print(f"│ Suspicious Processes: {pm_stats['suspicious_processes']:>6}" + " " * 45 + "│")
        print(f"│ New Processes:        {pm_stats['new_processes']:>6}" + " " * 45 + "│")
        print(f"│ Network Connections:  {pm_stats['network_connections']:>6}" + " " * 45 + "│")
        print(f"│ Suspicious Conns:     {pm_stats['suspicious_connections']:>6}" + " " * 45 + "│")
        print("└" + "─" * 78 + "┘")
        print()
        
        # Alert Summary
        print("┌─ ALERT SUMMARY " + "─" * 62 + "┐")
        print(f"│ Total Alerts: {self.alert_count:>6}" + " " * 53 + "│")
        if self.alert_count > 0:
            print(f"│ Last Alert:   {datetime.now().strftime('%H:%M:%S')}" + " " * 52 + "│")
        print("└" + "─" * 78 + "┘")
        print()
        
        # Top Processes
        print("┌─ TOP PROCESSES (CPU) " + "─" * 56 + "┐")
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            for i, proc in enumerate(processes[:5]):
                name = proc['name'][:30] if proc['name'] else 'Unknown'
                cpu = proc['cpu_percent'] or 0
                print(f"│ {i+1}. PID {proc['pid']:>6} | {name:30s} | {cpu:>5.1f}% CPU │")
            
            if len(processes) < 5:
                for i in range(len(processes), 5):
                    print(f"│ {i+1}. " + " " * 68 + "│")
        except Exception as e:
            print(f"│ Error getting processes: {str(e)[:50]}" + " " * (78 - len(str(e)[:50]) - 27) + "│")
        
        print("└" + "─" * 78 + "┘")
        print()
        
        # Controls
        print("─" * 80)
        print("Controls: [R] Refresh Now | [Q] Quit | Auto-refresh every 5 seconds")
        print("─" * 80)
    
    def run_scan(self):
        """Run a monitoring scan"""
        self.scan_count += 1
        
        # Scan processes
        alerts = self.process_monitor.scan_processes()
        self.alert_count += len(alerts)
        
        # Scan network
        conn_alerts = self.process_monitor.scan_network_connections()
        self.alert_count += len(conn_alerts)
        
        return alerts + conn_alerts
    
    def run(self, interval=5):
        """Run the monitoring dashboard"""
        print("\nInitializing monitoring dashboard...")
        print("Creating process baseline...")
        self.process_monitor.create_baseline()
        print(f"Baseline created with {len(self.process_monitor.baseline_processes)} processes")
        print("\nStarting monitoring...\n")
        time.sleep(2)
        
        try:
            last_scan = 0
            while True:
                current_time = time.time()
                
                # Run scan if interval elapsed
                if current_time - last_scan >= interval:
                    self.run_scan()
                    last_scan = current_time
                
                # Update display
                self.display_dashboard()
                
                # Wait a bit before next update
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n[INFO] Monitoring stopped by user")
            print("\nFinal Statistics:")
            self.process_monitor.print_stats()


def main():
    """Main entry point"""
    print("=" * 80)
    print(" " * 25 + "HYBRID IDS MONITORING DASHBOARD")
    print("=" * 80)
    print()
    print("This dashboard provides real-time monitoring of:")
    print("  - System resources (CPU, Memory, Disk)")
    print("  - Network activity")
    print("  - Process monitoring")
    print("  - Security alerts")
    print()
    print("Press Ctrl+C to stop monitoring")
    print()
    input("Press Enter to start...")
    
    dashboard = MonitoringDashboard()
    dashboard.run(interval=5)


if __name__ == "__main__":
    main()
