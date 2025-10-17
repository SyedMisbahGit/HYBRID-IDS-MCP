#ifndef HYBRID_IDS_TYPES_H
#define HYBRID_IDS_TYPES_H

#include <cstdint>
#include <string>
#include <vector>
#include <chrono>

namespace hybrid_ids {

// Packet protocols
enum class Protocol {
    UNKNOWN = 0,
    ETHERNET,
    IPV4,
    IPV6,
    TCP,
    UDP,
    ICMP,
    HTTP,
    DNS,
    TLS
};

// Alert severity levels
enum class Severity {
    LOW = 0,
    MEDIUM,
    HIGH,
    CRITICAL
};

// Packet headers
struct EthernetHeader {
    uint8_t dst_mac[6];
    uint8_t src_mac[6];
    uint16_t ethertype;
};

struct IPv4Header {
    uint8_t version_ihl;
    uint8_t tos;
    uint16_t total_length;
    uint16_t identification;
    uint16_t flags_fragment;
    uint8_t ttl;
    uint8_t protocol;
    uint16_t checksum;
    uint32_t src_ip;
    uint32_t dst_ip;
};

struct TCPHeader {
    uint16_t src_port;
    uint16_t dst_port;
    uint32_t seq_number;
    uint32_t ack_number;
    uint8_t data_offset;
    uint8_t flags;
    uint16_t window_size;
    uint16_t checksum;
    uint16_t urgent_pointer;
};

struct UDPHeader {
    uint16_t src_port;
    uint16_t dst_port;
    uint16_t length;
    uint16_t checksum;
};

// Parsed packet structure
struct ParsedPacket {
    // Timing
    std::chrono::system_clock::time_point timestamp;
    uint64_t packet_id;

    // Raw data
    const uint8_t* raw_data;
    uint32_t raw_length;

    // Headers
    EthernetHeader eth_header;
    IPv4Header ip_header;

    // Transport layer
    bool has_tcp;
    bool has_udp;
    TCPHeader tcp_header;
    UDPHeader udp_header;

    // Payload
    const uint8_t* payload;
    uint32_t payload_length;

    // Helper methods
    std::string get_src_ip() const;
    std::string get_dst_ip() const;
    uint16_t get_src_port() const;
    uint16_t get_dst_port() const;
    std::string get_protocol() const;
};

// Signature rule structure
struct SignatureRule {
    uint32_t rule_id;
    std::string name;
    std::string description;
    Protocol protocol;

    // IP filters
    std::string src_ip_filter;    // e.g., "192.168.1.0/24" or "any"
    std::string dst_ip_filter;

    // Port filters
    std::vector<uint16_t> src_ports;
    std::vector<uint16_t> dst_ports;

    // TCP flags
    uint8_t tcp_flags_mask;       // Which flags to check
    uint8_t tcp_flags_value;      // Expected flag values

    // Content patterns
    std::vector<std::string> content_patterns;  // Strings to search for
    std::vector<std::string> regex_patterns;    // Regex patterns

    // Metadata
    Severity severity;
    std::string action;           // "alert", "log", "drop"
    bool enabled;
};

// Alert structure
struct Alert {
    uint64_t alert_id;
    std::chrono::system_clock::time_point timestamp;

    uint32_t rule_id;
    std::string rule_name;
    Severity severity;

    // Packet info
    uint64_t packet_id;
    std::string src_ip;
    std::string dst_ip;
    uint16_t src_port;
    uint16_t dst_port;
    std::string protocol;

    // Details
    std::string description;
    std::string matched_content;

    std::string to_string() const;
    std::string to_json() const;
};

// Statistics structure
struct Statistics {
    uint64_t total_packets;
    uint64_t total_bytes;
    uint64_t tcp_packets;
    uint64_t udp_packets;
    uint64_t icmp_packets;
    uint64_t other_packets;

    uint64_t alerts_generated;
    uint64_t alerts_by_severity[4];  // LOW, MEDIUM, HIGH, CRITICAL

    double packets_per_second;
    double mbits_per_second;

    std::chrono::system_clock::time_point start_time;
    std::chrono::system_clock::time_point last_update;

    void update();
    void print() const;
    std::string to_string() const;
};

} // namespace hybrid_ids

#endif // HYBRID_IDS_TYPES_H
