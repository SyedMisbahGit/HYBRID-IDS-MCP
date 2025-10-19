#!/usr/bin/env python3
"""
Hybrid IDS Main Controller
Integrates NIDS and HIDS components into a unified intrusion detection system
"""

import os
import sys
import signal
import logging
import time
import threading
import yaml
from pathlib import Path
from typing import Dict, Optional

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / 'hids'))

# Import HIDS components
from hids.hids_main import HIDS

# Import integration components
from unified_alert_manager import UnifiedAlertManager, UnifiedAlert
from event_correlator import EventCorrelator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HybridIDS:
    """
    Main controller for Hybrid IDS
    Orchestrates NIDS, HIDS, alert management, and event correlation
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = {}
        self.running = False

        # Components
        self.hids = None
        self.alert_manager = None
        self.correlator = None

        # NIDS process (external C++ process)
        self.nids_process = None

        # Statistics
        self.stats = {
            'start_time': None,
            'total_alerts': 0,
            'hids_alerts': 0,
            'nids_alerts': 0,
            'correlated_alerts': 0
        }

        # Threading
        self.hids_thread = None
        self.stats_thread = None

    def load_config(self):
        """Load configuration from YAML file"""
        logger.info(f"Loading configuration from {self.config_path}")

        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)

            logger.info("Configuration loaded successfully")
            return True

        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return False
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False

    def initialize(self):
        """Initialize all IDS components"""
        logger.info("=" * 70)
        logger.info("  HYBRID IDS - Network and Host Intrusion Detection System")
        logger.info("=" * 70)

        # Load configuration
        if not self.load_config():
            logger.error("Failed to load configuration")
            return False

        # Initialize Alert Manager
        if not self._init_alert_manager():
            logger.error("Failed to initialize Alert Manager")
            return False

        # Initialize Event Correlator
        if not self._init_correlator():
            logger.error("Failed to initialize Event Correlator")
            return False

        # Initialize HIDS
        if self.config.get('hids', {}).get('enabled', True):
            if not self._init_hids():
                logger.warning("Failed to initialize HIDS - continuing without HIDS")
        else:
            logger.info("HIDS disabled in configuration")

        # NIDS is managed externally (C++ process)
        if self.config.get('nids', {}).get('enabled', True):
            logger.info("NIDS should be started separately (C++ process)")
            logger.info("  Run: ./build/sids -i <interface>")
            logger.info("  Or:  ./scripts/start_nids.sh")
        else:
            logger.info("NIDS disabled in configuration")

        logger.info("\n" + "=" * 70)
        logger.info("  Hybrid IDS initialized successfully")
        logger.info("=" * 70)

        return True

    def _init_alert_manager(self) -> bool:
        """Initialize the unified alert manager"""
        try:
            logger.info("Initializing Unified Alert Manager...")

            alert_config = self.config.get('alert_manager', {})
            self.alert_manager = UnifiedAlertManager(alert_config)
            self.alert_manager.initialize()

            logger.info("Alert Manager initialized")
            return True

        except Exception as e:
            logger.error(f"Error initializing Alert Manager: {e}")
            return False

    def _init_correlator(self) -> bool:
        """Initialize the event correlator"""
        try:
            logger.info("Initializing Event Correlator...")

            self.correlator = EventCorrelator(self.config)

            logger.info("Event Correlator initialized")
            return True

        except Exception as e:
            logger.error(f"Error initializing Event Correlator: {e}")
            return False

    def _init_hids(self) -> bool:
        """Initialize Host-based IDS"""
        try:
            logger.info("Initializing HIDS...")

            # Get HIDS config path
            hids_config_path = self.config.get('hids', {}).get('config_path')

            if not hids_config_path:
                # Use default path
                hids_config_path = str(Path(__file__).parent.parent.parent / 'config' / 'hids' / 'hids_config.yaml')

            # Create HIDS instance
            self.hids = HIDS(hids_config_path)

            # Override alert callback to integrate with our alert manager
            original_send_alert = self.hids._send_alert

            def integrated_alert_callback(alert_type, severity, description, details):
                # Call original handler
                original_send_alert(alert_type, severity, description, details)

                # Send to our alert manager
                self._handle_hids_alert(alert_type, severity, description, details)

            self.hids._send_alert = integrated_alert_callback

            logger.info("HIDS initialized")
            return True

        except Exception as e:
            logger.error(f"Error initializing HIDS: {e}")
            return False

    def _handle_hids_alert(self, alert_type: str, severity: str, description: str, details: Dict):
        """Handle HIDS alert and forward to alert manager"""
        try:
            # Determine source based on alert type
            from unified_alert_manager import AlertSource, AlertSeverity

            if 'file' in alert_type.lower():
                source = AlertSource.HIDS_FILE
            elif 'process' in alert_type.lower():
                source = AlertSource.HIDS_PROCESS
            elif 'log' in alert_type.lower():
                source = AlertSource.HIDS_LOG
            else:
                source = AlertSource.HIDS_PROCESS

            # Map severity
            severity_map = {
                'info': AlertSeverity.INFO,
                'low': AlertSeverity.LOW,
                'medium': AlertSeverity.MEDIUM,
                'high': AlertSeverity.HIGH,
                'critical': AlertSeverity.CRITICAL
            }
            alert_severity = severity_map.get(severity.lower(), AlertSeverity.MEDIUM)

            # Create unified alert
            alert = UnifiedAlert(
                source=source,
                severity=alert_severity,
                title=alert_type,
                description=description,
                metadata={
                    'component': 'hids',
                    'details': details,
                    'hostname': os.uname().nodename if hasattr(os, 'uname') else 'windows-host'
                }
            )

            # Send to alert manager
            self.alert_manager.add_alert(alert)

            # Check for correlations
            correlated = self.correlator.process_alert(alert)
            if correlated:
                for corr_alert in correlated:
                    self.alert_manager.add_alert(corr_alert)
                    self.stats['correlated_alerts'] += len(correlated)

            # Update statistics
            self.stats['hids_alerts'] += 1
            self.stats['total_alerts'] += 1

        except Exception as e:
            logger.error(f"Error handling HIDS alert: {e}")

    def start(self):
        """Start the Hybrid IDS"""
        logger.info("\nStarting Hybrid IDS...")
        self.running = True
        self.stats['start_time'] = time.time()

        # Start Alert Manager
        if self.alert_manager:
            self.alert_manager.start()

        # Start Event Correlator
        if self.correlator:
            self.correlator.start()

        # Start HIDS in separate thread
        if self.hids:
            self.hids_thread = threading.Thread(
                target=self._run_hids,
                daemon=True
            )
            self.hids_thread.start()
            logger.info("HIDS started in background thread")

        # Start statistics reporting thread
        self.stats_thread = threading.Thread(
            target=self._stats_reporter,
            daemon=True
        )
        self.stats_thread.start()

        logger.info("\n" + "=" * 70)
        logger.info("  Hybrid IDS is now running")
        logger.info("=" * 70)
        logger.info("\nPress Ctrl+C to stop\n")

    def _run_hids(self):
        """Run HIDS in separate thread"""
        try:
            self.hids.initialize()
            self.hids.run()
        except Exception as e:
            logger.error(f"Error running HIDS: {e}")

    def _stats_reporter(self):
        """Periodically report statistics"""
        stats_interval = self.config.get('monitoring', {}).get('stats_interval', 60)

        while self.running:
            try:
                time.sleep(stats_interval)
                if self.running:
                    self.print_stats()
            except Exception as e:
                logger.error(f"Error in stats reporter: {e}")

    def print_stats(self):
        """Print comprehensive statistics"""
        print("\n" + "=" * 70)
        print("  HYBRID IDS STATISTICS")
        print("=" * 70)

        # Overall stats
        if self.stats['start_time']:
            uptime = time.time() - self.stats['start_time']
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            print(f"Uptime:                {hours}h {minutes}m")

        print(f"Total Alerts:          {self.stats['total_alerts']}")
        print(f"  HIDS Alerts:         {self.stats['hids_alerts']}")
        print(f"  NIDS Alerts:         {self.stats['nids_alerts']}")
        print(f"  Correlated:          {self.stats['correlated_alerts']}")

        # Component statistics
        if self.alert_manager:
            print("\n" + "-" * 70)
            alert_stats = self.alert_manager.get_stats()
            print("Alert Manager:")
            print(f"  Processed:           {alert_stats['total_alerts']}")
            if alert_stats.get('alerts_by_severity'):
                for severity, count in alert_stats['alerts_by_severity'].items():
                    print(f"    {severity:15s}: {count}")

        if self.correlator:
            print("\n" + "-" * 70)
            corr_stats = self.correlator.get_stats()
            print("Event Correlator:")
            print(f"  Events Processed:    {corr_stats['total_events_processed']}")
            print(f"  Correlations Found:  {corr_stats['correlations_detected']}")
            print(f"  Event History Size:  {corr_stats['event_history_size']}")

        if self.hids:
            print("\n" + "-" * 70)
            print("HIDS:")
            hids_stats = self.hids.stats
            print(f"  Files Monitored:     {hids_stats['files_monitored']}")
            print(f"  File Changes:        {hids_stats['file_changes']}")
            print(f"  Process Scans:       {hids_stats['process_scans']}")
            print(f"  Suspicious Procs:    {hids_stats['suspicious_processes']}")

        print("=" * 70)

    def stop(self):
        """Stop the Hybrid IDS"""
        if not self.running:
            return

        logger.info("\nStopping Hybrid IDS...")
        self.running = False

        # Stop HIDS
        if self.hids:
            logger.info("Stopping HIDS...")
            self.hids.running = False
            if self.hids_thread:
                self.hids_thread.join(timeout=10)

        # Stop Event Correlator
        if self.correlator:
            self.correlator.stop()

        # Stop Alert Manager
        if self.alert_manager:
            self.alert_manager.stop()

        # Print final statistics
        logger.info("\nFinal Statistics:")
        self.print_stats()

        logger.info("\nHybrid IDS stopped successfully")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"\nReceived signal {signum}, initiating shutdown...")
    raise KeyboardInterrupt


def main():
    """Main entry point"""
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description='Hybrid IDS - Network and Host Intrusion Detection System')
    parser.add_argument(
        '-c', '--config',
        default='config/hybrid_ids_config.yaml',
        help='Path to configuration file (default: config/hybrid_ids_config.yaml)'
    )
    parser.add_argument(
        '--hids-only',
        action='store_true',
        help='Run only HIDS component'
    )
    parser.add_argument(
        '--no-correlation',
        action='store_true',
        help='Disable event correlation'
    )

    args = parser.parse_args()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and initialize Hybrid IDS
    hybrid_ids = HybridIDS(args.config)

    try:
        # Initialize
        if not hybrid_ids.initialize():
            logger.error("Failed to initialize Hybrid IDS")
            sys.exit(1)

        # Start
        hybrid_ids.start()

        # Run until interrupted
        while hybrid_ids.running:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        hybrid_ids.stop()


if __name__ == '__main__':
    main()
