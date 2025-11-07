#!/usr/bin/env python3
"""
Packet Capture Module for Python-based NIDS
Uses Scapy for packet capture and analysis
"""

import logging
from scapy.all import sniff, IP, TCP, UDP, ICMP, Raw, Ether
from scapy.layers.http import HTTP, HTTPRequest, HTTPResponse
from scapy.layers.dns import DNS, DNSQR, DNSRR
from datetime import datetime
from typing import Callable, Optional, List
import threading

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PacketCapture:
    """
    Packet capture engine using Scapy
    """
    
    def __init__(self, interface: Optional[str] = None, pcap_file: Optional[str] = None):
        """
        Initialize packet capture
        
        Args:
            interface: Network interface to capture from (e.g., 'eth0', 'Wi-Fi')
            pcap_file: PCAP file to read from (offline mode)
        """
        self.interface = interface
        self.pcap_file = pcap_file
        self.running = False
        self.packet_count = 0
        self.callback = None
        self.capture_thread = None
        
        self.stats = {
            'total_packets': 0,
            'ip_packets': 0,
            'tcp_packets': 0,
            'udp_packets': 0,
            'icmp_packets': 0,
            'http_packets': 0,
            'dns_packets': 0,
            'other_packets': 0,
            'bytes_captured': 0
        }
    
    def set_callback(self, callback: Callable):
        """
        Set callback function for packet processing
        
        Args:
            callback: Function to call for each packet
        """
        self.callback = callback
    
    def _process_packet(self, packet):
        """
        Process captured packet
        
        Args:
            packet: Scapy packet object
        """
        self.packet_count += 1
        self.stats['total_packets'] += 1
        
        try:
            # Get packet length
            if hasattr(packet, 'len'):
                self.stats['bytes_captured'] += packet.len
            elif hasattr(packet, '__len__'):
                self.stats['bytes_captured'] += len(packet)
            
            # Parse packet
            parsed = self._parse_packet(packet)
            
            # Update statistics
            if packet.haslayer(IP):
                self.stats['ip_packets'] += 1
            if packet.haslayer(TCP):
                self.stats['tcp_packets'] += 1
            if packet.haslayer(UDP):
                self.stats['udp_packets'] += 1
            if packet.haslayer(ICMP):
                self.stats['icmp_packets'] += 1
            if packet.haslayer(HTTP):
                self.stats['http_packets'] += 1
            if packet.haslayer(DNS):
                self.stats['dns_packets'] += 1
            
            # Call user callback
            if self.callback:
                self.callback(parsed)
                
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
            self.stats['other_packets'] += 1
    
    def _parse_packet(self, packet) -> dict:
        """
        Parse packet into dictionary format
        
        Args:
            packet: Scapy packet object
            
        Returns:
            Dictionary with packet information
        """
        parsed = {
            'timestamp': datetime.now().isoformat(),
            'packet_id': self.packet_count,
            'raw_length': len(packet) if hasattr(packet, '__len__') else 0,
            'layers': []
        }
        
        # Ethernet layer
        if packet.haslayer(Ether):
            eth = packet[Ether]
            parsed['eth'] = {
                'src_mac': eth.src,
                'dst_mac': eth.dst,
                'type': eth.type
            }
            parsed['layers'].append('Ethernet')
        
        # IP layer
        if packet.haslayer(IP):
            ip = packet[IP]
            parsed['ip'] = {
                'version': ip.version,
                'src': ip.src,
                'dst': ip.dst,
                'proto': ip.proto,
                'ttl': ip.ttl,
                'len': ip.len,
                'id': ip.id,
                'flags': str(ip.flags)
            }
            parsed['layers'].append('IP')
        
        # TCP layer
        if packet.haslayer(TCP):
            tcp = packet[TCP]
            parsed['tcp'] = {
                'sport': tcp.sport,
                'dport': tcp.dport,
                'seq': tcp.seq,
                'ack': tcp.ack,
                'flags': str(tcp.flags),
                'window': tcp.window,
                'dataofs': tcp.dataofs
            }
            parsed['layers'].append('TCP')
            
            # Check for HTTP
            if packet.haslayer(HTTPRequest):
                http_req = packet[HTTPRequest]
                parsed['http'] = {
                    'method': http_req.Method.decode() if http_req.Method else None,
                    'host': http_req.Host.decode() if http_req.Host else None,
                    'path': http_req.Path.decode() if http_req.Path else None,
                    'user_agent': http_req.User_Agent.decode() if http_req.User_Agent else None
                }
                parsed['layers'].append('HTTP')
        
        # UDP layer
        if packet.haslayer(UDP):
            udp = packet[UDP]
            parsed['udp'] = {
                'sport': udp.sport,
                'dport': udp.dport,
                'len': udp.len
            }
            parsed['layers'].append('UDP')
            
            # Check for DNS
            if packet.haslayer(DNS):
                dns = packet[DNS]
                parsed['dns'] = {
                    'id': dns.id,
                    'qr': dns.qr,
                    'opcode': dns.opcode,
                    'qdcount': dns.qdcount,
                    'ancount': dns.ancount
                }
                
                # DNS queries
                if dns.qd:
                    parsed['dns']['queries'] = []
                    if isinstance(dns.qd, list):
                        for q in dns.qd:
                            parsed['dns']['queries'].append({
                                'qname': q.qname.decode() if q.qname else None,
                                'qtype': q.qtype
                            })
                    else:
                        parsed['dns']['queries'].append({
                            'qname': dns.qd.qname.decode() if dns.qd.qname else None,
                            'qtype': dns.qd.qtype
                        })
                
                parsed['layers'].append('DNS')
        
        # ICMP layer
        if packet.haslayer(ICMP):
            icmp = packet[ICMP]
            parsed['icmp'] = {
                'type': icmp.type,
                'code': icmp.code,
                'id': icmp.id if hasattr(icmp, 'id') else None,
                'seq': icmp.seq if hasattr(icmp, 'seq') else None
            }
            parsed['layers'].append('ICMP')
        
        # Raw payload
        if packet.haslayer(Raw):
            raw = packet[Raw]
            parsed['payload_length'] = len(raw.load)
            # Store first 100 bytes of payload (hex)
            parsed['payload_preview'] = raw.load[:100].hex()
        else:
            parsed['payload_length'] = 0
        
        return parsed
    
    def start_capture(self, count: int = 0, timeout: Optional[int] = None):
        """
        Start packet capture
        
        Args:
            count: Number of packets to capture (0 = infinite)
            timeout: Timeout in seconds (None = no timeout)
        """
        self.running = True
        
        try:
            if self.pcap_file:
                # Offline capture from PCAP file
                logger.info(f"Reading packets from: {self.pcap_file}")
                sniff(
                    offline=self.pcap_file,
                    prn=self._process_packet,
                    count=count,
                    timeout=timeout,
                    store=False
                )
            else:
                # Live capture
                if self.interface:
                    logger.info(f"Starting live capture on interface: {self.interface}")
                else:
                    logger.info("Starting live capture on default interface")
                
                sniff(
                    iface=self.interface,
                    prn=self._process_packet,
                    count=count,
                    timeout=timeout,
                    store=False,
                    stop_filter=lambda x: not self.running
                )
        except PermissionError:
            logger.error("Permission denied. Run as Administrator or use a PCAP file.")
        except Exception as e:
            logger.error(f"Capture error: {e}")
        finally:
            self.running = False
            logger.info("Packet capture stopped")
    
    def start_capture_async(self, count: int = 0, timeout: Optional[int] = None):
        """
        Start packet capture in background thread
        
        Args:
            count: Number of packets to capture (0 = infinite)
            timeout: Timeout in seconds (None = no timeout)
        """
        self.capture_thread = threading.Thread(
            target=self.start_capture,
            args=(count, timeout),
            daemon=True
        )
        self.capture_thread.start()
        logger.info("Packet capture started in background")
    
    def stop_capture(self):
        """Stop packet capture"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
        logger.info("Packet capture stopped")
    
    def get_stats(self) -> dict:
        """Get capture statistics"""
        return self.stats.copy()
    
    def print_stats(self):
        """Print capture statistics"""
        print("\n" + "="*60)
        print("  Packet Capture Statistics")
        print("="*60)
        print(f"Total Packets:    {self.stats['total_packets']:>10}")
        print(f"IP Packets:       {self.stats['ip_packets']:>10}")
        print(f"TCP Packets:      {self.stats['tcp_packets']:>10}")
        print(f"UDP Packets:      {self.stats['udp_packets']:>10}")
        print(f"ICMP Packets:     {self.stats['icmp_packets']:>10}")
        print(f"HTTP Packets:     {self.stats['http_packets']:>10}")
        print(f"DNS Packets:      {self.stats['dns_packets']:>10}")
        print(f"Other Packets:    {self.stats['other_packets']:>10}")
        print(f"Bytes Captured:   {self.stats['bytes_captured']:>10}")
        print("="*60 + "\n")


# Example usage
if __name__ == "__main__":
    import sys
    
    def packet_handler(packet):
        """Example packet handler"""
        if 'ip' in packet:
            print(f"[{packet['packet_id']}] {packet['ip']['src']} -> {packet['ip']['dst']}")
    
    # Create capture instance
    if len(sys.argv) > 1:
        # Read from PCAP file
        capture = PacketCapture(pcap_file=sys.argv[1])
    else:
        # Live capture (requires admin)
        capture = PacketCapture()
    
    # Set callback
    capture.set_callback(packet_handler)
    
    # Start capture
    try:
        capture.start_capture(count=10)  # Capture 10 packets
        capture.print_stats()
    except KeyboardInterrupt:
        print("\nStopping capture...")
        capture.stop_capture()
