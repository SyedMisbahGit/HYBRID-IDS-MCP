#!/usr/bin/env python3
"""
Log Analysis Engine for HIDS
Analyzes system logs for suspicious activities and security events
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Pattern
from collections import defaultdict
import platform

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class LogAnalyzer:
    """
    Analyzes system logs for security events and anomalies
    """

    def __init__(self):
        """Initialize Log Analyzer"""
        self.rules = self._load_detection_rules()
        self.alerts = []
        self.stats = {
            'logs_analyzed': 0,
            'events_detected': 0,
            'failed_logins': 0,
            'privilege_escalations': 0,
            'suspicious_commands': 0
        }
        self.failed_login_tracker = defaultdict(int)

    def _load_detection_rules(self) -> List[Dict]:
        """Load log analysis rules"""
        return [
            {
                'name': 'Failed Login Attempt',
                'pattern': r'(failed|failure|invalid) (login|password|authentication)',
                'severity': 'MEDIUM',
                'category': 'authentication',
                'action': self._track_failed_login
            },
            {
                'name': 'Successful Login After Failures',
                'pattern': r'(successful|accepted) (login|authentication)',
                'severity': 'HIGH',
                'category': 'authentication',
                'action': self._check_brute_force
            },
            {
                'name': 'Privilege Escalation',
                'pattern': r'(sudo|su|runas|elevation|administrator)',
                'severity': 'HIGH',
                'category': 'privilege_escalation'
            },
            {
                'name': 'Service Start/Stop',
                'pattern': r'(service|daemon) (started|stopped|failed)',
                'severity': 'MEDIUM',
                'category': 'service_change'
            },
            {
                'name': 'Firewall Rule Change',
                'pattern': r'(firewall|iptables|netsh) (add|delete|modify|rule)',
                'severity': 'HIGH',
                'category': 'firewall_change'
            },
            {
                'name': 'User Account Created',
                'pattern': r'(user|account) (created|added|new)',
                'severity': 'HIGH',
                'category': 'account_management'
            },
            {
                'name': 'User Account Deleted',
                'pattern': r'(user|account) (deleted|removed)',
                'severity': 'HIGH',
                'category': 'account_management'
            },
            {
                'name': 'Password Change',
                'pattern': r'password (changed|reset|modified)',
                'severity': 'MEDIUM',
                'category': 'account_management'
            },
            {
                'name': 'Suspicious Command',
                'pattern': r'(nc|netcat|nmap|metasploit|mimikatz|powersploit)',
                'severity': 'CRITICAL',
                'category': 'suspicious_activity'
            },
            {
                'name': 'File Access Denied',
                'pattern': r'(access denied|permission denied|unauthorized)',
                'severity': 'LOW',
                'category': 'access_control'
            },
            {
                'name': 'System Reboot',
                'pattern': r'(reboot|restart|shutdown)',
                'severity': 'MEDIUM',
                'category': 'system_change'
            },
            {
                'name': 'Kernel Module Loaded',
                'pattern': r'(module|driver) (loaded|inserted)',
                'severity': 'MEDIUM',
                'category': 'system_change'
            }
        ]

    def analyze_log_line(self, log_line: str, source: str = 'system') -> List[Dict]:
        """
        Analyze a single log line

        Args:
            log_line: Log line to analyze
            source: Source of the log (auth, system, security, etc.)

        Returns:
            List of detected events
        """
        self.stats['logs_analyzed'] += 1
        detected_events = []

        log_lower = log_line.lower()

        for rule in self.rules:
            if re.search(rule['pattern'], log_lower, re.IGNORECASE):
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'rule_name': rule['name'],
                    'severity': rule['severity'],
                    'category': rule['category'],
                    'log_source': source,
                    'log_line': log_line.strip(),
                    'detected_pattern': rule['pattern']
                }

                # Call custom action if defined
                if 'action' in rule:
                    rule['action'](log_line, event)

                detected_events.append(event)
                self.stats['events_detected'] += 1

                # Update category stats
                if rule['category'] == 'authentication':
                    self.stats['failed_logins'] += 1
                elif rule['category'] == 'privilege_escalation':
                    self.stats['privilege_escalations'] += 1
                elif rule['category'] == 'suspicious_activity':
                    self.stats['suspicious_commands'] += 1

                logger.warning(f"[{rule['severity']}] {rule['name']}: {log_line[:100]}")

        return detected_events

    def _track_failed_login(self, log_line: str, event: Dict):
        """Track failed login attempts"""
        # Extract username if possible
        username_match = re.search(r'user[:\s]+(\S+)', log_line, re.IGNORECASE)
        if username_match:
            username = username_match.group(1)
            self.failed_login_tracker[username] += 1
            event['username'] = username
            event['failed_attempts'] = self.failed_login_tracker[username]

    def _check_brute_force(self, log_line: str, event: Dict):
        """Check if successful login follows multiple failures"""
        username_match = re.search(r'user[:\s]+(\S+)', log_line, re.IGNORECASE)
        if username_match:
            username = username_match.group(1)
            failed_count = self.failed_login_tracker.get(username, 0)

            if failed_count >= 3:
                event['severity'] = 'CRITICAL'
                event['alert_type'] = 'POSSIBLE_BRUTE_FORCE'
                event['previous_failures'] = failed_count
                logger.critical(f"BRUTE FORCE SUSPECTED: {username} succeeded after {failed_count} failures")

            # Reset counter
            self.failed_login_tracker[username] = 0

    def analyze_log_file(self, filepath: str, source: str = 'system') -> List[Dict]:
        """
        Analyze entire log file

        Args:
            filepath: Path to log file
            source: Source of the log

        Returns:
            List of all detected events
        """
        logger.info(f"Analyzing log file: {filepath}")
        all_events = []

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    events = self.analyze_log_line(line, source)
                    all_events.extend(events)

        except Exception as e:
            logger.error(f"Failed to analyze {filepath}: {e}")

        logger.info(f"Found {len(all_events)} events in {filepath}")
        return all_events

    def analyze_windows_event_log(self, log_name: str = 'Security'):
        """
        Analyze Windows Event Log (requires pywin32 on Windows)

        Args:
            log_name: Event log name (Security, System, Application)
        """
        if platform.system() != 'Windows':
            logger.warning("Windows Event Log analysis only available on Windows")
            return []

        try:
            import win32evtlog
            import win32evtlogutil

            events = []
            hand = win32evtlog.OpenEventLog(None, log_name)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

            total = 0
            while True:
                records = win32evtlog.ReadEventLog(hand, flags, 0)
                if not records:
                    break

                for record in records:
                    total += 1
                    # Process event record
                    msg = win32evtlogutil.SafeFormatMessage(record, log_name)
                    if msg:
                        detected = self.analyze_log_line(msg, f'Windows_{log_name}')
                        events.extend(detected)

                    # Limit to recent events
                    if total >= 1000:
                        break

                if total >= 1000:
                    break

            win32evtlog.CloseEventLog(hand)
            return events

        except ImportError:
            logger.error("pywin32 not installed. Install with: pip install pywin32")
            return []
        except Exception as e:
            logger.error(f"Failed to read Windows Event Log: {e}")
            return []

    def get_summary_report(self) -> str:
        """Generate summary report"""
        report = []
        report.append("\n" + "="*60)
        report.append("  HIDS Log Analysis Summary")
        report.append("="*60)
        report.append(f"Logs Analyzed:           {self.stats['logs_analyzed']}")
        report.append(f"Events Detected:         {self.stats['events_detected']}")
        report.append(f"Failed Logins:           {self.stats['failed_logins']}")
        report.append(f"Privilege Escalations:   {self.stats['privilege_escalations']}")
        report.append(f"Suspicious Commands:     {self.stats['suspicious_commands']}")
        report.append("\nTop Failed Login Users:")

        # Sort by failed attempts
        sorted_users = sorted(
            self.failed_login_tracker.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        for username, count in sorted_users:
            report.append(f"  {username}: {count} attempts")

        report.append("="*60 + "\n")

        return "\n".join(report)


def main():
    """Main function for standalone testing"""
    print("="*60)
    print("  HIDS - Log Analyzer")
    print("="*60)
    print()

    analyzer = LogAnalyzer()

    # Create test log entries
    test_logs = [
        "2025-10-18 10:15:23 auth: Failed login attempt for user admin from 192.168.1.100",
        "2025-10-18 10:15:45 auth: Failed login attempt for user admin from 192.168.1.100",
        "2025-10-18 10:16:12 auth: Failed login attempt for user admin from 192.168.1.100",
        "2025-10-18 10:16:30 auth: Successful login for user admin from 192.168.1.100",
        "2025-10-18 10:17:00 sudo: admin : TTY=pts/0 ; USER=root ; COMMAND=/bin/bash",
        "2025-10-18 10:18:15 firewall: New rule added: ALLOW port 4444",
        "2025-10-18 10:19:00 system: Service sshd started",
        "2025-10-18 10:20:30 security: User account 'backdoor' created",
        "2025-10-18 10:21:45 cmd: nc -l -p 1337 executed",
        "2025-10-18 10:22:00 auth: Password changed for user root"
    ]

    logger.info("Analyzing test log entries...")
    print()

    all_events = []
    for log in test_logs:
        events = analyzer.analyze_log_line(log, 'test')
        all_events.extend(events)

    print()
    print(analyzer.get_summary_report())

    logger.info(f"✓ Detected {len(all_events)} security events")
    logger.info("✓ Test completed successfully!")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
