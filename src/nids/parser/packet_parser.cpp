#include "packet_parser.h"
#include <cstring>
#include <arpa/inet.h>
#include <netinet/if_ether.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>

namespace hybrid_ids {

// Ethernet header size
constexpr size_t ETHER_HDR_SIZE = 14;

// IPv4 protocols
constexpr uint8_t IPPROTO_TCP_NUM = 6;
constexpr uint8_t IPPROTO_UDP_NUM = 17;
constexpr uint8_t IPPROTO_ICMP_NUM = 1;

PacketParser::PacketParser()
    : packets_parsed_(0)
    , parse_errors_(0)
    , next_packet_id_(1) {
}

ParsedPacket PacketParser::parse(const uint8_t* data, uint32_t length,
                                 const std::chrono::system_clock::time_point& timestamp) {
    ParsedPacket packet = {};
    packet.timestamp = timestamp;
    packet.packet_id = next_packet_id_++;
    packet.raw_data = data;
    packet.raw_length = length;

    // Validate minimum packet size
    if (!validate_packet(data, length)) {
        parse_errors_++;
        return packet;
    }

    // Parse layers
    if (!parse_ethernet(data, length, packet)) {
        parse_errors_++;
        return packet;
    }

    if (!parse_ipv4(data + ETHER_HDR_SIZE, length - ETHER_HDR_SIZE, packet)) {
        parse_errors_++;
        return packet;
    }

    // Parse transport layer
    uint8_t ip_header_length = (packet.ip_header.version_ihl & 0x0F) * 4;
    const uint8_t* transport_data = data + ETHER_HDR_SIZE + ip_header_length;
    uint32_t transport_length = length - ETHER_HDR_SIZE - ip_header_length;

    if (packet.ip_header.protocol == IPPROTO_TCP_NUM) {
        if (parse_tcp(transport_data, transport_length, packet)) {
            packet.has_tcp = true;
        }
    } else if (packet.ip_header.protocol == IPPROTO_UDP_NUM) {
        if (parse_udp(transport_data, transport_length, packet)) {
            packet.has_udp = true;
        }
    }

    packets_parsed_++;
    return packet;
}

bool PacketParser::validate_packet(const uint8_t* data, uint32_t length) const {
    // Minimum size: Ethernet (14) + IP (20) = 34 bytes
    return (data != nullptr && length >= 34);
}

bool PacketParser::has_ethernet(const uint8_t* data, uint32_t length) const {
    return length >= ETHER_HDR_SIZE;
}

bool PacketParser::has_ipv4(const uint8_t* data, uint32_t length) const {
    if (length < ETHER_HDR_SIZE + 20) return false;

    const uint8_t* ip_data = data + ETHER_HDR_SIZE;
    uint8_t version = (ip_data[0] >> 4) & 0x0F;
    return version == 4;
}

bool PacketParser::parse_ethernet(const uint8_t* data, uint32_t length, ParsedPacket& packet) {
    if (length < ETHER_HDR_SIZE) return false;

    // Copy MAC addresses
    memcpy(packet.eth_header.dst_mac, data, 6);
    memcpy(packet.eth_header.src_mac, data + 6, 6);

    // Ethertype (big endian)
    packet.eth_header.ethertype = (data[12] << 8) | data[13];

    // Check if IPv4 (0x0800)
    return packet.eth_header.ethertype == 0x0800;
}

bool PacketParser::parse_ipv4(const uint8_t* data, uint32_t length, ParsedPacket& packet) {
    if (length < 20) return false;

    // Version and IHL
    packet.ip_header.version_ihl = data[0];
    uint8_t version = (data[0] >> 4) & 0x0F;
    if (version != 4) return false;

    // Type of Service
    packet.ip_header.tos = data[1];

    // Total length (big endian)
    packet.ip_header.total_length = (data[2] << 8) | data[3];

    // Identification
    packet.ip_header.identification = (data[4] << 8) | data[5];

    // Flags and fragment offset
    packet.ip_header.flags_fragment = (data[6] << 8) | data[7];

    // TTL
    packet.ip_header.ttl = data[8];

    // Protocol
    packet.ip_header.protocol = data[9];

    // Checksum
    packet.ip_header.checksum = (data[10] << 8) | data[11];

    // Source IP (already in network byte order)
    memcpy(&packet.ip_header.src_ip, data + 12, 4);

    // Destination IP (already in network byte order)
    memcpy(&packet.ip_header.dst_ip, data + 16, 4);

    return true;
}

bool PacketParser::parse_tcp(const uint8_t* data, uint32_t length, ParsedPacket& packet) {
    if (length < 20) return false;

    // Source port (big endian)
    packet.tcp_header.src_port = (data[0] << 8) | data[1];

    // Destination port (big endian)
    packet.tcp_header.dst_port = (data[2] << 8) | data[3];

    // Sequence number
    packet.tcp_header.seq_number = (data[4] << 24) | (data[5] << 16) |
                                    (data[6] << 8) | data[7];

    // Acknowledgment number
    packet.tcp_header.ack_number = (data[8] << 24) | (data[9] << 16) |
                                    (data[10] << 8) | data[11];

    // Data offset (upper 4 bits of byte 12)
    packet.tcp_header.data_offset = (data[12] >> 4) & 0x0F;

    // Flags (lower 6 bits of byte 13)
    packet.tcp_header.flags = data[13] & 0x3F;

    // Window size
    packet.tcp_header.window_size = (data[14] << 8) | data[15];

    // Checksum
    packet.tcp_header.checksum = (data[16] << 8) | data[17];

    // Urgent pointer
    packet.tcp_header.urgent_pointer = (data[18] << 8) | data[19];

    // Calculate payload offset
    uint32_t tcp_header_length = packet.tcp_header.data_offset * 4;
    if (length > tcp_header_length) {
        packet.payload = data + tcp_header_length;
        packet.payload_length = length - tcp_header_length;
    } else {
        packet.payload = nullptr;
        packet.payload_length = 0;
    }

    return true;
}

bool PacketParser::parse_udp(const uint8_t* data, uint32_t length, ParsedPacket& packet) {
    if (length < 8) return false;

    // Source port (big endian)
    packet.udp_header.src_port = (data[0] << 8) | data[1];

    // Destination port (big endian)
    packet.udp_header.dst_port = (data[2] << 8) | data[3];

    // Length
    packet.udp_header.length = (data[4] << 8) | data[5];

    // Checksum
    packet.udp_header.checksum = (data[6] << 8) | data[7];

    // Payload
    if (length > 8) {
        packet.payload = data + 8;
        packet.payload_length = length - 8;
    } else {
        packet.payload = nullptr;
        packet.payload_length = 0;
    }

    return true;
}

} // namespace hybrid_ids
