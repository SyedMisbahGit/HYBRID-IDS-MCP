#!/usr/bin/env python3
"""
Event Correlator for Hybrid IDS
Performs cross-system correlation between NIDS and HIDS events
Detects multi-stage attacks and lateral movement
"""

import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from unified_alert_manager import UnifiedAlert, AlertSeverity, AlertSource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class CorrelationRule:
    """Defines a correlation rule between events"""
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    time_window: int  # seconds
    required_events: List[Dict]  # List of event patterns to match
    min_occurrences: int = 1
    same_ip: bool = False  # Events must share same IP
    same_host: bool = False  # Events must share same hostname


@dataclass
class EventContext:
    """Maintains context for event correlation"""
    alert: UnifiedAlert
    timestamp: datetime
    ip_addresses: Set[str] = field(default_factory=set)
    hostname: Optional[str] = None


class EventCorrelator:
    """
    Correlates events across NIDS and HIDS to detect complex attack patterns
    """

    def __init__(self, config: Dict):
        self.config = config
        self.running = False

        # Event history (sliding window)
        self.event_window_seconds = config.get('correlation', {}).get('window_seconds', 300)
        self.event_history = deque(maxlen=10000)

        # Event indices for fast lookup
        self.events_by_ip = defaultdict(list)
        self.events_by_host = defaultdict(list)
        self.events_by_source = defaultdict(list)

        # Correlation rules
        self.correlation_rules = []

        # Correlation results cache
        self.correlated_events = {}

        # Statistics
        self.stats = {
            'total_events_processed': 0,
            'correlations_detected': 0,
            'correlations_by_rule': defaultdict(int),
            'start_time': None
        }

        # Threading
        self.lock = threading.RLock()
        self.cleanup_thread = None

        # Initialize default correlation rules
        self._init_default_rules()

    def _init_default_rules(self):
        """Initialize default correlation rules"""

        # Rule 1: Port Scan followed by Exploitation
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR001",
            name="Port Scan to Exploitation",
            description="Port scanning activity followed by successful exploitation attempt",
            severity=AlertSeverity.CRITICAL,
            time_window=600,  # 10 minutes
            required_events=[
                {'source': 'nids_signature', 'pattern': 'port.*scan'},
                {'source': 'nids_signature', 'pattern': '(exploit|injection|overflow)'}
            ],
            same_ip=True
        ))

        # Rule 2: Network Attack followed by Process Execution
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR002",
            name="Network to Process Compromise",
            description="Network attack followed by suspicious process execution on host",
            severity=AlertSeverity.CRITICAL,
            time_window=300,  # 5 minutes
            required_events=[
                {'source': 'nids_signature', 'pattern': '(injection|exploit|shell)'},
                {'source': 'hids_process', 'pattern': 'suspicious'}
            ],
            same_ip=True
        ))

        # Rule 3: Brute Force followed by Lateral Movement
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR003",
            name="Brute Force to Lateral Movement",
            description="Successful brute force attack followed by lateral movement attempts",
            severity=AlertSeverity.CRITICAL,
            time_window=1800,  # 30 minutes
            required_events=[
                {'source': 'hids_log', 'pattern': 'brute.*force'},
                {'source': 'nids_signature', 'pattern': '(smb|rdp|ssh).*brute'}
            ],
            same_ip=True
        ))

        # Rule 4: File Modification after Network Activity
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR004",
            name="Network Attack to File Modification",
            description="Network attack followed by suspicious file modifications",
            severity=AlertSeverity.HIGH,
            time_window=600,  # 10 minutes
            required_events=[
                {'source': 'nids_signature', 'pattern': '(web.*attack|injection|upload)'},
                {'source': 'hids_file', 'pattern': '(modified|created|deleted)'}
            ],
            same_ip=True
        ))

        # Rule 5: Multiple Attack Vectors (Advanced Persistent Threat)
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR005",
            name="Multi-Vector Attack (APT Indicator)",
            description="Multiple attack types detected from same source - possible APT",
            severity=AlertSeverity.CRITICAL,
            time_window=3600,  # 1 hour
            required_events=[
                {'source': 'nids_signature'},
                {'source': 'hids_process'},
                {'source': 'hids_file'}
            ],
            min_occurrences=3,
            same_ip=True
        ))

        # Rule 6: DNS Tunneling with Data Exfiltration
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR006",
            name="DNS Tunneling and Exfiltration",
            description="DNS tunneling detected along with file access patterns",
            severity=AlertSeverity.CRITICAL,
            time_window=900,  # 15 minutes
            required_events=[
                {'source': 'nids_signature', 'pattern': 'dns.*tunnel'},
                {'source': 'hids_file', 'pattern': '(access|read)'}
            ],
            same_host=True
        ))

        # Rule 7: Privilege Escalation Chain
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR007",
            name="Privilege Escalation Chain",
            description="Network compromise followed by privilege escalation attempts",
            severity=AlertSeverity.CRITICAL,
            time_window=600,  # 10 minutes
            required_events=[
                {'source': 'nids_signature'},
                {'source': 'hids_log', 'pattern': '(privilege|admin|root|sudo)'}
            ],
            same_host=True
        ))

        # Rule 8: DDoS with Internal Reconnaissance
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR008",
            name="DDoS Smokescreen Attack",
            description="DDoS attack used as smokescreen for internal reconnaissance",
            severity=AlertSeverity.HIGH,
            time_window=1800,  # 30 minutes
            required_events=[
                {'source': 'nids_signature', 'pattern': '(ddos|flood)'},
                {'source': 'nids_signature', 'pattern': '(scan|recon)'}
            ]
        ))

        # Rule 9: Malware Installation Chain
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR009",
            name="Malware Installation Chain",
            description="Network download followed by process execution and file modifications",
            severity=AlertSeverity.CRITICAL,
            time_window=300,  # 5 minutes
            required_events=[
                {'source': 'nids_signature', 'pattern': '(download|http)'},
                {'source': 'hids_process', 'pattern': 'suspicious'},
                {'source': 'hids_file', 'pattern': 'created'}
            ],
            same_host=True
        ))

        # Rule 10: Anomaly-based APT Detection
        self.correlation_rules.append(CorrelationRule(
            rule_id="CR010",
            name="ML-Detected APT Pattern",
            description="Machine learning detected anomalies across both network and host",
            severity=AlertSeverity.CRITICAL,
            time_window=1800,  # 30 minutes
            required_events=[
                {'source': 'nids_anomaly'},
                {'source': 'hids_process', 'pattern': 'suspicious'}
            ],
            min_occurrences=2,
            same_ip=True
        ))

        logger.info(f"Initialized {len(self.correlation_rules)} correlation rules")

    def start(self):
        """Start the event correlator"""
        logger.info("Starting Event Correlator...")
        self.running = True
        self.stats['start_time'] = time.time()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True
        )
        self.cleanup_thread.start()

        logger.info("Event Correlator started")

    def process_alert(self, alert: UnifiedAlert) -> List[UnifiedAlert]:
        """
        Process an incoming alert and check for correlations
        Returns list of correlated alerts (if any)
        """
        with self.lock:
            # Create event context
            context = self._create_event_context(alert)

            # Add to event history
            self.event_history.append(context)

            # Index the event
            self._index_event(context)

            # Update statistics
            self.stats['total_events_processed'] += 1

            # Check for correlations
            correlated_alerts = self._check_correlations(context)

            return correlated_alerts

    def _create_event_context(self, alert: UnifiedAlert) -> EventContext:
        """Create event context from alert"""
        context = EventContext(
            alert=alert,
            timestamp=datetime.fromisoformat(alert.timestamp)
        )

        # Extract IP addresses
        metadata = alert.metadata
        if 'src_ip' in metadata:
            context.ip_addresses.add(metadata['src_ip'])
        if 'dst_ip' in metadata:
            context.ip_addresses.add(metadata['dst_ip'])

        # Extract hostname
        if 'hostname' in metadata:
            context.hostname = metadata['hostname']

        return context

    def _index_event(self, context: EventContext):
        """Index event for fast lookup"""
        # Index by IP
        for ip in context.ip_addresses:
            self.events_by_ip[ip].append(context)

        # Index by hostname
        if context.hostname:
            self.events_by_host[context.hostname].append(context)

        # Index by source
        self.events_by_source[context.alert.source].append(context)

    def _check_correlations(self, new_event: EventContext) -> List[UnifiedAlert]:
        """Check if new event correlates with existing events"""
        correlated_alerts = []

        for rule in self.correlation_rules:
            if self._matches_correlation_rule(new_event, rule):
                # Create correlated alert
                correlated_alert = self._create_correlated_alert(new_event, rule)
                correlated_alerts.append(correlated_alert)

                # Update statistics
                self.stats['correlations_detected'] += 1
                self.stats['correlations_by_rule'][rule.rule_id] += 1

                logger.warning(f"Correlation detected: {rule.name} (Rule: {rule.rule_id})")

        return correlated_alerts

    def _matches_correlation_rule(self, new_event: EventContext, rule: CorrelationRule) -> bool:
        """Check if events match a correlation rule"""
        # Get time window
        cutoff_time = new_event.timestamp - timedelta(seconds=rule.time_window)

        # Get candidate events based on constraints
        candidate_events = self._get_candidate_events(new_event, rule, cutoff_time)

        # Check if we have enough matching events
        matched_patterns = set()

        for event in candidate_events:
            for i, required_event in enumerate(rule.required_events):
                if i in matched_patterns:
                    continue

                if self._event_matches_pattern(event, required_event):
                    matched_patterns.add(i)
                    break

        # Check if all required patterns are matched
        return len(matched_patterns) >= len(rule.required_events)

    def _get_candidate_events(self,
                               new_event: EventContext,
                               rule: CorrelationRule,
                               cutoff_time: datetime) -> List[EventContext]:
        """Get candidate events based on rule constraints"""
        if rule.same_ip and new_event.ip_addresses:
            # Get events with same IP
            candidates = []
            for ip in new_event.ip_addresses:
                candidates.extend(self.events_by_ip.get(ip, []))
        elif rule.same_host and new_event.hostname:
            # Get events from same host
            candidates = self.events_by_host.get(new_event.hostname, [])
        else:
            # Get all recent events
            candidates = list(self.event_history)

        # Filter by time window
        candidates = [e for e in candidates if e.timestamp >= cutoff_time]

        return candidates

    def _event_matches_pattern(self, event: EventContext, pattern: Dict) -> bool:
        """Check if event matches a pattern"""
        import re

        # Check source
        if 'source' in pattern:
            if event.alert.source != pattern['source']:
                return False

        # Check pattern in title/description
        if 'pattern' in pattern:
            search_text = f"{event.alert.title} {event.alert.description}".lower()
            pattern_re = re.compile(pattern['pattern'], re.IGNORECASE)
            if not pattern_re.search(search_text):
                return False

        return True

    def _create_correlated_alert(self,
                                  trigger_event: EventContext,
                                  rule: CorrelationRule) -> UnifiedAlert:
        """Create a correlated alert"""
        # Gather related events
        cutoff_time = trigger_event.timestamp - timedelta(seconds=rule.time_window)
        related_events = self._get_candidate_events(trigger_event, rule, cutoff_time)

        # Build description
        description = f"{rule.description}\n\n"
        description += f"Correlation triggered by: {trigger_event.alert.title}\n"
        description += f"Related events in last {rule.time_window}s:\n"

        for event in related_events[:5]:  # Limit to 5 events in description
            description += f"  - [{event.alert.source}] {event.alert.title}\n"

        if len(related_events) > 5:
            description += f"  ... and {len(related_events) - 5} more events\n"

        # Create metadata
        metadata = {
            'correlation_rule_id': rule.rule_id,
            'trigger_alert_id': trigger_event.alert.alert_id,
            'related_alert_count': len(related_events),
            'related_alert_ids': [e.alert.alert_id for e in related_events],
            'time_window_seconds': rule.time_window,
            'ip_addresses': list(trigger_event.ip_addresses),
            'hostname': trigger_event.hostname
        }

        # Create correlated alert
        return UnifiedAlert(
            source=AlertSource.CORRELATION,
            severity=rule.severity,
            title=rule.name,
            description=description,
            metadata=metadata
        )

    def _cleanup_worker(self):
        """Worker thread to clean up old events"""
        while self.running:
            try:
                time.sleep(60)  # Run every minute
                self._cleanup_old_events()
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")

    def _cleanup_old_events(self):
        """Remove events older than the maximum window"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.event_window_seconds)

            # Clean event history (deque automatically limits size)
            # But we need to clean the indices

            # Clean IP index
            for ip, events in list(self.events_by_ip.items()):
                self.events_by_ip[ip] = [e for e in events if e.timestamp >= cutoff_time]
                if not self.events_by_ip[ip]:
                    del self.events_by_ip[ip]

            # Clean hostname index
            for hostname, events in list(self.events_by_host.items()):
                self.events_by_host[hostname] = [e for e in events if e.timestamp >= cutoff_time]
                if not self.events_by_host[hostname]:
                    del self.events_by_host[hostname]

            # Clean source index
            for source, events in list(self.events_by_source.items()):
                self.events_by_source[source] = [e for e in events if e.timestamp >= cutoff_time]
                if not self.events_by_source[source]:
                    del self.events_by_source[source]

    def get_stats(self) -> Dict:
        """Get correlation statistics"""
        with self.lock:
            stats = self.stats.copy()
            stats['event_history_size'] = len(self.event_history)
            stats['indexed_ips'] = len(self.events_by_ip)
            stats['indexed_hosts'] = len(self.events_by_host)
            stats['active_correlation_rules'] = len(self.correlation_rules)

            if stats['start_time']:
                stats['uptime_seconds'] = time.time() - stats['start_time']

            return stats

    def print_stats(self):
        """Print correlation statistics"""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("  Event Correlator Statistics")
        print("=" * 60)
        print(f"Events Processed:     {stats['total_events_processed']}")
        print(f"Correlations Found:   {stats['correlations_detected']}")
        print(f"Event History Size:   {stats['event_history_size']}")
        print(f"Indexed IPs:          {stats['indexed_ips']}")
        print(f"Indexed Hosts:        {stats['indexed_hosts']}")
        print(f"Active Rules:         {stats['active_correlation_rules']}")

        if stats.get('uptime_seconds'):
            uptime = stats['uptime_seconds']
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            print(f"Uptime:               {hours}h {minutes}m")

        if stats['correlations_by_rule']:
            print(f"\nCorrelations by Rule:")
            for rule_id, count in stats['correlations_by_rule'].items():
                print(f"  {rule_id}: {count}")

        print("=" * 60)

    def stop(self):
        """Stop the event correlator"""
        logger.info("Stopping Event Correlator...")
        self.running = False

        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)

        logger.info("Event Correlator stopped")


def main():
    """Test the event correlator"""
    from datetime import datetime

    # Create correlator
    config = {
        'correlation': {
            'window_seconds': 300
        }
    }

    correlator = EventCorrelator(config)
    correlator.start()

    # Create test alerts
    # Alert 1: Port scan
    alert1 = UnifiedAlert(
        source=AlertSource.NIDS_SIGNATURE,
        severity=AlertSeverity.MEDIUM,
        title="TCP Port Scan Detected",
        description="Port scanning activity detected from 192.168.1.100",
        metadata={
            'src_ip': '192.168.1.100',
            'dst_ip': '10.0.0.50',
            'protocol': 'TCP'
        }
    )

    # Alert 2: SQL Injection (same IP)
    alert2 = UnifiedAlert(
        source=AlertSource.NIDS_SIGNATURE,
        severity=AlertSeverity.HIGH,
        title="SQL Injection Attempt",
        description="SQL injection detected in HTTP request",
        metadata={
            'src_ip': '192.168.1.100',
            'dst_ip': '10.0.0.50',
            'protocol': 'TCP'
        }
    )

    # Process alerts
    print("Processing alert 1 (Port Scan)...")
    correlated1 = correlator.process_alert(alert1)
    print(f"Correlations: {len(correlated1)}")

    time.sleep(2)

    print("\nProcessing alert 2 (SQL Injection)...")
    correlated2 = correlator.process_alert(alert2)
    print(f"Correlations: {len(correlated2)}")

    if correlated2:
        print("\nCorrelated Alert Detected!")
        for alert in correlated2:
            print(f"  Title: {alert.title}")
            print(f"  Severity: {alert.severity}")
            print(f"  Description: {alert.description[:200]}...")

    # Print statistics
    correlator.print_stats()

    # Stop
    correlator.stop()


if __name__ == '__main__':
    main()
