#!/usr/bin/env python3
"""
Generate test network traffic PCAP file for S-IDS testing
"""

import struct
import time
import sys

def write_pcap_header(f):
    """Write PCAP file header"""
    magic = 0xa1b2c3d4
    version_major = 2
    version_minor = 4
    thiszone = 0
    sigfigs = 0
    snaplen = 65535
    network = 1  # Ethernet

    header = struct.pack('<IHHIIII',
                         magic, version_major, version_minor,
                         thiszone, sigfigs, snaplen, network)
    f.write(header)

def write_packet(f, packet_data, timestamp=None):
    """Write a packet to PCAP file"""
    if timestamp is None:
        timestamp = time.time()

    ts_sec = int(timestamp)
    ts_usec = int((timestamp - ts_sec) * 1000000)
    incl_len = len(packet_data)
    orig_len = len(packet_data)

    pkt_header = struct.pack('<IIII', ts_sec, ts_usec, incl_len, orig_len)
    f.write(pkt_header + packet_data)

def ip_to_bytes(ip_str):
    """Convert IP string to bytes"""
    parts = [int(x) for x in ip_str.split('.')]
    return bytes(parts)

def create_ethernet_header(src_mac, dst_mac, ethertype=0x0800):
    """Create Ethernet header"""
    return dst_mac + src_mac + struct.pack('>H', ethertype)

def create_ip_header(src_ip, dst_ip, protocol, payload_len):
    """Create IPv4 header"""
    version_ihl = 0x45  # Version 4, IHL 5 (20 bytes)
    tos = 0
    total_length = 20 + payload_len  # IP header + payload
    identification = 0x1234
    flags_fragment = 0
    ttl = 64
    checksum = 0  # Will be calculated later (simplified here)

    header = struct.pack('>BBHHHBBH',
                         version_ihl, tos, total_length,
                         identification, flags_fragment,
                         ttl, protocol, checksum)

    header += ip_to_bytes(src_ip)
    header += ip_to_bytes(dst_ip)

    return header

def create_tcp_header(src_port, dst_port, flags, payload_len):
    """Create TCP header"""
    seq = 0x12345678
    ack = 0x87654321
    data_offset = 0x50  # 5 * 4 = 20 bytes
    window = 0xFFFF
    checksum = 0
    urgent = 0

    header = struct.pack('>HHIIBBHHH',
                         src_port, dst_port,
                         seq, ack,
                         data_offset, flags,
                         window, checksum, urgent)

    return header

def create_udp_header(src_port, dst_port, payload_len):
    """Create UDP header"""
    length = 8 + payload_len
    checksum = 0

    header = struct.pack('>HHHH',
                         src_port, dst_port,
                         length, checksum)

    return header

def generate_test_pcap(filename):
    """Generate test PCAP with various traffic patterns"""
    print(f"[INFO] Generating test PCAP: {filename}")

    with open(filename, 'wb') as f:
        write_pcap_header(f)

        # MAC addresses
        src_mac = b'\x00\x11\x22\x33\x44\x55'
        dst_mac = b'\x00\xAA\xBB\xCC\xDD\xEE'

        timestamp = time.time()

        print("[INFO] Creating packets...")

        # 1. Normal HTTP traffic
        print("  - HTTP GET request")
        payload = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
        tcp_header = create_tcp_header(52341, 80, 0x18, len(payload))  # PSH+ACK
        ip_header = create_ip_header("192.168.1.100", "93.184.216.34", 6, 20 + len(payload))
        eth_header = create_ethernet_header(src_mac, dst_mac)
        packet = eth_header + ip_header + tcp_header + payload
        write_packet(f, packet, timestamp)
        timestamp += 0.001

        # 2. SQL Injection attempt (triggers alert)
        print("  - SQL Injection attempt")
        payload = b"GET /login.php?user=admin' OR '1'='1 HTTP/1.1\r\nHost: example.com\r\n\r\n"
        tcp_header = create_tcp_header(52342, 80, 0x18, len(payload))
        ip_header = create_ip_header("10.0.0.50", "192.168.1.10", 6, 20 + len(payload))
        eth_header = create_ethernet_header(src_mac, dst_mac)
        packet = eth_header + ip_header + tcp_header + payload
        write_packet(f, packet, timestamp)
        timestamp += 0.01

        # 3. Port scan - SYN packets to multiple ports
        print("  - Port scan (SYN packets)")
        for port in [21, 22, 23, 25, 80, 443, 3389, 8080]:
            tcp_header = create_tcp_header(12345, port, 0x02, 0)  # SYN flag
            ip_header = create_ip_header("10.0.0.50", "192.168.1.100", 6, 20)
            eth_header = create_ethernet_header(src_mac, dst_mac)
            packet = eth_header + ip_header + tcp_header
            write_packet(f, packet, timestamp)
            timestamp += 0.001

        # 4. SSH connection attempts
        print("  - SSH connection attempts")
        for i in range(5):
            tcp_header = create_tcp_header(10000 + i, 22, 0x02, 0)  # SYN
            ip_header = create_ip_header("172.16.0.50", "192.168.1.200", 6, 20)
            eth_header = create_ethernet_header(src_mac, dst_mac)
            packet = eth_header + ip_header + tcp_header
            write_packet(f, packet, timestamp)
            timestamp += 0.5

        # 5. FTP authentication
        print("  - FTP authentication")
        payload = b"USER anonymous\r\n"
        tcp_header = create_tcp_header(52343, 21, 0x18, len(payload))
        ip_header = create_ip_header("192.168.1.100", "192.168.1.10", 6, 20 + len(payload))
        eth_header = create_ethernet_header(src_mac, dst_mac)
        packet = eth_header + ip_header + tcp_header + payload
        write_packet(f, packet, timestamp)
        timestamp += 0.1

        payload = b"PASS password123\r\n"
        tcp_header = create_tcp_header(52343, 21, 0x18, len(payload))
        ip_header = create_ip_header("192.168.1.100", "192.168.1.10", 6, 20 + len(payload))
        eth_header = create_ethernet_header(src_mac, dst_mac)
        packet = eth_header + ip_header + tcp_header + payload
        write_packet(f, packet, timestamp)
        timestamp += 0.1

        # 6. DNS queries (UDP)
        print("  - DNS queries")
        for domain in [b"example.com", b"google.com", b"github.com"]:
            payload = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00' + domain
            udp_header = create_udp_header(52344, 53, len(payload))
            ip_header = create_ip_header("192.168.1.100", "8.8.8.8", 17, 8 + len(payload))
            eth_header = create_ethernet_header(src_mac, dst_mac)
            packet = eth_header + ip_header + udp_header + payload
            write_packet(f, packet, timestamp)
            timestamp += 0.05

        # 7. Telnet connection
        print("  - Telnet connection")
        tcp_header = create_tcp_header(52345, 23, 0x02, 0)  # SYN
        ip_header = create_ip_header("192.168.1.100", "10.0.0.10", 6, 20)
        eth_header = create_ethernet_header(src_mac, dst_mac)
        packet = eth_header + ip_header + tcp_header
        write_packet(f, packet, timestamp)
        timestamp += 0.1

        # 8. More SQL injection variants
        print("  - More SQL injection attempts")
        sql_payloads = [
            b"GET /search?q=1 UNION SELECT * FROM users HTTP/1.1\r\n\r\n",
            b"POST /login HTTP/1.1\r\nContent-Length: 30\r\n\r\nuser=admin&pass=' or 1=1--",
        ]
        for payload in sql_payloads:
            tcp_header = create_tcp_header(52346, 8080, 0x18, len(payload))
            ip_header = create_ip_header("10.0.0.50", "192.168.1.10", 6, 20 + len(payload))
            eth_header = create_ethernet_header(src_mac, dst_mac)
            packet = eth_header + ip_header + tcp_header + payload
            write_packet(f, packet, timestamp)
            timestamp += 0.1

    print(f"[SUCCESS] Generated test PCAP: {filename}")
    print(f"[INFO] The PCAP contains:")
    print("  - Normal HTTP traffic")
    print("  - SQL injection attempts (should trigger alerts)")
    print("  - Port scans (should trigger alerts)")
    print("  - SSH connection attempts (should trigger alerts)")
    print("  - FTP authentication (should trigger alerts)")
    print("  - DNS queries")
    print("  - Telnet connection (should trigger alert)")

if __name__ == "__main__":
    output_file = "test_traffic.pcap"
    if len(sys.argv) > 1:
        output_file = sys.argv[1]

    generate_test_pcap(output_file)
    print(f"\n[INFO] Test the S-IDS with:")
    print(f"  ./build/sids -r {output_file}")
