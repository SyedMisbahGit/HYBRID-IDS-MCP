#ifndef HYBRID_IDS_PROTOCOL_DECODER_H
#define HYBRID_IDS_PROTOCOL_DECODER_H

#include "../common/types.h"
#include <string>
#include <unordered_map>
#include <vector>

namespace hybrid_ids {

/**
 * @brief HTTP request/response structure
 */
struct HTTPData {
    // Request
    std::string method;           // GET, POST, etc.
    std::string uri;              // Request URI
    std::string version;          // HTTP/1.1, etc.
    std::unordered_map<std::string, std::string> headers;
    std::string body;

    // Response
    int status_code;              // 200, 404, etc.
    std::string status_message;   // OK, Not Found, etc.

    // Metadata
    bool is_request;
    bool is_response;
    size_t content_length;
};

/**
 * @brief DNS query/response structure
 */
struct DNSData {
    uint16_t transaction_id;
    bool is_query;
    bool is_response;
    uint16_t flags;

    // Query
    std::string query_name;
    uint16_t query_type;          // A, AAAA, MX, etc.
    uint16_t query_class;

    // Response
    std::vector<std::string> answers;
    uint16_t answer_count;
    uint16_t authority_count;
    uint16_t additional_count;
};

/**
 * @brief Protocol decoder for application-layer protocols
 */
class ProtocolDecoder {
public:
    ProtocolDecoder();
    ~ProtocolDecoder() = default;

    /**
     * @brief Decode HTTP traffic
     */
    bool decode_http(const uint8_t* payload, uint32_t length, HTTPData& http);

    /**
     * @brief Decode DNS traffic
     */
    bool decode_dns(const uint8_t* payload, uint32_t length, DNSData& dns);

    /**
     * @brief Check if payload looks like HTTP
     */
    bool is_http(const uint8_t* payload, uint32_t length) const;

    /**
     * @brief Check if payload looks like DNS
     */
    bool is_dns(const uint8_t* payload, uint32_t length) const;

    // Statistics
    uint64_t get_http_decoded() const { return http_decoded_; }
    uint64_t get_dns_decoded() const { return dns_decoded_; }
    uint64_t get_decode_errors() const { return decode_errors_; }

private:
    // HTTP parsing helpers
    bool parse_http_request(const std::string& data, HTTPData& http);
    bool parse_http_response(const std::string& data, HTTPData& http);
    void parse_http_headers(const std::string& header_section, HTTPData& http);

    // DNS parsing helpers
    std::string parse_dns_name(const uint8_t* data, uint32_t& offset, uint32_t max_length);
    uint16_t read_uint16(const uint8_t* data, uint32_t offset);

    // Statistics
    uint64_t http_decoded_;
    uint64_t dns_decoded_;
    uint64_t decode_errors_;
};

} // namespace hybrid_ids

#endif // HYBRID_IDS_PROTOCOL_DECODER_H
