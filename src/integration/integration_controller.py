#!/usr/bin/env python3
"""
Integration Controller - Master Control Plane (MCP)
Orchestrates all Hybrid IDS components
"""

import logging
import signal
import sys
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ComponentStatus:
    """Component status tracking"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"


class IntegrationController:
    """
    Master Control Plane for Hybrid IDS
    Orchestrates NIDS, HIDS, AI Engine, and Alert Manager
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize Integration Controller
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()
        self.running = False
        self.components = {}
        self.processes = {}
        
        # Statistics
        self.stats = {
            'start_time': None,
            'components_started': 0,
            'components_running': 0,
            'total_alerts': 0,
            'nids_alerts': 0,
            'hids_alerts': 0,
            'ai_detections': 0
        }
        
        # Health monitoring
        self.health_check_interval = 30  # seconds
        self.health_thread = None
    
    def _default_config(self) -> dict:
        """Get default configuration"""
        return {
            'components': {
                'nids': {
                    'enabled': True,
                    'type': 'python',  # or 'cpp' when built
                    'command': ['python', 'src/nids_python/nids_main.py', '-r', 'test.pcap'],
                    'zmq_port': 5556,
                    'restart_on_failure': True
                },
                'hids': {
                    'enabled': True,
                    'command': ['python', 'src/hids/hids_main.py', '--config', 'config/hids/hids_config.yaml', '--no-logs'],
                    'zmq_port': 5557,
                    'restart_on_failure': True
                },
                'ai_engine': {
                    'enabled': False,  # Enable when models are trained
                    'command': ['python', 'src/ai/inference/zmq_subscriber.py'],
                    'zmq_port': 5558,
                    'restart_on_failure': True
                },
                'alert_manager': {
                    'enabled': True,
                    'command': ['python', 'src/integration/alert_manager.py'],
                    'zmq_ports': [5556, 5557, 5558],
                    'restart_on_failure': True
                },
                'event_correlator': {
                    'enabled': True,
                    'command': ['python', 'src/integration/event_correlator.py'],
                    'restart_on_failure': True
                }
            },
            'monitoring': {
                'health_check_interval': 30,
                'log_stats_interval': 60
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/integration.log'
            }
        }
    
    def initialize(self):
        """Initialize the integration controller"""
        print("="*70)
        print("  Hybrid IDS - Integration Controller (MCP)")
        print("="*70)
        print()
        
        logger.info("Initializing Integration Controller...")
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        # Initialize component status
        for comp_name, comp_config in self.config['components'].items():
            self.components[comp_name] = {
                'status': ComponentStatus.STOPPED,
                'config': comp_config,
                'process': None,
                'start_time': None,
                'restart_count': 0
            }
        
        logger.info(f"Configured {len(self.components)} components")
        
        # Print component status
        print("\nConfigured Components:")
        print("-" * 70)
        for comp_name, comp_info in self.components.items():
            enabled = "✅" if comp_info['config']['enabled'] else "❌"
            print(f"  {enabled} {comp_name.upper()}")
        print()
    
    def start_component(self, component_name: str) -> bool:
        """
        Start a component
        
        Args:
            component_name: Name of component to start
            
        Returns:
            True if started successfully
        """
        comp = self.components.get(component_name)
        if not comp:
            logger.error(f"Component not found: {component_name}")
            return False
        
        if not comp['config']['enabled']:
            logger.info(f"Component {component_name} is disabled, skipping")
            return False
        
        if comp['status'] == ComponentStatus.RUNNING:
            logger.warning(f"Component {component_name} is already running")
            return True
        
        logger.info(f"Starting component: {component_name}")
        comp['status'] = ComponentStatus.STARTING
        
        try:
            # Start process
            command = comp['config']['command']
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            comp['process'] = process
            comp['start_time'] = datetime.now()
            comp['status'] = ComponentStatus.RUNNING
            self.stats['components_started'] += 1
            self.stats['components_running'] += 1
            
            logger.info(f"Component {component_name} started (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {component_name}: {e}")
            comp['status'] = ComponentStatus.ERROR
            return False
    
    def stop_component(self, component_name: str) -> bool:
        """
        Stop a component
        
        Args:
            component_name: Name of component to stop
            
        Returns:
            True if stopped successfully
        """
        comp = self.components.get(component_name)
        if not comp:
            logger.error(f"Component not found: {component_name}")
            return False
        
        if comp['status'] != ComponentStatus.RUNNING:
            logger.warning(f"Component {component_name} is not running")
            return True
        
        logger.info(f"Stopping component: {component_name}")
        comp['status'] = ComponentStatus.STOPPING
        
        try:
            process = comp['process']
            if process:
                process.terminate()
                process.wait(timeout=10)
                comp['process'] = None
                comp['status'] = ComponentStatus.STOPPED
                self.stats['components_running'] -= 1
                logger.info(f"Component {component_name} stopped")
                return True
        except subprocess.TimeoutExpired:
            logger.warning(f"Component {component_name} did not stop gracefully, killing")
            process.kill()
            comp['process'] = None
            comp['status'] = ComponentStatus.STOPPED
            self.stats['components_running'] -= 1
            return True
        except Exception as e:
            logger.error(f"Failed to stop {component_name}: {e}")
            comp['status'] = ComponentStatus.ERROR
            return False
    
    def start_all_components(self):
        """Start all enabled components"""
        logger.info("Starting all enabled components...")
        
        # Start order: NIDS -> HIDS -> AI Engine -> Alert Manager -> Event Correlator
        start_order = ['nids', 'hids', 'ai_engine', 'alert_manager', 'event_correlator']
        
        for comp_name in start_order:
            if comp_name in self.components:
                self.start_component(comp_name)
                time.sleep(2)  # Give component time to initialize
    
    def stop_all_components(self):
        """Stop all running components"""
        logger.info("Stopping all components...")
        
        # Stop in reverse order
        stop_order = ['event_correlator', 'alert_manager', 'ai_engine', 'hids', 'nids']
        
        for comp_name in stop_order:
            if comp_name in self.components:
                self.stop_component(comp_name)
    
    def health_check(self):
        """Check health of all components"""
        for comp_name, comp in self.components.items():
            if comp['status'] == ComponentStatus.RUNNING:
                process = comp['process']
                if process and process.poll() is not None:
                    # Process has terminated
                    logger.error(f"Component {comp_name} has crashed (exit code: {process.returncode})")
                    comp['status'] = ComponentStatus.ERROR
                    self.stats['components_running'] -= 1
                    
                    # Restart if configured
                    if comp['config'].get('restart_on_failure', False):
                        logger.info(f"Restarting {comp_name}...")
                        comp['restart_count'] += 1
                        time.sleep(5)
                        self.start_component(comp_name)
    
    def health_monitor_loop(self):
        """Health monitoring loop"""
        while self.running:
            time.sleep(self.health_check_interval)
            self.health_check()
    
    def print_stats(self):
        """Print system statistics"""
        print("\n" + "="*70)
        print("  Integration Controller Statistics")
        print("="*70)
        
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            print(f"Uptime:               {hours:02d}:{minutes:02d}")
        
        print(f"Components Started:   {self.stats['components_started']}")
        print(f"Components Running:   {self.stats['components_running']}")
        print(f"Total Alerts:         {self.stats['total_alerts']}")
        print(f"  NIDS Alerts:        {self.stats['nids_alerts']}")
        print(f"  HIDS Alerts:        {self.stats['hids_alerts']}")
        print(f"  AI Detections:      {self.stats['ai_detections']}")
        
        print("\nComponent Status:")
        for comp_name, comp in self.components.items():
            status_icon = {
                ComponentStatus.RUNNING: "✅",
                ComponentStatus.STOPPED: "⭕",
                ComponentStatus.ERROR: "❌",
                ComponentStatus.STARTING: "🔄",
                ComponentStatus.STOPPING: "🛑"
            }.get(comp['status'], "❓")
            
            restart_info = f" (restarts: {comp['restart_count']})" if comp['restart_count'] > 0 else ""
            print(f"  {status_icon} {comp_name.upper()}: {comp['status']}{restart_info}")
        
        print("="*70 + "\n")
    
    def run(self):
        """Main control loop"""
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # Start all components
        self.start_all_components()
        
        # Start health monitoring
        self.health_thread = threading.Thread(target=self.health_monitor_loop, daemon=True)
        self.health_thread.start()
        
        logger.info("Integration Controller running")
        logger.info("Press Ctrl+C to stop")
        
        # Main loop
        try:
            last_stats_print = time.time()
            stats_interval = self.config['monitoring'].get('log_stats_interval', 60)
            
            while self.running:
                time.sleep(1)
                
                # Print stats periodically
                if time.time() - last_stats_print >= stats_interval:
                    self.print_stats()
                    last_stats_print = time.time()
                    
        except KeyboardInterrupt:
            logger.info("\nReceived interrupt signal")
    
    def shutdown(self):
        """Shutdown the integration controller"""
        logger.info("Shutting down Integration Controller...")
        self.running = False
        
        # Stop all components
        self.stop_all_components()
        
        # Print final stats
        self.print_stats()
        
        logger.info("Integration Controller stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hybrid IDS Integration Controller')
    parser.add_argument('--config', type=str, help='Configuration file (JSON/YAML)')
    parser.add_argument('--no-nids', action='store_true', help='Disable NIDS')
    parser.add_argument('--no-hids', action='store_true', help='Disable HIDS')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI engine')
    
    args = parser.parse_args()
    
    # Load config
    config = None
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            import yaml
            config = yaml.safe_load(f)
    
    # Create controller
    controller = IntegrationController(config)
    
    # Apply command-line overrides
    if args.no_nids:
        controller.config['components']['nids']['enabled'] = False
    if args.no_hids:
        controller.config['components']['hids']['enabled'] = False
    if args.no_ai:
        controller.config['components']['ai_engine']['enabled'] = False
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"\nReceived signal {signum}")
        controller.running = False
        raise KeyboardInterrupt
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        controller.initialize()
        controller.run()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Controller error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        controller.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
