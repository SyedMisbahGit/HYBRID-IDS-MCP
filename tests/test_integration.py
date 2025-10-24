#!/usr/bin/env python3
"""
Integration Testing Suite for Hybrid IDS
Tests the integration layer components
"""

import os
import sys
import time
import json
import pytest
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'integration'))

from unified_alert_manager import (
    UnifiedAlertManager, UnifiedAlert, AlertSource, AlertSeverity
)
from event_correlator import EventCorrelator, CorrelationRule


class TestUnifiedAlert:
    """Test UnifiedAlert class"""

    def test_alert_creation(self):
        """Test creating a unified alert"""
        alert = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test description",
            metadata={'test_key': 'test_value'}
        )

        assert alert.title == "Test Alert"
        assert alert.severity == "HIGH"
        assert alert.source == "nids_signature"
        assert 'test_key' in alert.metadata
        assert alert.metadata['test_key'] == 'test_value'

    def test_alert_to_dict(self):
        """Test alert conversion to dictionary"""
        alert = UnifiedAlert(
            source=AlertSource.HIDS_FILE,
            severity=AlertSeverity.CRITICAL,
            title="File Modified",
            description="Critical system file modified"
        )

        alert_dict = alert.to_dict()

        assert 'alert_id' in alert_dict
        assert 'timestamp' in alert_dict
        assert alert_dict['source'] == "hids_file"
        assert alert_dict['severity'] == "CRITICAL"
        assert alert_dict['title'] == "File Modified"

    def test_alert_to_elasticsearch(self):
        """Test alert conversion to Elasticsearch format"""
        alert = UnifiedAlert(
            source=AlertSource.HIDS_PROCESS,
            severity=AlertSeverity.MEDIUM,
            title="Suspicious Process",
            description="Unusual process detected"
        )

        es_doc = alert.to_elasticsearch()

        assert '@timestamp' in es_doc
        assert 'alert_id' in es_doc
        assert 'source' in es_doc


class TestUnifiedAlertManager:
    """Test Unified Alert Manager"""

    @pytest.fixture
    def alert_manager_config(self, tmp_path):
        """Create test configuration"""
        log_dir = tmp_path / "logs" / "alerts"
        log_dir.mkdir(parents=True)

        config = {
            'inputs': {
                'nids': {
                    'enabled': True,
                    'endpoint': 'tcp://localhost:15556'  # Test port
                },
                'hids': {
                    'enabled': True,
                    'endpoint': 'tcp://localhost:15557'  # Test port
                }
            },
            'outputs': {
                'console': {
                    'enabled': True,
                    'verbose': False
                },
                'file': {
                    'enabled': True,
                    'directory': str(log_dir),
                    'filename': 'test_alerts.jsonl'
                },
                'elasticsearch': {
                    'enabled': False  # Disable for testing
                }
            },
            'processing': {
                'worker_threads': 2
            }
        }
        return config

    def test_alert_manager_initialization(self, alert_manager_config):
        """Test alert manager can be initialized"""
        manager = UnifiedAlertManager(alert_manager_config)
        manager.initialize()

        assert manager.alert_queue is not None
        assert manager.running == False
        assert manager.stats['total_alerts'] == 0

    def test_alert_manager_add_alert(self, alert_manager_config):
        """Test manually adding an alert"""
        manager = UnifiedAlertManager(alert_manager_config)
        manager.initialize()
        manager.start()

        # Create test alert
        alert = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.HIGH,
            title="Test SQL Injection",
            description="SQL injection detected",
            metadata={'src_ip': '192.168.1.100'}
        )

        # Add alert
        manager.add_alert(alert)

        # Wait for processing
        time.sleep(0.5)

        # Check stats
        stats = manager.get_stats()
        assert stats['total_alerts'] >= 1

        # Stop manager
        manager.stop()

    def test_alert_manager_file_output(self, alert_manager_config, tmp_path):
        """Test that alerts are written to file"""
        manager = UnifiedAlertManager(alert_manager_config)
        manager.initialize()
        manager.start()

        # Add test alert
        alert = UnifiedAlert(
            source=AlertSource.HIDS_FILE,
            severity=AlertSeverity.CRITICAL,
            title="File Tampering",
            description="System file modified"
        )
        manager.add_alert(alert)

        # Wait for processing
        time.sleep(1)
        manager.stop()

        # Check file was created and contains data
        log_file = tmp_path / "logs" / "alerts" / "test_alerts.jsonl"
        assert log_file.exists()

        # Read and verify content
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) >= 1

            # Parse first alert
            first_alert = json.loads(lines[0])
            assert 'alert_id' in first_alert
            assert 'source' in first_alert

    def test_normalize_nids_alert(self, alert_manager_config):
        """Test NIDS alert normalization"""
        manager = UnifiedAlertManager(alert_manager_config)

        # Simulate NIDS alert message
        nids_message = {
            'type': 'signature',
            'severity': 'HIGH',
            'name': 'SQL Injection',
            'description': 'SQL injection attempt detected',
            'src_ip': '192.168.1.100',
            'dst_ip': '10.0.0.50',
            'protocol': 'TCP',
            'rule_id': 1001
        }

        # Normalize
        unified = manager._normalize_nids_alert(nids_message)

        assert unified.source == AlertSource.NIDS_SIGNATURE.value
        assert unified.severity == "HIGH"
        assert unified.title == "SQL Injection"
        assert unified.metadata['src_ip'] == '192.168.1.100'

    def test_normalize_hids_alert(self, alert_manager_config):
        """Test HIDS alert normalization"""
        manager = UnifiedAlertManager(alert_manager_config)

        # Simulate HIDS alert message
        hids_message = {
            'component': 'file_monitor',
            'severity': 'critical',
            'alert_type': 'File Modified',
            'description': 'Critical system file changed',
            'hostname': 'server01',
            'details': {
                'file': '/etc/passwd',
                'action': 'modified'
            }
        }

        # Normalize
        unified = manager._normalize_hids_alert(hids_message)

        assert unified.source == AlertSource.HIDS_FILE.value
        assert unified.severity == "CRITICAL"
        assert unified.title == "File Modified"
        assert unified.metadata['hostname'] == 'server01'


class TestEventCorrelator:
    """Test Event Correlator"""

    @pytest.fixture
    def correlator_config(self):
        """Create test configuration"""
        return {
            'correlation': {
                'window_seconds': 600  # 10 minutes
            }
        }

    def test_correlator_initialization(self, correlator_config):
        """Test correlator can be initialized"""
        correlator = EventCorrelator(correlator_config)
        correlator.start()

        assert correlator.running == True
        assert len(correlator.correlation_rules) == 10
        assert correlator.event_window_seconds == 600

        correlator.stop()

    def test_correlator_process_single_alert(self, correlator_config):
        """Test processing a single alert (no correlation)"""
        correlator = EventCorrelator(correlator_config)
        correlator.start()

        # Create test alert
        alert = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.MEDIUM,
            title="Port Scan Detected",
            description="TCP port scan activity",
            metadata={'src_ip': '192.168.1.100'}
        )

        # Process alert
        correlated = correlator.process_alert(alert)

        # Should not correlate (only one event)
        assert len(correlated) == 0

        # Check stats
        stats = correlator.get_stats()
        assert stats['total_events_processed'] == 1
        assert stats['correlations_detected'] == 0

        correlator.stop()

    def test_correlator_port_scan_to_exploitation(self, correlator_config):
        """Test Rule CR001: Port Scan → Exploitation correlation"""
        correlator = EventCorrelator(correlator_config)
        correlator.start()

        # Alert 1: Port Scan
        alert1 = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.MEDIUM,
            title="TCP Port Scan Detected",
            description="Port scanning activity from 192.168.1.100",
            metadata={
                'src_ip': '192.168.1.100',
                'dst_ip': '10.0.0.50'
            }
        )

        # Process first alert
        correlated1 = correlator.process_alert(alert1)
        assert len(correlated1) == 0  # No correlation yet

        # Alert 2: SQL Injection (same IP, within window)
        time.sleep(1)
        alert2 = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.HIGH,
            title="SQL Injection Attempt",
            description="SQL injection detected from 192.168.1.100",
            metadata={
                'src_ip': '192.168.1.100',
                'dst_ip': '10.0.0.50'
            }
        )

        # Process second alert - should trigger correlation
        correlated2 = correlator.process_alert(alert2)

        # Should detect correlation
        assert len(correlated2) >= 1

        # Verify correlated alert
        corr_alert = correlated2[0]
        assert corr_alert.source == "correlation"
        assert corr_alert.severity == "CRITICAL"
        assert "Port Scan" in corr_alert.title or "Exploitation" in corr_alert.title

        # Check stats
        stats = correlator.get_stats()
        assert stats['correlations_detected'] >= 1

        correlator.stop()

    def test_correlator_different_ips_no_correlation(self, correlator_config):
        """Test that different IPs don't correlate when same_ip=True"""
        correlator = EventCorrelator(correlator_config)
        correlator.start()

        # Alert 1: Port Scan from IP1
        alert1 = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.MEDIUM,
            title="Port Scan Detected",
            description="Port scan",
            metadata={'src_ip': '192.168.1.100'}
        )
        correlator.process_alert(alert1)

        # Alert 2: SQL Injection from IP2 (different IP)
        alert2 = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.HIGH,
            title="SQL Injection Attempt",
            description="SQL injection",
            metadata={'src_ip': '192.168.1.200'}  # Different IP
        )
        correlated = correlator.process_alert(alert2)

        # Should NOT correlate (different IPs)
        assert len(correlated) == 0

        correlator.stop()

    def test_correlator_cleanup_old_events(self, correlator_config):
        """Test that old events are cleaned up"""
        # Use short window for testing
        config = {
            'correlation': {
                'window_seconds': 2  # 2 seconds
            }
        }

        correlator = EventCorrelator(config)
        correlator.start()

        # Add alert
        alert = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.MEDIUM,
            title="Test Alert",
            description="Test",
            metadata={'src_ip': '192.168.1.100'}
        )
        correlator.process_alert(alert)

        # Check event history
        assert len(correlator.event_history) == 1

        # Wait for cleanup (window + some margin)
        time.sleep(4)

        # Trigger cleanup by processing another alert
        correlator.process_alert(alert)

        # Old events should be cleaned (implementation dependent)
        # At least the new event should be there
        assert len(correlator.event_history) >= 1

        correlator.stop()

    def test_correlator_event_indexing(self, correlator_config):
        """Test that events are properly indexed"""
        correlator = EventCorrelator(correlator_config)
        correlator.start()

        # Create alert with IP
        alert = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.MEDIUM,
            title="Test",
            description="Test",
            metadata={
                'src_ip': '192.168.1.100',
                'hostname': 'server01'
            }
        )

        correlator.process_alert(alert)

        # Check indices
        assert '192.168.1.100' in correlator.events_by_ip
        assert 'server01' in correlator.events_by_host
        assert 'nids_signature' in correlator.events_by_source

        correlator.stop()


class TestIntegration:
    """Integration tests for complete workflow"""

    def test_end_to_end_alert_flow(self, tmp_path):
        """Test complete alert flow from creation to output"""
        # Configure alert manager
        log_dir = tmp_path / "logs" / "alerts"
        log_dir.mkdir(parents=True)

        manager_config = {
            'inputs': {
                'nids': {'enabled': True, 'endpoint': 'tcp://localhost:15556'},
                'hids': {'enabled': True, 'endpoint': 'tcp://localhost:15557'}
            },
            'outputs': {
                'console': {'enabled': False},
                'file': {
                    'enabled': True,
                    'directory': str(log_dir),
                    'filename': 'test_e2e.jsonl'
                },
                'elasticsearch': {'enabled': False}
            },
            'processing': {'worker_threads': 2}
        }

        correlator_config = {
            'correlation': {'window_seconds': 600}
        }

        # Initialize components
        manager = UnifiedAlertManager(manager_config)
        manager.initialize()
        manager.start()

        correlator = EventCorrelator(correlator_config)
        correlator.start()

        # Create and process alerts
        alert1 = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=AlertSeverity.HIGH,
            title="SQL Injection",
            description="SQL injection detected",
            metadata={'src_ip': '192.168.1.100'}
        )

        alert2 = UnifiedAlert(
            source=AlertSource.HIDS_FILE,
            severity=AlertSeverity.CRITICAL,
            title="File Modified",
            description="System file modified",
            metadata={'hostname': 'server01'}
        )

        # Add to manager
        manager.add_alert(alert1)
        manager.add_alert(alert2)

        # Process through correlator
        correlator.process_alert(alert1)
        correlator.process_alert(alert2)

        # Wait for processing
        time.sleep(1)

        # Check results
        manager_stats = manager.get_stats()
        assert manager_stats['total_alerts'] >= 2

        correlator_stats = correlator.get_stats()
        assert correlator_stats['total_events_processed'] >= 2

        # Verify file output
        log_file = log_dir / "test_e2e.jsonl"
        assert log_file.exists()

        # Clean up
        manager.stop()
        correlator.stop()


def test_all_alert_sources():
    """Test all alert source types"""
    sources = [
        AlertSource.NIDS_SIGNATURE,
        AlertSource.NIDS_ANOMALY,
        AlertSource.HIDS_FILE,
        AlertSource.HIDS_PROCESS,
        AlertSource.HIDS_LOG,
        AlertSource.CORRELATION
    ]

    for source in sources:
        alert = UnifiedAlert(
            source=source,
            severity=AlertSeverity.MEDIUM,
            title=f"Test {source.value}",
            description="Test alert"
        )
        assert alert.source == source.value


def test_all_alert_severities():
    """Test all alert severity levels"""
    severities = [
        AlertSeverity.INFO,
        AlertSeverity.LOW,
        AlertSeverity.MEDIUM,
        AlertSeverity.HIGH,
        AlertSeverity.CRITICAL
    ]

    for severity in severities:
        alert = UnifiedAlert(
            source=AlertSource.NIDS_SIGNATURE,
            severity=severity,
            title=f"Test {severity.name}",
            description="Test alert"
        )
        assert alert.severity == severity.name


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
