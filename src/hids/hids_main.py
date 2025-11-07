#!/usr/bin/env python3
"""
Complete HIDS (Host-based Intrusion Detection System)
Integrates file monitoring, log analysis, and process monitoring
"""

import argparse
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

# ZeroMQ for integration
try:
    import zmq
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False
    logging.warning("ZeroMQ not available. Install with: pip install pyzmq")

# Import HIDS components
from file_monitor import FileIntegrityMonitor
from log_analyzer import LogAnalyzer
from process_monitor import ProcessMonitor

# Import exporters
sys.path.insert(0, str(Path(__file__).parent.parent / 'exporters'))
try:
    from elasticsearch_exporter import ElasticsearchExporter
    ES_AVAILABLE = True
except ImportError:
    ES_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HybridHIDS:
    """
    Complete Host-based Intrusion Detection System
    """

    def __init__(self, config: dict = None):
        """
        Initialize HIDS

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.running = False

        # Initialize components
        self.file_monitor = FileIntegrityMonitor()
        self.log_analyzer = LogAnalyzer()
        self.process_monitor = ProcessMonitor()

        # Elasticsearch exporter (optional)
        self.es_exporter = None
        if self.config.get('elasticsearch_enabled', False) and ES_AVAILABLE:
            self.es_exporter = ElasticsearchExporter(
                hosts=self.config.get('elasticsearch_hosts', ['http://localhost:9200'])
            )

        # Alert logs
        self.alert_log_path = self.config.get('alert_log', 'hids_alerts.log')
        self.alert_log = None

        # ZeroMQ publisher for integration
        self.zmq_context = None
        self.zmq_publisher = None
        if self.config.get('zmq_enabled', True) and ZMQ_AVAILABLE:
            try:
                self.zmq_context = zmq.Context()
                self.zmq_publisher = self.zmq_context.socket(zmq.PUB)
                zmq_port = self.config.get('zmq_port', 5557)
                self.zmq_publisher.bind(f"tcp://*:{zmq_port}")
                logger.info(f"ZeroMQ publisher bound to port {zmq_port}")
            except Exception as e:
                logger.error(f"Failed to setup ZeroMQ: {e}")
                self.zmq_publisher = None

        # Statistics
        self.stats = {
            'start_time': None,
            'total_alerts': 0,
            'file_alerts': 0,
            'log_alerts': 0,
            'process_alerts': 0,
            'zmq_published': 0
        }

    def initialize(self):
        """Initialize HIDS system"""
        logger.info("="*60)
        logger.info("  Hybrid IDS - Host-based Detection System")
        logger.info("="*60)
        logger.info("")

        # Open alert log
        self.alert_log = open(self.alert_log_path, 'a')
        logger.info(f"Alert log: {self.alert_log_path}")

        # Initialize Elasticsearch
        if self.es_exporter:
            if self.es_exporter.connect():
                self.es_exporter.create_index_templates()
                logger.info("Elasticsearch integration enabled")
            else:
                logger.warning("Elasticsearch connection failed, continuing without it")
                self.es_exporter = None

        # Create file integrity baseline
        if self.config.get('file_monitoring', True):
            baseline_file = self.config.get('baseline_file', 'hids_baseline.json')
            if Path(baseline_file).exists():
                self.file_monitor.load_baseline(baseline_file)
                logger.info(f"Loaded baseline from {baseline_file}")
            else:
                logger.info("Creating new file integrity baseline...")
                self.file_monitor.create_baseline()
                self.file_monitor.save_baseline(baseline_file)

        # Create process baseline
        if self.config.get('process_monitoring', True):
            self.process_monitor.create_baseline()

        logger.info("")
        logger.info("HIDS initialized successfully")
        logger.info("Press Ctrl+C to stop")
        logger.info("")

    def run(self):
        """Main monitoring loop"""
        self.running = True
        self.stats['start_time'] = time.time()

        check_interval = self.config.get('check_interval', 60)  # seconds
        log_check_interval = self.config.get('log_check_interval', 300)  # 5 minutes

        last_file_check = 0
        last_process_check = 0
        last_log_check = 0

        try:
            while self.running:
                current_time = time.time()

                # File integrity monitoring
                if self.config.get('file_monitoring', True):
                    if current_time - last_file_check >= check_interval:
                        logger.info("[FIM] Checking file integrity...")
                        self.file_monitor.check_integrity()

                        # Export alerts
                        if self.file_monitor.alerts:
                            self._export_alerts(self.file_monitor.alerts, 'file_integrity')
                            self.stats['file_alerts'] += len(self.file_monitor.alerts)
                            self.stats['total_alerts'] += len(self.file_monitor.alerts)
                            self.file_monitor.alerts = []

                        last_file_check = current_time

                # Process monitoring
                if self.config.get('process_monitoring', True):
                    if current_time - last_process_check >= check_interval:
                        logger.info("[PM] Scanning processes...")
                        process_alerts = self.process_monitor.scan_processes()

                        # Scan network connections
                        conn_alerts = self.process_monitor.scan_network_connections()

                        all_process_alerts = process_alerts + conn_alerts

                        if all_process_alerts:
                            self._export_alerts(all_process_alerts, 'process_monitoring')
                            self.stats['process_alerts'] += len(all_process_alerts)
                            self.stats['total_alerts'] += len(all_process_alerts)

                        last_process_check = current_time

                # Log analysis
                if self.config.get('log_monitoring', True):
                    if current_time - last_log_check >= log_check_interval:
                        logger.info("[LA] Analyzing system logs...")
                        self._analyze_system_logs()
                        last_log_check = current_time

                # Print periodic statistics
                if int(current_time) % 300 == 0:  # Every 5 minutes
                    self._print_stats()

                # Sleep to prevent CPU spinning
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("\n[SIGNAL] Received interrupt, shutting down...")

    def _analyze_system_logs(self):
        """Analyze system logs"""
        log_paths = self.config.get('log_paths', [])

        # Default log paths if none specified
        if not log_paths:
            import platform
            if platform.system() == 'Windows':
                # Windows Event Log (requires pywin32)
                try:
                    events = self.log_analyzer.analyze_windows_event_log('Security')
                    if events:
                        self._export_alerts(events, 'log_analysis')
                        self.stats['log_alerts'] += len(events)
                        self.stats['total_alerts'] += len(events)
                except Exception as e:
                    logger.error(f"Failed to analyze Windows Event Log: {e}")
            else:
                # Linux/Unix logs
                log_paths = ['/var/log/auth.log', '/var/log/syslog', '/var/log/secure']

        # Analyze each log file
        for log_path in log_paths:
            if Path(log_path).exists():
                events = self.log_analyzer.analyze_log_file(log_path)
                if events:
                    self._export_alerts(events, 'log_analysis')
                    self.stats['log_alerts'] += len(events)
                    self.stats['total_alerts'] += len(events)

    def _export_alerts(self, alerts: list, alert_type: str):
        """
        Export alerts to various outputs

        Args:
            alerts: List of alert dictionaries
            alert_type: Type of alert (file_integrity, process_monitoring, log_analysis)
        """
        for alert in alerts:
            # Add alert type
            alert['alert_type'] = alert_type
            alert['host'] = self.config.get('hostname', 'localhost')

            # Write to file
            if self.alert_log:
                self.alert_log.write(json.dumps(alert) + '\n')
                self.alert_log.flush()

            # Publish to ZeroMQ for integration
            if self.zmq_publisher:
                try:
                    self.zmq_publisher.send_string(json.dumps(alert), zmq.NOBLOCK)
                    self.stats['zmq_published'] += 1
                except Exception as e:
                    logger.error(f"Failed to publish to ZeroMQ: {e}")

            # Export to Elasticsearch
            if self.es_exporter:
                try:
                    # Map to NIDS alert format for consistency
                    es_alert = {
                        '@timestamp': alert.get('timestamp', datetime.now().isoformat()),
                        'type': alert_type,
                        'severity': alert.get('severity', 'MEDIUM'),
                        'message': alert.get('message', 'HIDS Alert'),
                        'details': alert,
                        'host': alert['host']
                    }
                    # Use hybrid-ids-hids-alerts index
                    date_suffix = datetime.utcnow().strftime('%Y.%m.%d')
                    index_name = f"hybrid-ids-hids-alerts-{date_suffix}"
                    self.es_exporter.es.index(index=index_name, document=es_alert)
                except Exception as e:
                    logger.error(f"Failed to export to Elasticsearch: {e}")

    def _print_stats(self):
        """Print monitoring statistics"""
        print("\n" + "="*60)
        print("  HIDS Statistics")
        print("="*60)

        # Calculate uptime if monitoring has started
        if self.stats['start_time'] is not None:
            uptime = time.time() - self.stats['start_time']
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            print(f"Uptime:             {hours}h {minutes}m")
        else:
            print(f"Uptime:             Not started")

        print(f"Total Alerts:       {self.stats['total_alerts']}")
        print(f"  File Alerts:      {self.stats['file_alerts']}")
        print(f"  Process Alerts:   {self.stats['process_alerts']}")
        print(f"  Log Alerts:       {self.stats['log_alerts']}")
        print("="*60 + "\n")

    def shutdown(self):
        """Shutdown HIDS"""
        logger.info("\n[INFO] Shutting down HIDS...")

        # Save final baseline
        if self.config.get('file_monitoring', True):
            baseline_file = self.config.get('baseline_file', 'hids_baseline.json')
            self.file_monitor.save_baseline(baseline_file)

        # Close ZeroMQ
        if self.zmq_publisher:
            self.zmq_publisher.close()
        if self.zmq_context:
            self.zmq_context.term()

        # Close alert log
        if self.alert_log:
            self.alert_log.close()

        # Print final stats
        print()
        self._print_stats()
        self.file_monitor.print_stats()
        self.log_analyzer.print_stats() if hasattr(self.log_analyzer, 'print_stats') else None
        self.process_monitor.print_stats()

        logger.info("[INFO] HIDS stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Hybrid IDS - Host-based Detection System')
    parser.add_argument('--config', type=str, help='Configuration file (YAML)')
    parser.add_argument('--baseline', type=str, help='Baseline file path')
    parser.add_argument('--no-files', action='store_true', help='Disable file monitoring')
    parser.add_argument('--no-processes', action='store_true', help='Disable process monitoring')
    parser.add_argument('--no-logs', action='store_true', help='Disable log monitoring')
    parser.add_argument('--elasticsearch', action='store_true', help='Enable Elasticsearch export')
    parser.add_argument('--es-host', type=str, default='http://localhost:9200', help='Elasticsearch host')

    args = parser.parse_args()

    # Build configuration
    config = {
        'file_monitoring': not args.no_files,
        'process_monitoring': not args.no_processes,
        'log_monitoring': not args.no_logs,
        'elasticsearch_enabled': args.elasticsearch,
        'elasticsearch_hosts': [args.es_host],
        'check_interval': 60,
        'log_check_interval': 300
    }

    if args.baseline:
        config['baseline_file'] = args.baseline

    # Load config file if specified
    if args.config and Path(args.config).exists():
        import yaml
        with open(args.config, 'r') as f:
            file_config = yaml.safe_load(f)
            config.update(file_config)

    # Initialize HIDS
    hids = HybridHIDS(config)

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        """Handle shutdown signals"""
        logger.info(f"\n[SIGNAL] Received signal {signum}, shutting down...")
        hids.running = False
        # Allow cleanup to happen in finally block
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize and run
        hids.initialize()
        hids.run()
    except KeyboardInterrupt:
        logger.info("\n[INFO] Interrupted by user")
    except Exception as e:
        logger.error(f"HIDS error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        hids.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
