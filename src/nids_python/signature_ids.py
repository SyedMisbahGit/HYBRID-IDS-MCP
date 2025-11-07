#!/usr/bin/env python3
"""
Signature-based Intrusion Detection System (S-IDS)
Tier 1 detection using pattern matching and rules
"""

import re
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Severity(Enum):
    """Alert severity levels"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class DetectionRule:
    """Signature detection rule"""
    
    def __init__(self, rule_dict: dict):
        self.rule_id = rule_dict.get('id', 'unknown')
        self.name = rule_dict.get('name', 'Unknown Rule')
        self.description = rule_dict.get('description', '')
        self.severity = Severity[rule_dict.get('severity', 'MEDIUM').upper()]
        self.enabled = rule_dict.get('enabled', True)
        
        # Conditions
        self.conditions = rule_dict.get('conditions', {})
        self.src_ip = self.conditions.get('src_ip')
        self.dst_ip = self.conditions.get('dst_ip')
        self.src_port = self.conditions.get('src_port')
        self.dst_port = self.conditions.get('dst_port')
        self.protocol = self.conditions.get('protocol')
        self.flags = self.conditions.get('flags')
        self.payload_pattern = self.conditions.get('payload_pattern')
        self.payload_regex = None
        
        if self.payload_pattern:
            try:
                self.payload_regex = re.compile(self.payload_pattern, re.IGNORECASE)
            except re.error as e:
                logger.warning(f"Invalid regex in rule {self.rule_id}: {e}")
    
    def match(self, packet: dict) -> bool:
        """
        Check if packet matches this rule
        
        Args:
            packet: Parsed packet dictionary
            
        Returns:
            True if packet matches rule
        """
        if not self.enabled:
            return False
        
        # Check IP addresses
        if self.src_ip and 'ip' in packet:
            if not self._match_ip(packet['ip']['src'], self.src_ip):
                return False
        
        if self.dst_ip and 'ip' in packet:
            if not self._match_ip(packet['ip']['dst'], self.dst_ip):
                return False
        
        # Check ports
        if self.src_port:
            if 'tcp' in packet:
                if packet['tcp']['sport'] != self.src_port:
                    return False
            elif 'udp' in packet:
                if packet['udp']['sport'] != self.src_port:
                    return False
            else:
                return False
        
        if self.dst_port:
            if 'tcp' in packet:
                if packet['tcp']['dport'] != self.dst_port:
                    return False
            elif 'udp' in packet:
                if packet['udp']['dport'] != self.dst_port:
                    return False
            else:
                return False
        
        # Check protocol
        if self.protocol:
            proto_match = False
            if self.protocol.upper() == 'TCP' and 'tcp' in packet:
                proto_match = True
            elif self.protocol.upper() == 'UDP' and 'udp' in packet:
                proto_match = True
            elif self.protocol.upper() == 'ICMP' and 'icmp' in packet:
                proto_match = True
            elif self.protocol.upper() == 'HTTP' and 'http' in packet:
                proto_match = True
            elif self.protocol.upper() == 'DNS' and 'dns' in packet:
                proto_match = True
            
            if not proto_match:
                return False
        
        # Check TCP flags
        if self.flags and 'tcp' in packet:
            if not self._match_flags(packet['tcp']['flags'], self.flags):
                return False
        
        # Check payload pattern
        if self.payload_regex and 'payload_preview' in packet:
            payload_hex = packet['payload_preview']
            try:
                # Convert hex to string for pattern matching
                payload_str = bytes.fromhex(payload_hex).decode('utf-8', errors='ignore')
                if not self.payload_regex.search(payload_str):
                    return False
            except Exception:
                return False
        
        return True
    
    def _match_ip(self, ip: str, pattern: str) -> bool:
        """Match IP address against pattern"""
        if pattern == 'any':
            return True
        if '/' in pattern:
            # CIDR notation
            return self._ip_in_cidr(ip, pattern)
        return ip == pattern
    
    def _ip_in_cidr(self, ip: str, cidr: str) -> bool:
        """Check if IP is in CIDR range"""
        try:
            from ipaddress import ip_address, ip_network
            return ip_address(ip) in ip_network(cidr, strict=False)
        except Exception:
            return False
    
    def _match_flags(self, flags: str, pattern: str) -> bool:
        """Match TCP flags"""
        # Simple flag matching
        return pattern.upper() in flags.upper()


class SignatureIDS:
    """
    Signature-based Intrusion Detection System
    Fast pattern matching for known threats
    """
    
    def __init__(self, rules_dir: Optional[str] = None):
        """
        Initialize S-IDS
        
        Args:
            rules_dir: Directory containing rule files
        """
        self.rules: List[DetectionRule] = []
        self.alerts: List[dict] = []
        
        self.stats = {
            'packets_processed': 0,
            'alerts_generated': 0,
            'alerts_by_severity': {
                'LOW': 0,
                'MEDIUM': 0,
                'HIGH': 0,
                'CRITICAL': 0
            }
        }
        
        # Load rules
        if rules_dir:
            self.load_rules_from_directory(rules_dir)
        else:
            self.load_default_rules()
    
    def load_default_rules(self):
        """Load default detection rules"""
        default_rules = [
            {
                'id': 'SIDS-001',
                'name': 'Port Scan Detection',
                'description': 'Detects TCP SYN scan',
                'severity': 'MEDIUM',
                'enabled': True,
                'conditions': {
                    'protocol': 'TCP',
                    'flags': 'S'
                }
            },
            {
                'id': 'SIDS-002',
                'name': 'SSH Brute Force',
                'description': 'Multiple SSH connection attempts',
                'severity': 'HIGH',
                'enabled': True,
                'conditions': {
                    'protocol': 'TCP',
                    'dst_port': 22
                }
            },
            {
                'id': 'SIDS-003',
                'name': 'HTTP SQL Injection Attempt',
                'description': 'SQL injection pattern in HTTP request',
                'severity': 'CRITICAL',
                'enabled': True,
                'conditions': {
                    'protocol': 'HTTP',
                    'payload_pattern': r'(union.*select|select.*from|insert.*into|delete.*from|drop.*table)'
                }
            },
            {
                'id': 'SIDS-004',
                'name': 'ICMP Flood',
                'description': 'ICMP echo request (potential ping flood)',
                'severity': 'LOW',
                'enabled': True,
                'conditions': {
                    'protocol': 'ICMP'
                }
            },
            {
                'id': 'SIDS-005',
                'name': 'DNS Tunneling',
                'description': 'Suspicious DNS query',
                'severity': 'MEDIUM',
                'enabled': True,
                'conditions': {
                    'protocol': 'DNS'
                }
            },
            {
                'id': 'SIDS-006',
                'name': 'FTP Brute Force',
                'description': 'FTP connection attempt',
                'severity': 'MEDIUM',
                'enabled': True,
                'conditions': {
                    'protocol': 'TCP',
                    'dst_port': 21
                }
            },
            {
                'id': 'SIDS-007',
                'name': 'Telnet Access',
                'description': 'Telnet connection (insecure)',
                'severity': 'HIGH',
                'enabled': True,
                'conditions': {
                    'protocol': 'TCP',
                    'dst_port': 23
                }
            },
            {
                'id': 'SIDS-008',
                'name': 'SMB Access',
                'description': 'SMB/CIFS connection',
                'severity': 'MEDIUM',
                'enabled': True,
                'conditions': {
                    'protocol': 'TCP',
                    'dst_port': 445
                }
            },
            {
                'id': 'SIDS-009',
                'name': 'RDP Connection',
                'description': 'Remote Desktop Protocol connection',
                'severity': 'MEDIUM',
                'enabled': True,
                'conditions': {
                    'protocol': 'TCP',
                    'dst_port': 3389
                }
            },
            {
                'id': 'SIDS-010',
                'name': 'Suspicious Port',
                'description': 'Connection to commonly exploited port',
                'severity': 'HIGH',
                'enabled': True,
                'conditions': {
                    'protocol': 'TCP',
                    'dst_port': 4444  # Metasploit default
                }
            }
        ]
        
        for rule_dict in default_rules:
            rule = DetectionRule(rule_dict)
            self.rules.append(rule)
        
        logger.info(f"Loaded {len(self.rules)} default detection rules")
    
    def load_rules_from_directory(self, rules_dir: str):
        """
        Load rules from YAML files in directory
        
        Args:
            rules_dir: Directory containing rule YAML files
        """
        rules_path = Path(rules_dir)
        if not rules_path.exists():
            logger.warning(f"Rules directory not found: {rules_dir}")
            self.load_default_rules()
            return
        
        rule_files = list(rules_path.glob('*.yaml')) + list(rules_path.glob('*.yml'))
        
        for rule_file in rule_files:
            try:
                with open(rule_file, 'r') as f:
                    rules_data = yaml.safe_load(f)
                    if isinstance(rules_data, list):
                        for rule_dict in rules_data:
                            rule = DetectionRule(rule_dict)
                            self.rules.append(rule)
                    elif isinstance(rules_data, dict) and 'rules' in rules_data:
                        for rule_dict in rules_data['rules']:
                            rule = DetectionRule(rule_dict)
                            self.rules.append(rule)
            except Exception as e:
                logger.error(f"Error loading rules from {rule_file}: {e}")
        
        if not self.rules:
            logger.warning("No rules loaded from directory, using defaults")
            self.load_default_rules()
        else:
            logger.info(f"Loaded {len(self.rules)} rules from {rules_dir}")
    
    def process_packet(self, packet: dict) -> Optional[dict]:
        """
        Process packet and check against rules
        
        Args:
            packet: Parsed packet dictionary
            
        Returns:
            Alert dictionary if match found, None otherwise
        """
        self.stats['packets_processed'] += 1
        
        for rule in self.rules:
            if rule.match(packet):
                alert = self._generate_alert(rule, packet)
                self.alerts.append(alert)
                self.stats['alerts_generated'] += 1
                self.stats['alerts_by_severity'][rule.severity.name] += 1
                return alert
        
        return None
    
    def _generate_alert(self, rule: DetectionRule, packet: dict) -> dict:
        """Generate alert from rule match"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'rule_id': rule.rule_id,
            'rule_name': rule.name,
            'description': rule.description,
            'severity': rule.severity.name,
            'packet_id': packet.get('packet_id', 0)
        }
        
        # Add packet details
        if 'ip' in packet:
            alert['src_ip'] = packet['ip']['src']
            alert['dst_ip'] = packet['ip']['dst']
        
        if 'tcp' in packet:
            alert['src_port'] = packet['tcp']['sport']
            alert['dst_port'] = packet['tcp']['dport']
            alert['protocol'] = 'TCP'
        elif 'udp' in packet:
            alert['src_port'] = packet['udp']['sport']
            alert['dst_port'] = packet['udp']['dport']
            alert['protocol'] = 'UDP'
        elif 'icmp' in packet:
            alert['protocol'] = 'ICMP'
        
        return alert
    
    def get_alerts(self) -> List[dict]:
        """Get all generated alerts"""
        return self.alerts.copy()
    
    def clear_alerts(self):
        """Clear alert history"""
        self.alerts.clear()
    
    def get_stats(self) -> dict:
        """Get detection statistics"""
        return self.stats.copy()
    
    def print_stats(self):
        """Print detection statistics"""
        print("\n" + "="*60)
        print("  Signature IDS Statistics")
        print("="*60)
        print(f"Packets Processed:  {self.stats['packets_processed']:>10}")
        print(f"Alerts Generated:   {self.stats['alerts_generated']:>10}")
        print(f"  LOW:              {self.stats['alerts_by_severity']['LOW']:>10}")
        print(f"  MEDIUM:           {self.stats['alerts_by_severity']['MEDIUM']:>10}")
        print(f"  HIGH:             {self.stats['alerts_by_severity']['HIGH']:>10}")
        print(f"  CRITICAL:         {self.stats['alerts_by_severity']['CRITICAL']:>10}")
        print(f"Active Rules:       {len([r for r in self.rules if r.enabled]):>10}")
        print("="*60 + "\n")
    
    def print_alert(self, alert: dict):
        """Print alert in formatted way"""
        severity_colors = {
            'LOW': '\033[0;32m',      # Green
            'MEDIUM': '\033[0;33m',   # Yellow
            'HIGH': '\033[0;31m',     # Red
            'CRITICAL': '\033[1;31m'  # Bold Red
        }
        
        color = severity_colors.get(alert['severity'], '\033[0m')
        reset = '\033[0m'
        
        print(f"{color}[{alert['timestamp']}] [{alert['severity']}] {alert['rule_name']}{reset}")
        print(f"  Rule ID: {alert['rule_id']}")
        print(f"  Description: {alert['description']}")
        
        if 'src_ip' in alert:
            print(f"  {alert['src_ip']}:{alert.get('src_port', 'N/A')} -> " +
                  f"{alert['dst_ip']}:{alert.get('dst_port', 'N/A')} " +
                  f"[{alert.get('protocol', 'N/A')}]")
        print()


# Example usage
if __name__ == "__main__":
    # Create S-IDS instance
    sids = SignatureIDS()
    
    # Example packet
    test_packet = {
        'packet_id': 1,
        'timestamp': datetime.now().isoformat(),
        'ip': {
            'src': '192.168.1.100',
            'dst': '10.0.0.1'
        },
        'tcp': {
            'sport': 54321,
            'dport': 22,
            'flags': 'S'
        },
        'layers': ['Ethernet', 'IP', 'TCP']
    }
    
    # Process packet
    alert = sids.process_packet(test_packet)
    
    if alert:
        sids.print_alert(alert)
    
    # Print statistics
    sids.print_stats()
