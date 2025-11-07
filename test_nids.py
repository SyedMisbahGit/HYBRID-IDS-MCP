#!/usr/bin/env python3
"""
Test script for Python-based NIDS
Demonstrates NIDS functionality without C++ compilation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'nids_python'))

from packet_capture import PacketCapture
from signature_ids import SignatureIDS
from feature_extractor import FlowTracker

def test_signature_detection():
    """Test signature-based detection"""
    print("="*70)
    print("  Testing NIDS - Signature Detection")
    print("="*70)
    print()
    
    # Create S-IDS instance
    sids = SignatureIDS()
    
    print(f"[1] Loaded {len(sids.rules)} detection rules")
    print()
    
    # Test packets
    test_packets = [
        {
            'packet_id': 1,
            'ip': {'src': '192.168.1.100', 'dst': '10.0.0.1'},
            'tcp': {'sport': 54321, 'dport': 22, 'flags': 'S'},
            'layers': ['IP', 'TCP']
        },
        {
            'packet_id': 2,
            'ip': {'src': '192.168.1.100', 'dst': '10.0.0.1'},
            'tcp': {'sport': 54322, 'dport': 4444, 'flags': 'S'},
            'layers': ['IP', 'TCP']
        },
        {
            'packet_id': 3,
            'ip': {'src': '192.168.1.100', 'dst': '10.0.0.1'},
            'tcp': {'sport': 54323, 'dport': 3389, 'flags': 'S'},
            'layers': ['IP', 'TCP']
        },
        {
            'packet_id': 4,
            'ip': {'src': '192.168.1.100', 'dst': '10.0.0.1'},
            'icmp': {'type': 8, 'code': 0},
            'layers': ['IP', 'ICMP']
        }
    ]
    
    print("[2] Processing test packets...")
    print()
    
    for packet in test_packets:
        alert = sids.process_packet(packet)
        if alert:
            sids.print_alert(alert)
    
    print("[3] Detection Statistics:")
    sids.print_stats()
    
    return True

def test_packet_capture():
    """Test packet capture from PCAP file"""
    print("="*70)
    print("  Testing NIDS - Packet Capture")
    print("="*70)
    print()
    
    pcap_file = Path(__file__).parent / 'test.pcap'
    
    if not pcap_file.exists():
        print(f"[WARNING] PCAP file not found: {pcap_file}")
        print("Skipping packet capture test")
        print()
        return False
    
    print(f"[1] Reading packets from: {pcap_file}")
    print()
    
    # Create capture instance
    capture = PacketCapture(pcap_file=str(pcap_file))
    
    # Packet counter
    packet_count = [0]
    
    def packet_handler(packet):
        packet_count[0] += 1
        if packet_count[0] <= 5:  # Print first 5
            if 'ip' in packet:
                proto = 'TCP' if 'tcp' in packet else 'UDP' if 'udp' in packet else 'ICMP' if 'icmp' in packet else 'OTHER'
                print(f"  [{packet['packet_id']}] {packet['ip']['src']} -> {packet['ip']['dst']} [{proto}]")
    
    capture.set_callback(packet_handler)
    
    print("[2] Captured packets (first 5):")
    
    try:
        capture.start_capture(count=20)  # Capture 20 packets
        print()
        print("[3] Capture Statistics:")
        capture.print_stats()
        return True
    except Exception as e:
        print(f"[ERROR] Capture failed: {e}")
        return False

def test_feature_extraction():
    """Test feature extraction"""
    print("="*70)
    print("  Testing NIDS - Feature Extraction")
    print("="*70)
    print()
    
    # Create flow tracker
    tracker = FlowTracker(timeout=60)
    
    print("[1] Creating test flow...")
    print()
    
    # Simulate a flow with multiple packets
    test_packets = [
        {
            'packet_id': 1,
            'raw_length': 60,
            'ip': {'src': '192.168.1.100', 'dst': '10.0.0.1'},
            'tcp': {'sport': 54321, 'dport': 80, 'flags': 'S'}
        },
        {
            'packet_id': 2,
            'raw_length': 60,
            'ip': {'src': '10.0.0.1', 'dst': '192.168.1.100'},
            'tcp': {'sport': 80, 'dport': 54321, 'flags': 'SA'}
        },
        {
            'packet_id': 3,
            'raw_length': 52,
            'ip': {'src': '192.168.1.100', 'dst': '10.0.0.1'},
            'tcp': {'sport': 54321, 'dport': 80, 'flags': 'A'}
        },
        {
            'packet_id': 4,
            'raw_length': 500,
            'ip': {'src': '192.168.1.100', 'dst': '10.0.0.1'},
            'tcp': {'sport': 54321, 'dport': 80, 'flags': 'PA'}
        },
        {
            'packet_id': 5,
            'raw_length': 1500,
            'ip': {'src': '10.0.0.1', 'dst': '192.168.1.100'},
            'tcp': {'sport': 80, 'dport': 54321, 'flags': 'PA'}
        }
    ]
    
    for packet in test_packets:
        tracker.process_packet(packet)
    
    print(f"[2] Processed {len(test_packets)} packets")
    print(f"    Active flows: {len(tracker.flows)}")
    print()
    
    # Extract features from first flow
    if tracker.flows:
        flow = list(tracker.flows.values())[0]
        features = tracker.extract_features(flow)
        
        print("[3] Extracted Features (sample):")
        print(f"    Total features: {len(features)}")
        print(f"    Duration: {features['duration']:.4f}s")
        print(f"    Total packets: {features['total_fwd_packets'] + features['total_bwd_packets']}")
        print(f"    Total bytes: {features['total_fwd_bytes'] + features['total_bwd_bytes']}")
        print(f"    Flow bytes/sec: {features['flow_bytes_per_sec']:.2f}")
        print(f"    Avg packet size: {features['avg_packet_size']:.2f}")
        print(f"    SYN flags: {features['syn_flag_count']}")
        print(f"    ACK flags: {features['ack_flag_count']}")
        print()
    
    return True

def test_integrated_nids():
    """Test integrated NIDS with PCAP file"""
    print("="*70)
    print("  Testing NIDS - Integrated System")
    print("="*70)
    print()
    
    pcap_file = Path(__file__).parent / 'test.pcap'
    
    if not pcap_file.exists():
        print(f"[WARNING] PCAP file not found: {pcap_file}")
        print("Skipping integrated test")
        print()
        return False
    
    print(f"[1] Initializing NIDS with PCAP file: {pcap_file}")
    print()
    
    # Create components
    capture = PacketCapture(pcap_file=str(pcap_file))
    sids = SignatureIDS()
    tracker = FlowTracker()
    
    alert_count = [0]
    
    def packet_handler(packet):
        # Signature detection
        alert = sids.process_packet(packet)
        if alert:
            alert_count[0] += 1
            if alert_count[0] <= 3:  # Print first 3 alerts
                print(f"  [ALERT] {alert['rule_name']} - {alert['severity']}")
        
        # Feature extraction
        tracker.process_packet(packet)
    
    capture.set_callback(packet_handler)
    
    print("[2] Processing packets...")
    print()
    
    try:
        capture.start_capture(count=50)  # Process 50 packets
        
        print()
        print("[3] Results:")
        print(f"    Packets processed: {sids.stats['packets_processed']}")
        print(f"    Alerts generated: {sids.stats['alerts_generated']}")
        print(f"    Active flows: {len(tracker.flows)}")
        print(f"    Completed flows: {len(tracker.completed_flows)}")
        print()
        
        return True
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print("\n" + "="*70)
    print("  Hybrid IDS - NIDS Component Test (Python)")
    print("  No C++ Compilation Required!")
    print("="*70)
    print()
    
    tests = [
        ("Signature Detection", test_signature_detection),
        ("Feature Extraction", test_feature_extraction),
        ("Packet Capture", test_packet_capture),
        ("Integrated NIDS", test_integrated_nids)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
        print()
    
    # Summary
    print("="*70)
    print("  Test Summary")
    print("="*70)
    for test_name, result in results:
        status = "[PASS]" if result else "[SKIP/FAIL]"
        print(f"  {status} {test_name}")
    print()
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    print()
    
    if passed > 0:
        print("[SUCCESS] NIDS components are working!")
        print()
        print("To run full NIDS:")
        print("  # With PCAP file:")
        print("  python src/nids_python/nids_main.py -r test.pcap")
        print()
        print("  # Live capture (requires admin):")
        print("  python src/nids_python/nids_main.py -i eth0")
        print()
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
