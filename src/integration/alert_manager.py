#!/usr/bin/env python3
"""
Unified Alert Manager
Receives, normalizes, enriches, and routes alerts from all detection components
"""

import logging
import json
import zmq
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class AlertManager:
    """
    Unified Alert Manager
    Multi-source ingestion, normalization, enrichment, and deduplication
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize Alert Manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()
        self.running = False
        
        # ZeroMQ context and sockets
        self.context = zmq.Context()
        self.subscribers = []
        self.publisher = None
        
        # Alert queue and deduplication
        self.alert_queue = deque(maxlen=10000)
        self.recent_alerts = {}  # For deduplication
        self.dedup_window = 60  # seconds
        
        # Statistics
        self.stats = {
            'total_received': 0,
            'total_processed': 0,
            'total_deduplicated': 0,
            'by_source': {
                'nids': 0,
                'hids': 0,
                'ai': 0
            },
            'by_severity': {
                'INFO': 0,
                'LOW': 0,
                'MEDIUM': 0,
                'HIGH': 0,
                'CRITICAL': 0
            }
        }
        
        # Alert log
        self.alert_log_path = self.config.get('alert_log', 'logs/unified_alerts.log')
        self.alert_log = None
    
    def _default_config(self) -> dict:
        """Get default configuration"""
        return {
            'zmq_subscribe_ports': [5556, 5557, 5558],  # NIDS, HIDS, AI
            'zmq_publish_port': 5559,  # For downstream consumers
            'deduplication_window': 60,  # seconds
            'alert_log': 'logs/unified_alerts.log',
            'enrichment': {
                'geoip': False,  # Requires GeoIP database
                'dns_lookup': False  # Can be slow
            }
        }
    
    def initialize(self):
        """Initialize the alert manager"""
        logger.info("Initializing Unified Alert Manager...")
        
        # Create alert log
        from pathlib import Path
        Path(self.alert_log_path).parent.mkdir(parents=True, exist_ok=True)
        self.alert_log = open(self.alert_log_path, 'a')
        
        # Setup ZeroMQ subscribers
        for port in self.config['zmq_subscribe_ports']:
            try:
                socket = self.context.socket(zmq.SUB)
                socket.connect(f"tcp://localhost:{port}")
                socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages
                socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
                self.subscribers.append({
                    'socket': socket,
                    'port': port,
                    'source': self._port_to_source(port)
                })
                logger.info(f"Subscribed to port {port} ({self._port_to_source(port)})")
            except Exception as e:
                logger.error(f"Failed to subscribe to port {port}: {e}")
        
        # Setup ZeroMQ publisher
        try:
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind(f"tcp://*:{self.config['zmq_publish_port']}")
            logger.info(f"Publishing on port {self.config['zmq_publish_port']}")
        except Exception as e:
            logger.error(f"Failed to setup publisher: {e}")
        
        logger.info("Alert Manager initialized")
    
    def _port_to_source(self, port: int) -> str:
        """Map port to source component"""
        port_map = {
            5556: 'nids',
            5557: 'hids',
            5558: 'ai'
        }
        return port_map.get(port, 'unknown')
    
    def receive_alerts(self):
        """Receive alerts from all subscribers"""
        while self.running:
            for sub in self.subscribers:
                try:
                    # Non-blocking receive
                    message = sub['socket'].recv_string(flags=zmq.NOBLOCK)
                    alert = json.loads(message)
                    alert['source'] = sub['source']
                    
                    self.stats['total_received'] += 1
                    self.stats['by_source'][sub['source']] += 1
                    
                    # Process alert
                    self.process_alert(alert)
                    
                except zmq.Again:
                    # No message available
                    pass
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {sub['source']}: {e}")
                except Exception as e:
                    logger.error(f"Error receiving from {sub['source']}: {e}")
            
            time.sleep(0.01)  # Small sleep to prevent CPU spinning
    
    def process_alert(self, alert: dict):
        """
        Process incoming alert
        
        Args:
            alert: Raw alert dictionary
        """
        # Normalize alert
        normalized = self.normalize_alert(alert)
        
        # Check for duplicates
        if self.is_duplicate(normalized):
            self.stats['total_deduplicated'] += 1
            logger.debug(f"Duplicate alert filtered: {normalized.get('name', 'unknown')}")
            return
        
        # Enrich alert
        enriched = self.enrich_alert(normalized)
        
        # Update statistics
        self.stats['total_processed'] += 1
        severity = enriched.get('severity', 'MEDIUM')
        if severity in self.stats['by_severity']:
            self.stats['by_severity'][severity] += 1
        
        # Add to queue
        self.alert_queue.append(enriched)
        
        # Log alert
        self.log_alert(enriched)
        
        # Publish to downstream
        self.publish_alert(enriched)
        
        # Print critical alerts
        if severity in ['HIGH', 'CRITICAL']:
            self.print_alert(enriched)
    
    def normalize_alert(self, alert: dict) -> dict:
        """
        Normalize alert to common schema
        
        Args:
            alert: Raw alert
            
        Returns:
            Normalized alert
        """
        normalized = {
            'id': self._generate_alert_id(alert),
            'timestamp': alert.get('timestamp', datetime.now().isoformat()),
            'source': alert.get('source', 'unknown'),
            'type': alert.get('type', alert.get('alert_type', 'unknown')),
            'severity': alert.get('severity', 'MEDIUM').upper(),
            'name': alert.get('name', alert.get('rule_name', 'Unknown Alert')),
            'description': alert.get('description', alert.get('message', '')),
            'src_ip': alert.get('src_ip', alert.get('source_ip', 'N/A')),
            'dst_ip': alert.get('dst_ip', alert.get('destination_ip', 'N/A')),
            'src_port': alert.get('src_port', 0),
            'dst_port': alert.get('dst_port', 0),
            'protocol': alert.get('protocol', 'N/A'),
            'metadata': alert.get('metadata', alert.get('details', {})),
            'raw': alert  # Keep original for reference
        }
        
        return normalized
    
    def _generate_alert_id(self, alert: dict) -> str:
        """Generate unique alert ID"""
        # Create hash from key fields
        key_fields = [
            str(alert.get('timestamp', '')),
            str(alert.get('source', '')),
            str(alert.get('src_ip', '')),
            str(alert.get('dst_ip', '')),
            str(alert.get('name', ''))
        ]
        hash_input = '|'.join(key_fields).encode()
        return hashlib.md5(hash_input).hexdigest()[:16]
    
    def is_duplicate(self, alert: dict) -> bool:
        """
        Check if alert is a duplicate
        
        Args:
            alert: Normalized alert
            
        Returns:
            True if duplicate
        """
        # Create dedup key
        dedup_key = f"{alert['source']}:{alert['name']}:{alert['src_ip']}:{alert['dst_ip']}"
        
        # Check recent alerts
        if dedup_key in self.recent_alerts:
            last_seen = self.recent_alerts[dedup_key]
            if (datetime.now() - last_seen).total_seconds() < self.dedup_window:
                return True
        
        # Update recent alerts
        self.recent_alerts[dedup_key] = datetime.now()
        
        # Cleanup old entries
        cutoff = datetime.now() - timedelta(seconds=self.dedup_window * 2)
        self.recent_alerts = {
            k: v for k, v in self.recent_alerts.items()
            if v > cutoff
        }
        
        return False
    
    def enrich_alert(self, alert: dict) -> dict:
        """
        Enrich alert with additional information
        
        Args:
            alert: Normalized alert
            
        Returns:
            Enriched alert
        """
        enriched = alert.copy()
        
        # Add enrichment timestamp
        enriched['enriched_at'] = datetime.now().isoformat()
        
        # GeoIP lookup (if enabled and available)
        if self.config['enrichment'].get('geoip', False):
            # Would require GeoIP database
            pass
        
        # DNS lookup (if enabled)
        if self.config['enrichment'].get('dns_lookup', False):
            # Would perform reverse DNS
            pass
        
        # Add risk score (simple calculation)
        enriched['risk_score'] = self._calculate_risk_score(enriched)
        
        return enriched
    
    def _calculate_risk_score(self, alert: dict) -> int:
        """Calculate risk score (0-100)"""
        severity_scores = {
            'INFO': 10,
            'LOW': 25,
            'MEDIUM': 50,
            'HIGH': 75,
            'CRITICAL': 95
        }
        
        base_score = severity_scores.get(alert['severity'], 50)
        
        # Adjust based on source
        if alert['source'] == 'ai':
            base_score += 5  # AI detections are more novel
        
        return min(base_score, 100)
    
    def log_alert(self, alert: dict):
        """Log alert to file"""
        if self.alert_log:
            self.alert_log.write(json.dumps(alert) + '\n')
            self.alert_log.flush()
    
    def publish_alert(self, alert: dict):
        """Publish alert to downstream consumers"""
        if self.publisher:
            try:
                self.publisher.send_string(json.dumps(alert))
            except Exception as e:
                logger.error(f"Failed to publish alert: {e}")
    
    def print_alert(self, alert: dict):
        """Print alert to console"""
        severity_colors = {
            'INFO': '\033[0;37m',      # White
            'LOW': '\033[0;32m',       # Green
            'MEDIUM': '\033[0;33m',    # Yellow
            'HIGH': '\033[0;31m',      # Red
            'CRITICAL': '\033[1;31m'   # Bold Red
        }
        
        color = severity_colors.get(alert['severity'], '\033[0m')
        reset = '\033[0m'
        
        print(f"{color}[{alert['timestamp']}] [{alert['severity']}] [{alert['source'].upper()}] {alert['name']}{reset}")
        if alert['src_ip'] != 'N/A':
            print(f"  {alert['src_ip']}:{alert['src_port']} -> {alert['dst_ip']}:{alert['dst_port']} [{alert['protocol']}]")
        print(f"  {alert['description']}")
        print()
    
    def print_stats(self):
        """Print statistics"""
        print("\n" + "="*70)
        print("  Unified Alert Manager Statistics")
        print("="*70)
        print(f"Total Received:       {self.stats['total_received']}")
        print(f"Total Processed:      {self.stats['total_processed']}")
        print(f"Total Deduplicated:   {self.stats['total_deduplicated']}")
        print()
        print("By Source:")
        for source, count in self.stats['by_source'].items():
            print(f"  {source.upper():10s}: {count:>6}")
        print()
        print("By Severity:")
        for severity, count in self.stats['by_severity'].items():
            print(f"  {severity:10s}: {count:>6}")
        print("="*70 + "\n")
    
    def run(self):
        """Main processing loop"""
        self.running = True
        
        # Start receiver thread
        receiver_thread = threading.Thread(target=self.receive_alerts, daemon=True)
        receiver_thread.start()
        
        logger.info("Alert Manager running")
        logger.info("Press Ctrl+C to stop")
        
        try:
            last_stats = time.time()
            while self.running:
                time.sleep(1)
                
                # Print stats every 60 seconds
                if time.time() - last_stats >= 60:
                    self.print_stats()
                    last_stats = time.time()
                    
        except KeyboardInterrupt:
            logger.info("\nReceived interrupt")
    
    def shutdown(self):
        """Shutdown alert manager"""
        logger.info("Shutting down Alert Manager...")
        self.running = False
        
        # Close sockets
        for sub in self.subscribers:
            sub['socket'].close()
        
        if self.publisher:
            self.publisher.close()
        
        self.context.term()
        
        # Close log
        if self.alert_log:
            self.alert_log.close()
        
        # Print final stats
        self.print_stats()
        
        logger.info("Alert Manager stopped")


def main():
    """Main entry point"""
    import signal
    import sys
    
    manager = AlertManager()
    
    def signal_handler(signum, frame):
        logger.info(f"\nReceived signal {signum}")
        manager.running = False
        raise KeyboardInterrupt
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        manager.initialize()
        manager.run()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Alert Manager error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        manager.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
