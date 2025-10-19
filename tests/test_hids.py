#!/usr/bin/env python3
"""
Comprehensive Test Suite for HIDS Components
Tests file monitoring, log analysis, and process monitoring
"""

import os
import sys
import time
import unittest
from pathlib import Path
import tempfile
import shutil
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'hids'))

from file_monitor import FileIntegrityMonitor
from log_analyzer import LogAnalyzer
from process_monitor import ProcessMonitor


class TestFileIntegrityMonitor(unittest.TestCase):
    """Test File Integrity Monitoring"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.monitor = FileIntegrityMonitor()
        self.monitor.config['monitored_paths'] = [str(self.test_dir)]
        self.monitor.config['file_extensions'] = ['.txt', '.conf', '.exe']

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_create_baseline(self):
        """Test baseline creation"""
        # Create test files
        (self.test_dir / 'file1.txt').write_text('Content 1')
        (self.test_dir / 'file2.txt').write_text('Content 2')
        (self.test_dir / 'config.conf').write_text('setting=value')

        # Create baseline
        self.monitor.create_baseline()

        # Verify baseline
        self.assertEqual(len(self.monitor.baseline), 3)
        self.assertIn(str(self.test_dir / 'file1.txt'), self.monitor.baseline)

    def test_hash_calculation(self):
        """Test file hash calculation"""
        test_file = self.test_dir / 'test.txt'
        test_file.write_text('Test content')

        hash1 = self.monitor.calculate_hash(str(test_file))
        self.assertIsNotNone(hash1)
        self.assertEqual(len(hash1), 64)  # SHA256 is 64 hex chars

        # Hash should be consistent
        hash2 = self.monitor.calculate_hash(str(test_file))
        self.assertEqual(hash1, hash2)

    def test_detect_new_file(self):
        """Test detection of new files"""
        # Create baseline with one file
        (self.test_dir / 'file1.txt').write_text('Content 1')
        self.monitor.create_baseline()

        # Add new file
        (self.test_dir / 'new_file.txt').write_text('New content')

        # Check integrity
        self.monitor.check_integrity()

        # Verify alert
        self.assertEqual(self.monitor.stats['new_files'], 1)
        self.assertGreater(len(self.monitor.alerts), 0)
        self.assertEqual(self.monitor.alerts[0]['type'], 'NEW_FILE')

    def test_detect_modified_file(self):
        """Test detection of modified files"""
        # Create baseline
        test_file = self.test_dir / 'file1.txt'
        test_file.write_text('Original content')
        self.monitor.create_baseline()

        # Modify file
        time.sleep(0.1)
        test_file.write_text('Modified content')

        # Check integrity
        self.monitor.check_integrity()

        # Verify alert
        self.assertEqual(self.monitor.stats['modified_files'], 1)
        modified_alerts = [a for a in self.monitor.alerts if a['type'] == 'MODIFIED_FILE']
        self.assertGreater(len(modified_alerts), 0)

    def test_detect_deleted_file(self):
        """Test detection of deleted files"""
        # Create baseline
        test_file = self.test_dir / 'file1.txt'
        test_file.write_text('Content')
        self.monitor.create_baseline()

        # Delete file
        test_file.unlink()

        # Check integrity
        self.monitor.check_integrity()

        # Verify alert
        self.assertEqual(self.monitor.stats['deleted_files'], 1)
        deleted_alerts = [a for a in self.monitor.alerts if a['type'] == 'DELETED_FILE']
        self.assertGreater(len(deleted_alerts), 0)

    def test_save_load_baseline(self):
        """Test baseline persistence"""
        # Create baseline
        (self.test_dir / 'file1.txt').write_text('Content 1')
        self.monitor.create_baseline()

        # Save baseline
        baseline_file = self.test_dir / 'baseline.json'
        self.monitor.save_baseline(str(baseline_file))

        # Create new monitor and load
        monitor2 = FileIntegrityMonitor()
        monitor2.load_baseline(str(baseline_file))

        # Verify
        self.assertEqual(len(monitor2.baseline), len(self.monitor.baseline))


class TestLogAnalyzer(unittest.TestCase):
    """Test Log Analysis Engine"""

    def setUp(self):
        """Set up test environment"""
        self.analyzer = LogAnalyzer()

    def test_failed_login_detection(self):
        """Test failed login detection"""
        log_line = "2025-10-18 10:15:23 auth: Failed login attempt for user admin"
        events = self.analyzer.analyze_log_line(log_line, 'auth')

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['rule_name'], 'Failed Login Attempt')
        self.assertEqual(events[0]['severity'], 'MEDIUM')

    def test_brute_force_detection(self):
        """Test brute force detection"""
        # Simulate multiple failed logins
        for i in range(3):
            log = f"2025-10-18 10:15:{i:02d} auth: Failed login attempt for user admin"
            self.analyzer.analyze_log_line(log, 'auth')

        # Successful login after failures
        log = "2025-10-18 10:16:00 auth: Successful login for user admin"
        events = self.analyzer.analyze_log_line(log, 'auth')

        # Should detect brute force
        brute_force = [e for e in events if e.get('alert_type') == 'POSSIBLE_BRUTE_FORCE']
        self.assertGreater(len(brute_force), 0)
        self.assertEqual(brute_force[0]['severity'], 'CRITICAL')

    def test_privilege_escalation_detection(self):
        """Test privilege escalation detection"""
        log_line = "2025-10-18 10:17:00 sudo: admin : TTY=pts/0 ; USER=root ; COMMAND=/bin/bash"
        events = self.analyzer.analyze_log_line(log_line, 'system')

        self.assertGreater(len(events), 0)
        self.assertEqual(events[0]['category'], 'privilege_escalation')
        self.assertEqual(events[0]['severity'], 'HIGH')

    def test_suspicious_command_detection(self):
        """Test suspicious command detection"""
        log_line = "2025-10-18 10:21:45 cmd: nc -l -p 1337 executed"
        events = self.analyzer.analyze_log_line(log_line, 'system')

        self.assertGreater(len(events), 0)
        suspicious = [e for e in events if e['category'] == 'suspicious_activity']
        self.assertGreater(len(suspicious), 0)
        self.assertEqual(suspicious[0]['severity'], 'CRITICAL')

    def test_account_management_detection(self):
        """Test account management detection"""
        # Pattern requires: (user|account) (created|added|new)
        log_line = "2025-10-18 10:20:30 security: user account created for backdoor"
        events = self.analyzer.analyze_log_line(log_line, 'security')

        self.assertGreater(len(events), 0)
        account_events = [e for e in events if e['category'] == 'account_management']
        self.assertGreater(len(account_events), 0)

    def test_log_file_analysis(self):
        """Test log file analysis"""
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("2025-10-18 10:15:23 Failed login for user admin\n")
            f.write("2025-10-18 10:16:45 sudo command executed\n")
            f.write("2025-10-18 10:17:30 Service ssh started\n")
            log_file = f.name

        try:
            events = self.analyzer.analyze_log_file(log_file, 'test')
            self.assertGreater(len(events), 0)
        finally:
            os.unlink(log_file)


class TestProcessMonitor(unittest.TestCase):
    """Test Process Monitoring"""

    def setUp(self):
        """Set up test environment"""
        self.monitor = ProcessMonitor()

    def test_create_baseline(self):
        """Test process baseline creation"""
        self.monitor.create_baseline()
        self.assertGreater(len(self.monitor.baseline_processes), 0)

    def test_suspicious_process_detection(self):
        """Test suspicious process name detection"""
        # Test suspicious patterns
        self.assertTrue(self.monitor._is_suspicious_process('nc', []))
        self.assertTrue(self.monitor._is_suspicious_process('netcat', []))
        self.assertTrue(self.monitor._is_suspicious_process('mimikatz.exe', []))

        # Test legitimate process
        self.assertFalse(self.monitor._is_suspicious_process('chrome.exe', []))

    def test_suspicious_command_line(self):
        """Test suspicious command line detection"""
        # Suspicious command line
        cmdline = ['powershell.exe', '-e', 'base64encodedcommand']
        self.assertTrue(self.monitor._is_suspicious_process('powershell.exe', cmdline))

        # Normal command line
        cmdline = ['python.exe', 'script.py']
        self.assertFalse(self.monitor._is_suspicious_process('python.exe', cmdline))

    def test_process_scan(self):
        """Test process scanning"""
        self.monitor.create_baseline()
        alerts = self.monitor.scan_processes()

        # Should return a list (may be empty if no suspicious processes)
        self.assertIsInstance(alerts, list)

    def test_network_connection_scan(self):
        """Test network connection scanning"""
        alerts = self.monitor.scan_network_connections()

        # Should return a list
        self.assertIsInstance(alerts, list)

    def test_suspicious_port_detection(self):
        """Test suspicious port detection logic"""
        # Mock connection object
        class MockAddr:
            def __init__(self, ip, port):
                self.ip = ip
                self.port = port

        class MockConnection:
            def __init__(self, local_port, remote_port, status):
                self.laddr = MockAddr('192.168.1.10', local_port)
                self.raddr = MockAddr('10.0.0.1', remote_port) if remote_port else None
                self.status = status

        # Test suspicious remote port
        conn = MockConnection(50000, 4444, 'ESTABLISHED')
        self.assertTrue(self.monitor._is_suspicious_connection(conn, 'python.exe'))

        # Test suspicious listening port
        conn = MockConnection(1337, None, 'LISTEN')
        self.assertTrue(self.monitor._is_suspicious_connection(conn, 'python.exe'))

        # Test normal connection
        conn = MockConnection(50000, 443, 'ESTABLISHED')
        self.assertFalse(self.monitor._is_suspicious_connection(conn, 'chrome.exe'))


class TestHIDSIntegration(unittest.TestCase):
    """Integration tests for HIDS components"""

    def test_alert_format_consistency(self):
        """Test that all components produce consistent alert formats"""
        # File monitor alert
        monitor = FileIntegrityMonitor()
        test_dir = Path(tempfile.mkdtemp())
        monitor.config['monitored_paths'] = [str(test_dir)]
        (test_dir / 'test.txt').write_text('content')
        monitor.create_baseline()
        (test_dir / 'new.txt').write_text('new')
        monitor.check_integrity()

        if monitor.alerts:
            alert = monitor.alerts[0]
            self.assertIn('timestamp', alert)
            self.assertIn('type', alert)
            self.assertIn('severity', alert)
            self.assertIn('message', alert)

        shutil.rmtree(test_dir)

        # Log analyzer alert
        analyzer = LogAnalyzer()
        events = analyzer.analyze_log_line("Failed login for user test", 'auth')

        if events:
            alert = events[0]
            self.assertIn('timestamp', alert)
            self.assertIn('severity', alert)
            self.assertIn('category', alert)

        # Process monitor alert
        proc_monitor = ProcessMonitor()
        proc_monitor.create_baseline()
        # Process alerts tested in scan

    def test_statistics_tracking(self):
        """Test that all components track statistics properly"""
        # File monitor
        monitor = FileIntegrityMonitor()
        test_dir = Path(tempfile.mkdtemp())
        monitor.config['monitored_paths'] = [str(test_dir)]
        (test_dir / 'test.txt').write_text('content')
        monitor.create_baseline()

        stats = monitor.get_stats()
        self.assertIn('files_monitored', stats)
        self.assertIn('changes_detected', stats)

        shutil.rmtree(test_dir)

        # Log analyzer
        analyzer = LogAnalyzer()
        analyzer.analyze_log_line("Test log line", 'test')
        self.assertGreater(analyzer.stats['logs_analyzed'], 0)

        # Process monitor
        proc_monitor = ProcessMonitor()
        self.assertIn('processes_scanned', proc_monitor.stats)


def run_tests():
    """Run all tests"""
    print("="*60)
    print("  HIDS Component Test Suite")
    print("="*60)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFileIntegrityMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestLogAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestHIDSIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("="*60)
    print("  Test Summary")
    print("="*60)
    print(f"Tests Run:     {result.testsRun}")
    print(f"Successes:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:      {len(result.failures)}")
    print(f"Errors:        {len(result.errors)}")
    print("="*60)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
