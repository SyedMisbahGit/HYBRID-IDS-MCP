#!/usr/bin/env python3
"""
Feature Extraction Module for ML-based Detection
Extracts 78 features from network flows for anomaly detection
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class FlowTracker:
    """
    Tracks network flows and extracts statistical features
    """
    
    def __init__(self, timeout: int = 120):
        """
        Initialize flow tracker
        
        Args:
            timeout: Flow timeout in seconds
        """
        self.timeout = timeout
        self.flows: Dict[str, dict] = {}
        self.completed_flows: List[dict] = []
    
    def _get_flow_key(self, packet: dict) -> Optional[str]:
        """Generate flow key from packet"""
        if 'ip' not in packet:
            return None
        
        src_ip = packet['ip']['src']
        dst_ip = packet['ip']['dst']
        
        if 'tcp' in packet:
            src_port = packet['tcp']['sport']
            dst_port = packet['tcp']['dport']
            protocol = 'TCP'
        elif 'udp' in packet:
            src_port = packet['udp']['sport']
            dst_port = packet['udp']['dport']
            protocol = 'UDP'
        else:
            return None
        
        # Bidirectional flow key (sorted to match both directions)
        if (src_ip, src_port) < (dst_ip, dst_port):
            return f"{src_ip}:{src_port}-{dst_ip}:{dst_port}-{protocol}"
        else:
            return f"{dst_ip}:{dst_port}-{src_ip}:{src_port}-{protocol}"
    
    def process_packet(self, packet: dict):
        """
        Process packet and update flow statistics
        
        Args:
            packet: Parsed packet dictionary
        """
        flow_key = self._get_flow_key(packet)
        if not flow_key:
            return
        
        # Get or create flow
        if flow_key not in self.flows:
            self.flows[flow_key] = self._create_flow(packet)
        
        flow = self.flows[flow_key]
        self._update_flow(flow, packet)
        
        # Check for flow timeout
        self._check_timeouts()
    
    def _create_flow(self, packet: dict) -> dict:
        """Create new flow from first packet"""
        flow = {
            'flow_id': len(self.flows) + len(self.completed_flows),
            'start_time': datetime.now(),
            'last_packet_time': datetime.now(),
            
            # Endpoints
            'src_ip': packet['ip']['src'],
            'dst_ip': packet['ip']['dst'],
            'protocol': 'TCP' if 'tcp' in packet else 'UDP',
            
            # Counters
            'total_fwd_packets': 0,
            'total_bwd_packets': 0,
            'total_fwd_bytes': 0,
            'total_bwd_bytes': 0,
            
            # Packet lengths
            'fwd_pkt_lens': [],
            'bwd_pkt_lens': [],
            
            # Inter-arrival times
            'fwd_iats': [],
            'bwd_iats': [],
            'flow_iats': [],
            
            # TCP flags
            'fin_count': 0,
            'syn_count': 0,
            'rst_count': 0,
            'psh_count': 0,
            'ack_count': 0,
            'urg_count': 0,
            
            # Flow state
            'is_active': True,
            'last_fwd_time': None,
            'last_bwd_time': None
        }
        
        # Set ports
        if 'tcp' in packet:
            flow['src_port'] = packet['tcp']['sport']
            flow['dst_port'] = packet['tcp']['dport']
        elif 'udp' in packet:
            flow['src_port'] = packet['udp']['sport']
            flow['dst_port'] = packet['udp']['dport']
        
        return flow
    
    def _update_flow(self, flow: dict, packet: dict):
        """Update flow with new packet"""
        current_time = datetime.now()
        packet_len = packet.get('raw_length', 0)
        
        # Determine direction
        is_forward = (packet['ip']['src'] == flow['src_ip'])
        
        if is_forward:
            flow['total_fwd_packets'] += 1
            flow['total_fwd_bytes'] += packet_len
            flow['fwd_pkt_lens'].append(packet_len)
            
            if flow['last_fwd_time']:
                iat = (current_time - flow['last_fwd_time']).total_seconds() * 1000000  # microseconds
                flow['fwd_iats'].append(iat)
            
            flow['last_fwd_time'] = current_time
        else:
            flow['total_bwd_packets'] += 1
            flow['total_bwd_bytes'] += packet_len
            flow['bwd_pkt_lens'].append(packet_len)
            
            if flow['last_bwd_time']:
                iat = (current_time - flow['last_bwd_time']).total_seconds() * 1000000  # microseconds
                flow['bwd_iats'].append(iat)
            
            flow['last_bwd_time'] = current_time
        
        # Flow IAT
        if flow['last_packet_time']:
            flow_iat = (current_time - flow['last_packet_time']).total_seconds() * 1000000
            flow['flow_iats'].append(flow_iat)
        
        flow['last_packet_time'] = current_time
        
        # TCP flags
        if 'tcp' in packet:
            flags = packet['tcp']['flags']
            if 'F' in flags:
                flow['fin_count'] += 1
            if 'S' in flags:
                flow['syn_count'] += 1
            if 'R' in flags:
                flow['rst_count'] += 1
            if 'P' in flags:
                flow['psh_count'] += 1
            if 'A' in flags:
                flow['ack_count'] += 1
            if 'U' in flags:
                flow['urg_count'] += 1
    
    def _check_timeouts(self):
        """Check for timed out flows"""
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=self.timeout)
        
        to_remove = []
        for flow_key, flow in self.flows.items():
            if current_time - flow['last_packet_time'] > timeout_threshold:
                flow['is_active'] = False
                self.completed_flows.append(flow)
                to_remove.append(flow_key)
        
        for key in to_remove:
            del self.flows[key]
    
    def extract_features(self, flow: dict) -> dict:
        """
        Extract 78 features from flow
        
        Args:
            flow: Flow dictionary
            
        Returns:
            Dictionary with 78 features
        """
        features = {}
        
        # Duration
        duration = (flow['last_packet_time'] - flow['start_time']).total_seconds()
        features['duration'] = duration
        
        # Packet counts
        features['total_fwd_packets'] = flow['total_fwd_packets']
        features['total_bwd_packets'] = flow['total_bwd_packets']
        features['total_fwd_bytes'] = flow['total_fwd_bytes']
        features['total_bwd_bytes'] = flow['total_bwd_bytes']
        
        # Forward packet lengths
        if flow['fwd_pkt_lens']:
            features['fwd_pkt_len_max'] = max(flow['fwd_pkt_lens'])
            features['fwd_pkt_len_min'] = min(flow['fwd_pkt_lens'])
            features['fwd_pkt_len_mean'] = statistics.mean(flow['fwd_pkt_lens'])
            features['fwd_pkt_len_std'] = statistics.stdev(flow['fwd_pkt_lens']) if len(flow['fwd_pkt_lens']) > 1 else 0
        else:
            features['fwd_pkt_len_max'] = 0
            features['fwd_pkt_len_min'] = 0
            features['fwd_pkt_len_mean'] = 0
            features['fwd_pkt_len_std'] = 0
        
        # Backward packet lengths
        if flow['bwd_pkt_lens']:
            features['bwd_pkt_len_max'] = max(flow['bwd_pkt_lens'])
            features['bwd_pkt_len_min'] = min(flow['bwd_pkt_lens'])
            features['bwd_pkt_len_mean'] = statistics.mean(flow['bwd_pkt_lens'])
            features['bwd_pkt_len_std'] = statistics.stdev(flow['bwd_pkt_lens']) if len(flow['bwd_pkt_lens']) > 1 else 0
        else:
            features['bwd_pkt_len_max'] = 0
            features['bwd_pkt_len_min'] = 0
            features['bwd_pkt_len_mean'] = 0
            features['bwd_pkt_len_std'] = 0
        
        # Flow bytes/packets per second
        if duration > 0:
            features['flow_bytes_per_sec'] = (flow['total_fwd_bytes'] + flow['total_bwd_bytes']) / duration
            features['flow_packets_per_sec'] = (flow['total_fwd_packets'] + flow['total_bwd_packets']) / duration
            features['fwd_packets_per_sec'] = flow['total_fwd_packets'] / duration
            features['bwd_packets_per_sec'] = flow['total_bwd_packets'] / duration
        else:
            features['flow_bytes_per_sec'] = 0
            features['flow_packets_per_sec'] = 0
            features['fwd_packets_per_sec'] = 0
            features['bwd_packets_per_sec'] = 0
        
        # Flow IAT statistics
        if flow['flow_iats']:
            features['flow_iat_mean'] = statistics.mean(flow['flow_iats'])
            features['flow_iat_std'] = statistics.stdev(flow['flow_iats']) if len(flow['flow_iats']) > 1 else 0
            features['flow_iat_max'] = max(flow['flow_iats'])
            features['flow_iat_min'] = min(flow['flow_iats'])
        else:
            features['flow_iat_mean'] = 0
            features['flow_iat_std'] = 0
            features['flow_iat_max'] = 0
            features['flow_iat_min'] = 0
        
        # Forward IAT statistics
        if flow['fwd_iats']:
            features['fwd_iat_total'] = sum(flow['fwd_iats'])
            features['fwd_iat_mean'] = statistics.mean(flow['fwd_iats'])
            features['fwd_iat_std'] = statistics.stdev(flow['fwd_iats']) if len(flow['fwd_iats']) > 1 else 0
            features['fwd_iat_max'] = max(flow['fwd_iats'])
            features['fwd_iat_min'] = min(flow['fwd_iats'])
        else:
            features['fwd_iat_total'] = 0
            features['fwd_iat_mean'] = 0
            features['fwd_iat_std'] = 0
            features['fwd_iat_max'] = 0
            features['fwd_iat_min'] = 0
        
        # Backward IAT statistics
        if flow['bwd_iats']:
            features['bwd_iat_total'] = sum(flow['bwd_iats'])
            features['bwd_iat_mean'] = statistics.mean(flow['bwd_iats'])
            features['bwd_iat_std'] = statistics.stdev(flow['bwd_iats']) if len(flow['bwd_iats']) > 1 else 0
            features['bwd_iat_max'] = max(flow['bwd_iats'])
            features['bwd_iat_min'] = min(flow['bwd_iats'])
        else:
            features['bwd_iat_total'] = 0
            features['bwd_iat_mean'] = 0
            features['bwd_iat_std'] = 0
            features['bwd_iat_max'] = 0
            features['bwd_iat_min'] = 0
        
        # TCP flags
        features['fin_flag_count'] = flow['fin_count']
        features['syn_flag_count'] = flow['syn_count']
        features['rst_flag_count'] = flow['rst_count']
        features['psh_flag_count'] = flow['psh_count']
        features['ack_flag_count'] = flow['ack_count']
        features['urg_flag_count'] = flow['urg_count']
        
        # Additional features (simplified versions)
        all_pkt_lens = flow['fwd_pkt_lens'] + flow['bwd_pkt_lens']
        if all_pkt_lens:
            features['pkt_len_min'] = min(all_pkt_lens)
            features['pkt_len_max'] = max(all_pkt_lens)
            features['pkt_len_mean'] = statistics.mean(all_pkt_lens)
            features['pkt_len_std'] = statistics.stdev(all_pkt_lens) if len(all_pkt_lens) > 1 else 0
            features['pkt_len_variance'] = statistics.variance(all_pkt_lens) if len(all_pkt_lens) > 1 else 0
        else:
            features['pkt_len_min'] = 0
            features['pkt_len_max'] = 0
            features['pkt_len_mean'] = 0
            features['pkt_len_std'] = 0
            features['pkt_len_variance'] = 0
        
        # Down/Up ratio
        if flow['total_fwd_packets'] > 0:
            features['down_up_ratio'] = flow['total_bwd_packets'] / flow['total_fwd_packets']
        else:
            features['down_up_ratio'] = 0
        
        # Average packet size
        total_packets = flow['total_fwd_packets'] + flow['total_bwd_packets']
        if total_packets > 0:
            features['avg_packet_size'] = (flow['total_fwd_bytes'] + flow['total_bwd_bytes']) / total_packets
        else:
            features['avg_packet_size'] = 0
        
        # Average segment sizes
        if flow['total_fwd_packets'] > 0:
            features['avg_fwd_segment_size'] = flow['total_fwd_bytes'] / flow['total_fwd_packets']
        else:
            features['avg_fwd_segment_size'] = 0
        
        if flow['total_bwd_packets'] > 0:
            features['avg_bwd_segment_size'] = flow['total_bwd_bytes'] / flow['total_bwd_packets']
        else:
            features['avg_bwd_segment_size'] = 0
        
        # Simplified bulk/subflow features (set to 0 for basic implementation)
        for feature_name in [
            'fwd_bulk_rate_avg', 'fwd_bulk_size_avg', 'fwd_bulk_packets_avg',
            'bwd_bulk_rate_avg', 'bwd_bulk_size_avg', 'bwd_bulk_packets_avg',
            'subflow_fwd_packets', 'subflow_fwd_bytes', 'subflow_bwd_packets', 'subflow_bwd_bytes',
            'init_fwd_win_bytes', 'init_bwd_win_bytes', 'act_data_pkt_fwd', 'min_seg_size_fwd',
            'active_mean', 'active_std', 'active_max', 'active_min',
            'idle_mean', 'idle_std', 'idle_max', 'idle_min',
            'fwd_psh_flags', 'bwd_psh_flags', 'fwd_urg_flags', 'bwd_urg_flags',
            'fwd_header_len', 'bwd_header_len', 'cwe_flag_count', 'ece_flag_count'
        ]:
            features[feature_name] = 0
        
        return features
    
    def get_completed_flows(self) -> List[dict]:
        """Get list of completed flows"""
        return self.completed_flows.copy()
    
    def clear_completed_flows(self):
        """Clear completed flows list"""
        self.completed_flows.clear()


# Example usage
if __name__ == "__main__":
    tracker = FlowTracker(timeout=60)
    
    # Example packet
    test_packet = {
        'packet_id': 1,
        'timestamp': datetime.now().isoformat(),
        'raw_length': 100,
        'ip': {
            'src': '192.168.1.100',
            'dst': '10.0.0.1'
        },
        'tcp': {
            'sport': 54321,
            'dport': 80,
            'flags': 'S'
        }
    }
    
    tracker.process_packet(test_packet)
    
    # Extract features from active flows
    for flow in tracker.flows.values():
        features = tracker.extract_features(flow)
        print(f"Extracted {len(features)} features")
        print(f"Duration: {features['duration']:.2f}s")
        print(f"Total packets: {features['total_fwd_packets'] + features['total_bwd_packets']}")
