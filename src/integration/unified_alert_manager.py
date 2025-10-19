#!/usr/bin/env python3
"""
Unified Alert Manager for Hybrid IDS
Combines and normalizes alerts from both NIDS and HIDS components
"""

import json
import logging
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

import zmq
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class AlertSource(Enum):
    """Alert source systems"""
    NIDS_SIGNATURE = "nids_signature"
    NIDS_ANOMALY = "nids_anomaly"
    HIDS_FILE = "hids_file"
    HIDS_PROCESS = "hids_process"
    HIDS_LOG = "hids_log"
    CORRELATION = "correlation"


class UnifiedAlert:
    """Unified alert structure"""

    def __init__(self,
                 source: AlertSource,
                 severity: AlertSeverity,
                 title: str,
                 description: str,
                 metadata: Optional[Dict] = None):
        self.alert_id = f"{source.value}_{int(time.time() * 1000000)}"
        self.timestamp = datetime.utcnow().isoformat()
        self.source = source.value
        self.severity = severity.name
        self.title = title
        self.description = description
        self.metadata = metadata or {}

        # Add common fields
        self.metadata['alert_version'] = '1.0'
        self.metadata['ids_type'] = 'hybrid'

    def to_dict(self) -> Dict:
        """Convert alert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp,
            'source': self.source,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'metadata': self.metadata
        }

    def to_elasticsearch(self) -> Dict:
        """Convert to Elasticsearch document format"""
        doc = self.to_dict()
        doc['@timestamp'] = self.timestamp
        return doc


class UnifiedAlertManager:
    """
    Manages alerts from multiple IDS sources
    Normalizes, enriches, and forwards alerts to various outputs
    """

    def __init__(self, config: Dict):
        self.config = config
        self.alert_queue = queue.Queue(maxsize=10000)
        self.running = False

        # Statistics
        self.stats = {
            'total_alerts': 0,
            'alerts_by_source': {},
            'alerts_by_severity': {},
            'start_time': None
        }

        # Initialize outputs
        self.elasticsearch = None
        self.file_handler = None

        # ZMQ context for receiving alerts
        self.zmq_context = None
        self.zmq_subscribers = []

        # Worker threads
        self.threads = []

    def initialize(self):
        """Initialize alert manager components"""
        logger.info("Initializing Unified Alert Manager...")

        # Initialize Elasticsearch if enabled
        if self.config.get('outputs', {}).get('elasticsearch', {}).get('enabled', False):
            self._init_elasticsearch()

        # Initialize file output if enabled
        if self.config.get('outputs', {}).get('file', {}).get('enabled', False):
            self._init_file_output()

        # Initialize ZMQ subscribers for alert sources
        self._init_zmq_subscribers()

        logger.info("Unified Alert Manager initialized successfully")

    def _init_elasticsearch(self):
        """Initialize Elasticsearch connection"""
        try:
            es_config = self.config['outputs']['elasticsearch']
            self.elasticsearch = Elasticsearch(
                [es_config['host']],
                verify_certs=es_config.get('verify_certs', False)
            )

            # Test connection
            if self.elasticsearch.ping():
                logger.info(f"Connected to Elasticsearch at {es_config['host']}")
            else:
                logger.error("Failed to connect to Elasticsearch")
                self.elasticsearch = None
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch: {e}")
            self.elasticsearch = None

    def _init_file_output(self):
        """Initialize file output handler"""
        try:
            file_config = self.config['outputs']['file']
            log_dir = Path(file_config['directory'])
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / file_config['filename']
            self.file_handler = open(log_file, 'a', encoding='utf-8')
            logger.info(f"File output enabled: {log_file}")
        except Exception as e:
            logger.error(f"Error initializing file output: {e}")
            self.file_handler = None

    def _init_zmq_subscribers(self):
        """Initialize ZMQ subscribers for different alert sources"""
        try:
            self.zmq_context = zmq.Context()

            # Subscribe to NIDS alerts
            nids_config = self.config.get('inputs', {}).get('nids', {})
            if nids_config.get('enabled', False):
                nids_sub = self.zmq_context.socket(zmq.SUB)
                nids_sub.connect(nids_config['endpoint'])
                nids_sub.setsockopt_string(zmq.SUBSCRIBE, "")
                self.zmq_subscribers.append(('nids', nids_sub))
                logger.info(f"Subscribed to NIDS alerts at {nids_config['endpoint']}")

            # Subscribe to HIDS alerts
            hids_config = self.config.get('inputs', {}).get('hids', {})
            if hids_config.get('enabled', False):
                hids_sub = self.zmq_context.socket(zmq.SUB)
                hids_sub.connect(hids_config['endpoint'])
                hids_sub.setsockopt_string(zmq.SUBSCRIBE, "")
                self.zmq_subscribers.append(('hids', hids_sub))
                logger.info(f"Subscribed to HIDS alerts at {hids_config['endpoint']}")

        except Exception as e:
            logger.error(f"Error initializing ZMQ subscribers: {e}")

    def start(self):
        """Start the alert manager"""
        logger.info("Starting Unified Alert Manager...")
        self.running = True
        self.stats['start_time'] = time.time()

        # Start ZMQ receiver threads
        for source_name, subscriber in self.zmq_subscribers:
            thread = threading.Thread(
                target=self._zmq_receiver_worker,
                args=(source_name, subscriber),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            logger.info(f"Started {source_name} receiver thread")

        # Start alert processor threads
        num_processors = self.config.get('processing', {}).get('worker_threads', 2)
        for i in range(num_processors):
            thread = threading.Thread(
                target=self._alert_processor_worker,
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
        logger.info(f"Started {num_processors} alert processor threads")

    def _zmq_receiver_worker(self, source_name: str, subscriber: zmq.Socket):
        """Worker thread to receive alerts from ZMQ"""
        logger.info(f"ZMQ receiver for {source_name} started")

        while self.running:
            try:
                # Receive alert with timeout
                if subscriber.poll(timeout=1000):  # 1 second timeout
                    message = subscriber.recv_json()
                    self._process_incoming_alert(source_name, message)
            except zmq.ZMQError as e:
                if self.running:  # Only log if we're still supposed to be running
                    logger.error(f"ZMQ error in {source_name} receiver: {e}")
            except Exception as e:
                logger.error(f"Error in {source_name} receiver: {e}")

        logger.info(f"ZMQ receiver for {source_name} stopped")

    def _process_incoming_alert(self, source_name: str, message: Dict):
        """Process incoming alert from a source system"""
        try:
            # Normalize the alert based on source
            if source_name == 'nids':
                unified_alert = self._normalize_nids_alert(message)
            elif source_name == 'hids':
                unified_alert = self._normalize_hids_alert(message)
            else:
                logger.warning(f"Unknown alert source: {source_name}")
                return

            # Add to processing queue
            self.alert_queue.put(unified_alert)

        except Exception as e:
            logger.error(f"Error processing incoming alert from {source_name}: {e}")

    def _normalize_nids_alert(self, message: Dict) -> UnifiedAlert:
        """Normalize NIDS alert to unified format"""
        # Determine if this is signature or anomaly based alert
        alert_type = message.get('type', 'signature')

        if alert_type == 'anomaly':
            source = AlertSource.NIDS_ANOMALY
        else:
            source = AlertSource.NIDS_SIGNATURE

        # Map severity
        severity_map = {
            'INFO': AlertSeverity.INFO,
            'LOW': AlertSeverity.LOW,
            'MEDIUM': AlertSeverity.MEDIUM,
            'HIGH': AlertSeverity.HIGH,
            'CRITICAL': AlertSeverity.CRITICAL
        }
        severity = severity_map.get(message.get('severity', 'MEDIUM'), AlertSeverity.MEDIUM)

        # Create unified alert
        return UnifiedAlert(
            source=source,
            severity=severity,
            title=message.get('name', 'NIDS Alert'),
            description=message.get('description', ''),
            metadata={
                'src_ip': message.get('src_ip'),
                'dst_ip': message.get('dst_ip'),
                'src_port': message.get('src_port'),
                'dst_port': message.get('dst_port'),
                'protocol': message.get('protocol'),
                'rule_id': message.get('rule_id'),
                'mitre_attack': message.get('mitre_attack'),
                'confidence': message.get('confidence'),
                'raw_data': message
            }
        )

    def _normalize_hids_alert(self, message: Dict) -> UnifiedAlert:
        """Normalize HIDS alert to unified format"""
        # Determine HIDS component
        component = message.get('component', 'unknown')

        source_map = {
            'file_monitor': AlertSource.HIDS_FILE,
            'process_monitor': AlertSource.HIDS_PROCESS,
            'log_analyzer': AlertSource.HIDS_LOG
        }
        source = source_map.get(component, AlertSource.HIDS_PROCESS)

        # Map severity
        severity_map = {
            'info': AlertSeverity.INFO,
            'low': AlertSeverity.LOW,
            'medium': AlertSeverity.MEDIUM,
            'high': AlertSeverity.HIGH,
            'critical': AlertSeverity.CRITICAL
        }
        severity = severity_map.get(
            message.get('severity', 'medium').lower(),
            AlertSeverity.MEDIUM
        )

        # Create unified alert
        return UnifiedAlert(
            source=source,
            severity=severity,
            title=message.get('alert_type', 'HIDS Alert'),
            description=message.get('description', ''),
            metadata={
                'hostname': message.get('hostname'),
                'component': component,
                'details': message.get('details'),
                'raw_data': message
            }
        )

    def _alert_processor_worker(self):
        """Worker thread to process and output alerts"""
        while self.running:
            try:
                # Get alert from queue with timeout
                alert = self.alert_queue.get(timeout=1)

                # Process the alert
                self._output_alert(alert)

                # Update statistics
                self._update_stats(alert)

                self.alert_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing alert: {e}")

    def _output_alert(self, alert: UnifiedAlert):
        """Output alert to configured destinations"""
        # Output to Elasticsearch
        if self.elasticsearch:
            try:
                index_name = self.config['outputs']['elasticsearch']['index_pattern'].format(
                    date=datetime.utcnow().strftime('%Y.%m.%d')
                )
                self.elasticsearch.index(
                    index=index_name,
                    document=alert.to_elasticsearch()
                )
            except Exception as e:
                logger.error(f"Error sending alert to Elasticsearch: {e}")

        # Output to file
        if self.file_handler:
            try:
                self.file_handler.write(json.dumps(alert.to_dict()) + '\n')
                self.file_handler.flush()
            except Exception as e:
                logger.error(f"Error writing alert to file: {e}")

        # Output to console (if enabled)
        if self.config.get('outputs', {}).get('console', {}).get('enabled', True):
            self._print_alert(alert)

    def _print_alert(self, alert: UnifiedAlert):
        """Print alert to console"""
        severity_colors = {
            'INFO': '\033[94m',      # Blue
            'LOW': '\033[92m',       # Green
            'MEDIUM': '\033[93m',    # Yellow
            'HIGH': '\033[91m',      # Red
            'CRITICAL': '\033[95m'   # Magenta
        }
        reset = '\033[0m'

        color = severity_colors.get(alert.severity, '')

        print(f"{color}[{alert.severity}]{reset} [{alert.source}] {alert.title}")
        if self.config.get('outputs', {}).get('console', {}).get('verbose', False):
            print(f"  Description: {alert.description}")
            print(f"  Time: {alert.timestamp}")
            print(f"  ID: {alert.alert_id}")

    def _update_stats(self, alert: UnifiedAlert):
        """Update statistics"""
        self.stats['total_alerts'] += 1

        # By source
        if alert.source not in self.stats['alerts_by_source']:
            self.stats['alerts_by_source'][alert.source] = 0
        self.stats['alerts_by_source'][alert.source] += 1

        # By severity
        if alert.severity not in self.stats['alerts_by_severity']:
            self.stats['alerts_by_severity'][alert.severity] = 0
        self.stats['alerts_by_severity'][alert.severity] += 1

    def add_alert(self, alert: UnifiedAlert):
        """Manually add an alert to the queue"""
        try:
            self.alert_queue.put_nowait(alert)
        except queue.Full:
            logger.error("Alert queue is full, dropping alert")

    def get_stats(self) -> Dict:
        """Get current statistics"""
        stats = self.stats.copy()
        if stats['start_time']:
            stats['uptime_seconds'] = time.time() - stats['start_time']
        return stats

    def print_stats(self):
        """Print statistics to console"""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("  Unified Alert Manager Statistics")
        print("=" * 60)
        print(f"Total Alerts:         {stats['total_alerts']}")

        if stats.get('uptime_seconds'):
            uptime = stats['uptime_seconds']
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            print(f"Uptime:               {hours}h {minutes}m")

        print(f"\nAlerts by Source:")
        for source, count in stats['alerts_by_source'].items():
            print(f"  {source:20s}: {count}")

        print(f"\nAlerts by Severity:")
        for severity, count in stats['alerts_by_severity'].items():
            print(f"  {severity:20s}: {count}")

        print("=" * 60)

    def stop(self):
        """Stop the alert manager"""
        logger.info("Stopping Unified Alert Manager...")
        self.running = False

        # Wait for queue to be processed
        logger.info("Waiting for alert queue to be processed...")
        self.alert_queue.join()

        # Wait for threads
        for thread in self.threads:
            thread.join(timeout=5)

        # Close ZMQ subscribers
        for _, subscriber in self.zmq_subscribers:
            subscriber.close()

        if self.zmq_context:
            self.zmq_context.term()

        # Close file handler
        if self.file_handler:
            self.file_handler.close()

        logger.info("Unified Alert Manager stopped")


def main():
    """Test the unified alert manager"""
    # Test configuration
    config = {
        'inputs': {
            'nids': {
                'enabled': True,
                'endpoint': 'tcp://localhost:5556'
            },
            'hids': {
                'enabled': True,
                'endpoint': 'tcp://localhost:5557'
            }
        },
        'outputs': {
            'console': {
                'enabled': True,
                'verbose': True
            },
            'file': {
                'enabled': True,
                'directory': 'logs/alerts',
                'filename': 'unified_alerts.json'
            },
            'elasticsearch': {
                'enabled': False,
                'host': 'http://localhost:9200',
                'index_pattern': 'hybrid-ids-alerts-{date}',
                'verify_certs': False
            }
        },
        'processing': {
            'worker_threads': 2
        }
    }

    # Create and start manager
    manager = UnifiedAlertManager(config)
    manager.initialize()
    manager.start()

    # Add some test alerts
    test_alert = UnifiedAlert(
        source=AlertSource.NIDS_SIGNATURE,
        severity=AlertSeverity.HIGH,
        title="Test SQL Injection Detected",
        description="Potential SQL injection attempt detected in HTTP request",
        metadata={
            'src_ip': '192.168.1.100',
            'dst_ip': '10.0.0.50',
            'src_port': 54321,
            'dst_port': 80,
            'protocol': 'TCP'
        }
    )
    manager.add_alert(test_alert)

    # Keep running
    try:
        while True:
            time.sleep(5)
            manager.print_stats()
    except KeyboardInterrupt:
        print("\nShutting down...")
        manager.stop()


if __name__ == '__main__':
    main()
