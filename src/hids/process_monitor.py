#!/usr/bin/env python3
"""
Process Monitoring for HIDS
Monitors running processes for suspicious behavior and anomalies
"""

import psutil
import logging
from datetime import datetime
from typing import Dict, List, Set
import time

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ProcessMonitor:
    """
    Monitors system processes for suspicious activities
    """

    def __init__(self):
        """Initialize Process Monitor"""
        self.baseline_processes = set()
        self.suspicious_names = self._load_suspicious_patterns()
        self.suspicious_connections = []
        self.alerts = []
        self.stats = {
            'processes_scanned': 0,
            'suspicious_processes': 0,
            'new_processes': 0,
            'network_connections': 0,
            'suspicious_connections': 0
        }

    def _load_suspicious_patterns(self) -> List[str]:
        """Load suspicious process name patterns"""
        return [
            'nc', 'netcat', 'ncat',  # Netcat variants
            'nmap', 'masscan',  # Port scanners
            'metasploit', 'msfconsole', 'meterpreter',  # Metasploit
            'mimikatz', 'lazagne',  # Credential dumpers
            'powersploit', 'empire',  # Post-exploitation
            'keylogger', 'keylog',  # Keyloggers
            'backdoor', 'rootkit',  # Malware
            'ransomware', 'cryptolocker',  # Ransomware
            'miner', 'xmrig', 'cpuminer',  # Cryptocurrency miners
            'wget', 'curl', 'certutil',  # Downloaders (suspicious in some contexts)
            'psexec', 'wmic',  # Remote execution
            'reg.exe', 'regedit',  # Registry access
            'cmd.exe', 'powershell.exe'  # Command shells (monitor closely)
        ]

    def create_baseline(self):
        """Create baseline of running processes"""
        logger.info("Creating process baseline...")

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                self.baseline_processes.add(proc.info['name'].lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        logger.info(f"Baseline created: {len(self.baseline_processes)} unique processes")

    def scan_processes(self) -> List[Dict]:
        """
        Scan current processes

        Returns:
            List of alerts
        """
        logger.info("Scanning processes...")
        current_processes = set()
        alerts = []

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'create_time']):
            try:
                self.stats['processes_scanned'] += 1

                info = proc.info
                proc_name = info['name'].lower() if info['name'] else ''
                current_processes.add(proc_name)

                # Check for suspicious names
                if self._is_suspicious_process(proc_name, info.get('cmdline', [])):
                    alert = self._create_process_alert(proc)
                    alerts.append(alert)
                    self.stats['suspicious_processes'] += 1

                # Check for new processes
                if proc_name not in self.baseline_processes:
                    alert = self._create_new_process_alert(proc)
                    alerts.append(alert)
                    self.stats['new_processes'] += 1

                # Check for suspicious CPU/memory usage
                try:
                    cpu = proc.cpu_percent(interval=0.1)
                    mem = proc.memory_percent()

                    if cpu > 80 or mem > 50:
                        alert = {
                            'timestamp': datetime.now().isoformat(),
                            'type': 'HIGH_RESOURCE_USAGE',
                            'severity': 'MEDIUM',
                            'pid': info['pid'],
                            'name': info['name'],
                            'cpu_percent': cpu,
                            'memory_percent': mem,
                            'message': f"High resource usage: {info['name']} (CPU: {cpu}%, MEM: {mem}%)"
                        }
                        alerts.append(alert)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        self.alerts.extend(alerts)
        return alerts

    def _is_suspicious_process(self, proc_name: str, cmdline: List[str]) -> bool:
        """Check if process name or command line is suspicious"""
        # Check process name
        for pattern in self.suspicious_names:
            if pattern in proc_name:
                return True

        # Check command line arguments
        if cmdline:
            cmdline_str = ' '.join(cmdline).lower()
            suspicious_args = [
                '-e /bin/sh', '-e /bin/bash',  # Reverse shells
                'download', 'invoke-expression',  # PowerShell download/execute
                'base64', 'encoded',  # Obfuscation
                'exec', 'eval',  # Code execution
                'credential', 'password', 'hash'  # Credential access
            ]

            for arg in suspicious_args:
                if arg in cmdline_str:
                    return True

        return False

    def _create_process_alert(self, proc: psutil.Process) -> Dict:
        """Create alert for suspicious process"""
        try:
            info = proc.info
            alert = {
                'timestamp': datetime.now().isoformat(),
                'type': 'SUSPICIOUS_PROCESS',
                'severity': 'HIGH',
                'pid': info['pid'],
                'name': info['name'],
                'exe': info.get('exe', 'N/A'),
                'cmdline': ' '.join(info.get('cmdline', [])) if info.get('cmdline') else 'N/A',
                'username': info.get('username', 'N/A'),
                'message': f"Suspicious process detected: {info['name']}"
            }

            logger.error(f"[SUSPICIOUS PROCESS] PID: {info['pid']}, Name: {info['name']}")
            return alert

        except Exception as e:
            logger.error(f"Failed to create process alert: {e}")
            return {}

    def _create_new_process_alert(self, proc: psutil.Process) -> Dict:
        """Create alert for new process"""
        try:
            info = proc.info
            alert = {
                'timestamp': datetime.now().isoformat(),
                'type': 'NEW_PROCESS',
                'severity': 'LOW',
                'pid': info['pid'],
                'name': info['name'],
                'exe': info.get('exe', 'N/A'),
                'message': f"New process started: {info['name']}"
            }

            logger.info(f"[NEW PROCESS] PID: {info['pid']}, Name: {info['name']}")
            return alert

        except Exception as e:
            return {}

    def scan_network_connections(self) -> List[Dict]:
        """
        Scan network connections from processes

        Returns:
            List of suspicious connection alerts
        """
        logger.info("Scanning network connections...")
        alerts = []

        for conn in psutil.net_connections(kind='inet'):
            try:
                self.stats['network_connections'] += 1

                # Skip localhost connections
                if conn.laddr.ip == '127.0.0.1':
                    continue

                # Get process info
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        proc_name = proc.name()

                        # Check for suspicious connections
                        if self._is_suspicious_connection(conn, proc_name):
                            alert = {
                                'timestamp': datetime.now().isoformat(),
                                'type': 'SUSPICIOUS_CONNECTION',
                                'severity': 'HIGH',
                                'pid': conn.pid,
                                'process': proc_name,
                                'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}",
                                'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else 'N/A',
                                'status': conn.status,
                                'message': f"Suspicious connection: {proc_name} -> {conn.raddr.ip if conn.raddr else 'N/A'}"
                            }

                            alerts.append(alert)
                            self.stats['suspicious_connections'] += 1

                            logger.warning(f"[SUSPICIOUS CONNECTION] {proc_name} -> {conn.raddr.ip if conn.raddr else 'N/A'}")

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

            except Exception as e:
                continue

        self.alerts.extend(alerts)
        return alerts

    def _is_suspicious_connection(self, conn, proc_name: str) -> bool:
        """Check if network connection is suspicious"""
        # Suspicious ports
        suspicious_ports = [
            1337, 31337,  # Common backdoor ports
            4444, 4445,  # Metasploit
            5555, 5554,  # Android Debug Bridge
            6666, 6667,  # IRC (could be C&C)
            8000, 8080, 8888,  # Alternative HTTP (suspicious for some processes)
            9999, 10000  # Common backdoor ports
        ]

        # Check suspicious listening ports
        if conn.status == 'LISTEN' and conn.laddr.port in suspicious_ports:
            return True

        if conn.raddr:
            # Check remote port
            if conn.raddr.port in suspicious_ports:
                return True

        # Suspicious processes making connections
        suspicious_connecting = ['cmd.exe', 'powershell.exe', 'wscript.exe', 'cscript.exe']
        if proc_name.lower() in suspicious_connecting and conn.raddr:
            return True

        return False

    def get_running_processes_summary(self) -> Dict:
        """Get summary of running processes"""
        summary = {
            'total': 0,
            'by_user': {},
            'cpu_intensive': [],
            'memory_intensive': []
        }

        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                summary['total'] += 1

                # Count by user
                username = proc.info.get('username', 'Unknown')
                summary['by_user'][username] = summary['by_user'].get(username, 0) + 1

                # Track resource-intensive processes
                if proc.info['cpu_percent'] and proc.info['cpu_percent'] > 50:
                    summary['cpu_intensive'].append({
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent']
                    })

                if proc.info['memory_percent'] and proc.info['memory_percent'] > 10:
                    summary['memory_intensive'].append({
                        'name': proc.info['name'],
                        'memory': proc.info['memory_percent']
                    })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return summary

    def print_stats(self):
        """Print monitoring statistics"""
        print("\n" + "="*60)
        print("  Process Monitor Statistics")
        print("="*60)
        print(f"Processes Scanned:         {self.stats['processes_scanned']}")
        print(f"Suspicious Processes:      {self.stats['suspicious_processes']}")
        print(f"New Processes:             {self.stats['new_processes']}")
        print(f"Network Connections:       {self.stats['network_connections']}")
        print(f"Suspicious Connections:    {self.stats['suspicious_connections']}")
        print("="*60 + "\n")


def main():
    """Main function for standalone testing"""
    print("="*60)
    print("  HIDS - Process Monitor")
    print("="*60)
    print()

    monitor = ProcessMonitor()

    # Create baseline
    monitor.create_baseline()

    # Scan processes
    process_alerts = monitor.scan_processes()
    logger.info(f"Found {len(process_alerts)} process alerts")

    # Scan network connections
    connection_alerts = monitor.scan_network_connections()
    logger.info(f"Found {len(connection_alerts)} connection alerts")

    # Show summary
    summary = monitor.get_running_processes_summary()
    print("\nSystem Summary:")
    print(f"  Total processes: {summary['total']}")
    print(f"  CPU intensive: {len(summary['cpu_intensive'])}")
    print(f"  Memory intensive: {len(summary['memory_intensive'])}")

    # Show stats
    monitor.print_stats()

    logger.info("✓ Test completed successfully!")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
