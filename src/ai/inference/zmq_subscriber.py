#!/usr/bin/env python3
"""
ZMQ Subscriber - Receives flow features from NIDS and performs real-time detection
"""

import json
import logging
import signal
import sys
import time
from pathlib import Path

# Note: ZeroMQ import (install with: pip install pyzmq)
try:
    import zmq
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False
    logging.warning("pyzmq not installed, using simulation mode")

from anomaly_detector import AnomalyDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class NIDSSubscriber:
    """
    Subscribes to NIDS feature stream and performs real-time anomaly detection
    """

    def __init__(self, zmq_endpoint: str = "tcp://localhost:5555", topic: str = "features"):
        """
        Initialize subscriber

        Args:
            zmq_endpoint: ZMQ endpoint to connect to
            topic: Topic to subscribe to
        """
        self.endpoint = zmq_endpoint
        self.topic = topic
        self.detector = AnomalyDetector()
        self.running = False

        # ZMQ context and socket
        self.context = None
        self.socket = None

        # Alert log
        self.alert_log_path = "ai_alerts.log"
        self.alert_log = None

    def connect(self) -> bool:
        """
        Connect to ZMQ publisher

        Returns:
            True if successful
        """
        try:
            if not ZMQ_AVAILABLE:
                logger.warning("ZMQ not available, running in simulation mode")
                return True

            logger.info(f"Connecting to {self.endpoint}...")

            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect(self.endpoint)
            self.socket.setsockopt_string(zmq.SUBSCRIBE, self.topic)

            # Set timeout for recv
            self.socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout

            logger.info(f"Connected successfully, subscribed to topic: '{self.topic}'")
            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """Disconnect from ZMQ"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        logger.info("Disconnected from ZMQ")

    def log_alert(self, flow_id: int, confidence: float, details: dict):
        """Log detected anomaly"""
        alert = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'flow_id': flow_id,
            'type': 'ANOMALY',
            'confidence': confidence,
            'details': details
        }

        if self.alert_log:
            self.alert_log.write(json.dumps(alert) + '\n')
            self.alert_log.flush()

        # Print to console
        color = "\033[0;31m"  # Red
        reset = "\033[0m"
        print(f"{color}[ALERT] Anomaly detected! (confidence: {confidence:.3f}){reset}")
        print(f"  Flow ID: {flow_id}")
        print(f"  Ensemble Score: {details.get('ensemble_score', 0):.3f}")
        print(f"  Inference Time: {details.get('inference_time_ms', 0):.2f} ms")
        print()

    def run(self):
        """
        Main loop - receive and process features
        """
        logger.info("Starting AI inference engine...")

        # Load models
        if not self.detector.load_models():
            logger.error("Failed to load models")
            return 1

        # Open alert log
        self.alert_log = open(self.alert_log_path, 'a')
        logger.info(f"Alert log: {self.alert_log_path}")

        # Start processing
        self.running = True
        flow_count = 0
        last_stats_time = time.time()
        stats_interval = 10  # Print stats every 10 seconds

        logger.info("Waiting for feature vectors from NIDS...")
        logger.info("Press Ctrl+C to stop\n")

        try:
            while self.running:
                try:
                    if ZMQ_AVAILABLE and self.socket:
                        # Receive message from ZMQ
                        try:
                            # Receive topic
                            topic = self.socket.recv_string(zmq.DONTWAIT)
                            # Receive JSON data
                            json_data = self.socket.recv_string()

                            flow_count += 1

                            # Process features
                            is_anomaly, confidence, details = self.detector.process_json_features(json_data)

                            if is_anomaly:
                                self.log_alert(flow_count, confidence, details)

                        except zmq.Again:
                            # No message available, continue
                            time.sleep(0.01)
                            continue

                    else:
                        # Simulation mode - process dummy data
                        import numpy as np
                        test_features = np.random.randn(78)
                        is_anomaly, confidence, details = self.detector.predict(test_features)

                        flow_count += 1

                        if is_anomaly:
                            self.log_alert(flow_count, confidence, details)

                        time.sleep(1)  # Simulate 1 flow per second

                    # Print periodic statistics
                    now = time.time()
                    if now - last_stats_time >= stats_interval:
                        self.detector.print_stats()
                        last_stats_time = now

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue

        except KeyboardInterrupt:
            logger.info("\nReceived interrupt signal")
        finally:
            self.cleanup()

        return 0

    def cleanup(self):
        """Cleanup resources"""
        logger.info("\nCleaning up...")

        self.running = False

        # Print final stats
        self.detector.print_stats()

        # Close alert log
        if self.alert_log:
            self.alert_log.close()

        # Disconnect ZMQ
        self.disconnect()

        logger.info("Cleanup complete")


def signal_handler(signum, frame):
    """Handle signals"""
    logger.info(f"\nReceived signal {signum}")
    sys.exit(0)


def main():
    """Main entry point"""
    print("="*60)
    print("  Hybrid IDS - AI Inference Engine")
    print("  Real-time Anomaly Detection")
    print("="*60)
    print()

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='AI Inference Engine for Hybrid IDS')
    parser.add_argument('--endpoint', type=str, default='tcp://localhost:5555',
                        help='ZMQ endpoint to connect to (default: tcp://localhost:5555)')
    parser.add_argument('--topic', type=str, default='features',
                        help='Topic to subscribe to (default: features)')
    parser.add_argument('--simulate', action='store_true',
                        help='Run in simulation mode (no ZMQ connection)')

    args = parser.parse_args()

    # Create and run subscriber
    subscriber = NIDSSubscriber(
        zmq_endpoint=args.endpoint,
        topic=args.topic
    )

    # Connect
    if not args.simulate:
        if not subscriber.connect():
            logger.error("Failed to connect to NIDS")
            return 1
    else:
        logger.info("Running in simulation mode")

    # Run
    return subscriber.run()


if __name__ == "__main__":
    sys.exit(main())
