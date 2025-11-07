#!/usr/bin/env python3
"""
Complete Network Intrusion Detection System (NIDS) - Python Implementation
Integrates packet capture, signature detection, and feature extraction
"""

import argparse
import json
import logging
import signal
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# ZeroMQ for integration
try:
    import zmq
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False
    logging.warning("ZeroMQ not available. Install with: pip install pyzmq")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from packet_capture import PacketCapture
from signature_ids import SignatureIDS

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HybridNIDS:
    """
    Complete Network Intrusion Detection System
    Combines packet capture and signature-based detection
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize NIDS
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.running = False
        
        # Initialize components
        interface = self.config.get('interface')
        pcap_file = self.config.get('pcap_file')
        
        self.capture = PacketCapture(interface=interface, pcap_file=pcap_file)
        
        rules_dir = self.config.get('rules_dir')
        self.sids = SignatureIDS(rules_dir=rules_dir)
        
        # Alert log
        self.alert_log_path = self.config.get('alert_log', 'logs/nids_alerts.log')
        self.alert_log = None
        
        # ZeroMQ publisher for integration
        self.zmq_context = None
        self.zmq_publisher = None
        if self.config.get('zmq_enabled', True) and ZMQ_AVAILABLE:
            try:
                self.zmq_context = zmq.Context()
                self.zmq_publisher = self.zmq_context.socket(zmq.PUB)
                zmq_port = self.config.get('zmq_port', 5556)
                self.zmq_publisher.bind(f"tcp://*:{zmq_port}")
                logger.info(f"ZeroMQ publisher bound to port {zmq_port}")
            except Exception as e:
                logger.error(f"Failed to setup ZeroMQ: {e}")
                self.zmq_publisher = None
        
        # Statistics
        self.stats = {
            'start_time': None,
            'total_packets': 0,
            'total_alerts': 0,
            'zmq_published': 0,
            'last_stats_print': time.time()
        }
    
    def initialize(self):
        """Initialize NIDS system"""
        print("="*70)
        print("  Hybrid IDS - Network-based Detection System (Python)")
        print("="*70)
        print()
        
        # Create logs directory
        log_dir = Path(self.alert_log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Open alert log
        self.alert_log = open(self.alert_log_path, 'a')
        logger.info(f"Alert log: {self.alert_log_path}")
        
        # Print configuration
        if self.config.get('pcap_file'):
            logger.info(f"Mode: Offline (PCAP file: {self.config['pcap_file']})")
        elif self.config.get('interface'):
            logger.info(f"Mode: Live capture (Interface: {self.config['interface']})")
        else:
            logger.info("Mode: Live capture (Default interface)")
        
        logger.info(f"Loaded {len(self.sids.rules)} detection rules")
        
        # Print active rules
        print("\nActive Detection Rules:")
        print("-" * 70)
        for rule in self.sids.rules:
            if rule.enabled:
                print(f"  [{rule.rule_id}] {rule.name} ({rule.severity.name})")
        
        print()
        logger.info("NIDS initialized successfully")
        logger.info("Press Ctrl+C to stop")
        print()
    
    def packet_handler(self, packet: dict):
        """
        Handle captured packet
        
        Args:
            packet: Parsed packet dictionary
        """
        self.stats['total_packets'] += 1
        
        # Check against signatures
        alert = self.sids.process_packet(packet)
        
        if alert:
            self.stats['total_alerts'] += 1
            self._export_alert(alert)
            self._print_alert(alert)
        
        # Print periodic statistics
        current_time = time.time()
        if current_time - self.stats['last_stats_print'] >= 10:  # Every 10 seconds
            self._print_stats()
            self.stats['last_stats_print'] = current_time
    
    def _export_alert(self, alert: dict):
        """
        Export alert to log file
        
        Args:
            alert: Alert dictionary
        """
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
    
    def _print_alert(self, alert: dict):
        """Print alert to console"""
        self.sids.print_alert(alert)
    
    def _print_stats(self):
        """Print current statistics"""
        print("\n" + "="*70)
        print("  NIDS Statistics")
        print("="*70)
        
        if self.stats['start_time']:
            uptime = time.time() - self.stats['start_time']
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            print(f"Uptime:           {hours:02d}:{minutes:02d}")
        
        print(f"Packets Captured: {self.stats['total_packets']}")
        print(f"Alerts Generated: {self.stats['total_alerts']}")
        
        # Capture stats
        cap_stats = self.capture.get_stats()
        print(f"TCP Packets:      {cap_stats['tcp_packets']}")
        print(f"UDP Packets:      {cap_stats['udp_packets']}")
        print(f"ICMP Packets:     {cap_stats['icmp_packets']}")
        print(f"HTTP Packets:     {cap_stats['http_packets']}")
        print(f"DNS Packets:      {cap_stats['dns_packets']}")
        
        print("="*70 + "\n")
    
    def run(self):
        """Main detection loop"""
        self.running = True
        self.stats['start_time'] = time.time()
        
        # Set packet handler
        self.capture.set_callback(self.packet_handler)
        
        # Start capture
        try:
            count = self.config.get('packet_count', 0)
            timeout = self.config.get('timeout')
            
            self.capture.start_capture(count=count, timeout=timeout)
            
        except KeyboardInterrupt:
            logger.info("\nReceived interrupt, shutting down...")
        finally:
            self.running = False
    
    def shutdown(self):
        """Shutdown NIDS"""
        logger.info("\nShutting down NIDS...")
        
        # Stop capture
        self.capture.stop_capture()
        
        # Close ZeroMQ
        if self.zmq_publisher:
            self.zmq_publisher.close()
        if self.zmq_context:
            self.zmq_context.term()
        
        # Close alert log
        if self.alert_log:
            self.alert_log.close()
        
        # Print final statistics
        print("\n" + "="*70)
        print("  Final Statistics")
        print("="*70)
        self.capture.print_stats()
        self.sids.print_stats()
        
        logger.info("NIDS stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Hybrid IDS - Network-based Detection System (Python)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Capture from PCAP file
  python nids_main.py -r test.pcap
  
  # Live capture on interface (requires admin)
  python nids_main.py -i eth0
  
  # Capture 100 packets
  python nids_main.py -r test.pcap -c 100
  
  # Use custom rules directory
  python nids_main.py -r test.pcap --rules-dir config/nids/rules
        """
    )
    
    # Input options
    parser.add_argument('-i', '--interface', type=str,
                        help='Network interface to capture from')
    parser.add_argument('-r', '--read-file', type=str,
                        help='Read packets from PCAP file')
    
    # Capture options
    parser.add_argument('-c', '--count', type=int, default=0,
                        help='Number of packets to capture (0 = infinite)')
    parser.add_argument('-t', '--timeout', type=int,
                        help='Capture timeout in seconds')
    
    # Detection options
    parser.add_argument('--rules-dir', type=str,
                        help='Directory containing detection rules')
    parser.add_argument('--alert-log', type=str, default='logs/nids_alerts.log',
                        help='Alert log file path')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.interface and args.read_file:
        parser.error("Cannot specify both --interface and --read-file")
    
    # Build configuration
    config = {
        'interface': args.interface,
        'pcap_file': args.read_file,
        'packet_count': args.count,
        'timeout': args.timeout,
        'rules_dir': args.rules_dir,
        'alert_log': args.alert_log
    }
    
    # Initialize NIDS
    nids = HybridNIDS(config)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"\nReceived signal {signum}, shutting down...")
        nids.running = False
        raise KeyboardInterrupt
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and run
        nids.initialize()
        nids.run()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"NIDS error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        nids.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
