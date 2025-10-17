#include "protocol_decoder.h"
#include <sstream>
#include <algorithm>
#include <cstring>

namespace hybrid_ids {

ProtocolDecoder::ProtocolDecoder()
    : http_decoded_(0)
    , dns_decoded_(0)
    , decode_errors_(0) {
}

bool ProtocolDecoder::is_http(const uint8_t* payload, uint32_t length) const {
    if (length < 4) return false;

    // Check for HTTP methods or version
    const char* data = reinterpret_cast<const char*>(payload);
    return (strncmp(data, "GET ", 4) == 0 ||
            strncmp(data, "POST", 4) == 0 ||
            strncmp(data, "HEAD", 4) == 0 ||
            strncmp(data, "PUT ", 4) == 0 ||
            strncmp(data, "HTTP", 4) == 0);
}

bool ProtocolDecoder::is_dns(const uint8_t* payload, uint32_t length) const {
    if (length < 12) return false;

    // DNS header is at least 12 bytes
    // Check if it looks reasonable (simple heuristic)
    uint16_t flags = (payload[2] << 8) | payload[3];
    uint16_t qd_count = (payload[4] << 8) | payload[5];

    // Check if QR bit makes sense and question count is reasonable
    return (qd_count > 0 && qd_count < 100);
}

bool ProtocolDecoder::decode_http(const uint8_t* payload, uint32_t length, HTTPData& http) {
    if (!is_http(payload, length)) {
        decode_errors_++;
        return false;
    }

    // Convert to string for easier parsing
    std::string data(reinterpret_cast<const char*>(payload), length);

    // Check if request or response
    if (data.substr(0, 4) == "HTTP") {
        http.is_response = true;
        http.is_request = false;
        if (!parse_http_response(data, http)) {
            decode_errors_++;
            return false;
        }
    } else {
        http.is_request = true;
        http.is_response = false;
        if (!parse_http_request(data, http)) {
            decode_errors_++;
            return false;
        }
    }

    http_decoded_++;
    return true;
}

bool ProtocolDecoder::parse_http_request(const std::string& data, HTTPData& http) {
    // Find first line
    size_t first_line_end = data.find("\r\n");
    if (first_line_end == std::string::npos) {
        first_line_end = data.find("\n");
    }

    if (first_line_end == std::string::npos) {
        return false;
    }

    std::string first_line = data.substr(0, first_line_end);

    // Parse "METHOD URI VERSION"
    std::istringstream iss(first_line);
    iss >> http.method >> http.uri >> http.version;

    // Find headers section
    size_t header_start = first_line_end + 2;  // Skip \r\n
    size_t body_start = data.find("\r\n\r\n", header_start);

    if (body_start == std::string::npos) {
        body_start = data.find("\n\n", header_start);
        if (body_start != std::string::npos) {
            body_start += 2;
        }
    } else {
        body_start += 4;
    }

    // Parse headers
    if (body_start != std::string::npos && body_start > header_start) {
        std::string headers_section = data.substr(header_start, body_start - header_start - 4);
        parse_http_headers(headers_section, http);

        // Body (if any)
        if (body_start < data.length()) {
            http.body = data.substr(body_start);
            http.content_length = http.body.length();
        }
    }

    return true;
}

bool ProtocolDecoder::parse_http_response(const std::string& data, HTTPData& http) {
    // Find first line
    size_t first_line_end = data.find("\r\n");
    if (first_line_end == std::string::npos) {
        first_line_end = data.find("\n");
    }

    if (first_line_end == std::string::npos) {
        return false;
    }

    std::string first_line = data.substr(0, first_line_end);

    // Parse "HTTP/version code message"
    std::istringstream iss(first_line);
    iss >> http.version >> http.status_code;
    std::getline(iss, http.status_message);

    // Trim leading space
    if (!http.status_message.empty() && http.status_message[0] == ' ') {
        http.status_message = http.status_message.substr(1);
    }

    // Parse headers (similar to request)
    size_t header_start = first_line_end + 2;
    size_t body_start = data.find("\r\n\r\n", header_start);

    if (body_start == std::string::npos) {
        body_start = data.find("\n\n", header_start);
        if (body_start != std::string::npos) {
            body_start += 2;
        }
    } else {
        body_start += 4;
    }

    if (body_start != std::string::npos && body_start > header_start) {
        std::string headers_section = data.substr(header_start, body_start - header_start - 4);
        parse_http_headers(headers_section, http);

        if (body_start < data.length()) {
            http.body = data.substr(body_start);
            http.content_length = http.body.length();
        }
    }

    return true;
}

void ProtocolDecoder::parse_http_headers(const std::string& header_section, HTTPData& http) {
    std::istringstream iss(header_section);
    std::string line;

    while (std::getline(iss, line)) {
        // Remove \r if present
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        size_t colon = line.find(':');
        if (colon != std::string::npos) {
            std::string key = line.substr(0, colon);
            std::string value = line.substr(colon + 1);

            // Trim leading/trailing spaces
            key.erase(0, key.find_first_not_of(" \t"));
            key.erase(key.find_last_not_of(" \t") + 1);
            value.erase(0, value.find_first_not_of(" \t"));
            value.erase(value.find_last_not_of(" \t") + 1);

            // Convert key to lowercase
            std::transform(key.begin(), key.end(), key.begin(), ::tolower);

            http.headers[key] = value;

            // Check for Content-Length
            if (key == "content-length") {
                http.content_length = std::stoul(value);
            }
        }
    }
}

bool ProtocolDecoder::decode_dns(const uint8_t* payload, uint32_t length, DNSData& dns) {
    if (!is_dns(payload, length)) {
        decode_errors_++;
        return false;
    }

    // Parse DNS header (12 bytes minimum)
    dns.transaction_id = read_uint16(payload, 0);
    dns.flags = read_uint16(payload, 2);

    uint16_t qd_count = read_uint16(payload, 4);
    dns.answer_count = read_uint16(payload, 6);
    dns.authority_count = read_uint16(payload, 8);
    dns.additional_count = read_uint16(payload, 10);

    // Check QR bit (bit 15 of flags)
    dns.is_query = (dns.flags & 0x8000) == 0;
    dns.is_response = !dns.is_query;

    // Parse question section (at offset 12)
    uint32_t offset = 12;

    if (qd_count > 0 && offset < length) {
        // Parse query name
        dns.query_name = parse_dns_name(payload, offset, length);

        // Parse query type and class
        if (offset + 4 <= length) {
            dns.query_type = read_uint16(payload, offset);
            offset += 2;
            dns.query_class = read_uint16(payload, offset);
            offset += 2;
        }
    }

    // Parse answers (simplified - just count them)
    // Full parsing would require handling compression pointers
    dns.answers.clear();
    for (int i = 0; i < dns.answer_count && offset < length; i++) {
        // Skip name (compressed pointer or labels)
        if (offset < length && (payload[offset] & 0xC0) == 0xC0) {
            offset += 2;  // Compression pointer
        } else {
            // Skip labels
            while (offset < length && payload[offset] != 0) {
                offset += payload[offset] + 1;
            }
            offset++;  // Skip null terminator
        }

        // Skip type, class, TTL, data length, data
        if (offset + 10 <= length) {
            uint16_t data_len = read_uint16(payload, offset + 8);
            offset += 10 + data_len;
        }
    }

    dns_decoded_++;
    return true;
}

std::string ProtocolDecoder::parse_dns_name(const uint8_t* data, uint32_t& offset, uint32_t max_length) {
    std::string name;
    bool jumped = false;
    uint32_t original_offset = offset;

    while (offset < max_length) {
        uint8_t len = data[offset];

        if (len == 0) {
            offset++;
            break;
        }

        // Check for compression pointer (top 2 bits set)
        if ((len & 0xC0) == 0xC0) {
            if (!jumped) {
                original_offset = offset + 2;
            }
            jumped = true;

            // Calculate pointer offset
            uint16_t pointer = ((len & 0x3F) << 8) | data[offset + 1];
            offset = pointer;
            continue;
        }

        // Read label
        offset++;
        if (offset + len > max_length) {
            break;
        }

        if (!name.empty()) {
            name += ".";
        }

        name += std::string(reinterpret_cast<const char*>(data + offset), len);
        offset += len;
    }

    if (jumped) {
        offset = original_offset;
    }

    return name;
}

uint16_t ProtocolDecoder::read_uint16(const uint8_t* data, uint32_t offset) {
    return (data[offset] << 8) | data[offset + 1];
}

} // namespace hybrid_ids
