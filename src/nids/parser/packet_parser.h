#ifndef HYBRID_IDS_PACKET_PARSER_H
#define HYBRID_IDS_PACKET_PARSER_H

#include "../common/types.h"
#include <memory>

namespace hybrid_ids {

/**
 * @brief High-performance packet parser for network protocols
 *
 * Parses Ethernet, IP, TCP, UDP headers and extracts payload.
 * Optimized for speed with minimal memory allocations.
 */
class PacketParser {
public:
    PacketParser();
    ~PacketParser() = default;

    /**
     * @brief Parse raw packet data
     *
     * @param data Raw packet bytes
     * @param length Packet length in bytes
     * @param timestamp Capture timestamp
     * @return Parsed packet structure
     */
    ParsedPacket parse(const uint8_t* data, uint32_t length,
                      const std::chrono::system_clock::time_point& timestamp);

    /**
     * @brief Check if packet has valid Ethernet header
     */
    bool has_ethernet(const uint8_t* data, uint32_t length) const;

    /**
     * @brief Check if packet has valid IPv4 header
     */
    bool has_ipv4(const uint8_t* data, uint32_t length) const;

    // Statistics
    uint64_t get_packets_parsed() const { return packets_parsed_; }
    uint64_t get_parse_errors() const { return parse_errors_; }

private:
    // Parsing methods
    bool parse_ethernet(const uint8_t* data, uint32_t length, ParsedPacket& packet);
    bool parse_ipv4(const uint8_t* data, uint32_t length, ParsedPacket& packet);
    bool parse_tcp(const uint8_t* data, uint32_t length, ParsedPacket& packet);
    bool parse_udp(const uint8_t* data, uint32_t length, ParsedPacket& packet);

    // Validation
    bool validate_packet(const uint8_t* data, uint32_t length) const;

    // Statistics
    uint64_t packets_parsed_;
    uint64_t parse_errors_;
    uint64_t next_packet_id_;
};

} // namespace hybrid_ids

#endif // HYBRID_IDS_PACKET_PARSER_H
