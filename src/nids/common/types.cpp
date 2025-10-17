#include "types.h"
#include <sstream>
#include <iomanip>
#include <arpa/inet.h>

namespace hybrid_ids {

// ParsedPacket helper methods
std::string ParsedPacket::get_src_ip() const {
    char ip_str[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &ip_header.src_ip, ip_str, INET_ADDRSTRLEN);
    return std::string(ip_str);
}

std::string ParsedPacket::get_dst_ip() const {
    char ip_str[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &ip_header.dst_ip, ip_str, INET_ADDRSTRLEN);
    return std::string(ip_str);
}

uint16_t ParsedPacket::get_src_port() const {
    if (has_tcp) return ntohs(tcp_header.src_port);
    if (has_udp) return ntohs(udp_header.src_port);
    return 0;
}

uint16_t ParsedPacket::get_dst_port() const {
    if (has_tcp) return ntohs(tcp_header.dst_port);
    if (has_udp) return ntohs(udp_header.dst_port);
    return 0;
}

std::string ParsedPacket::get_protocol() const {
    if (has_tcp) return "TCP";
    if (has_udp) return "UDP";
    return "OTHER";
}

// Alert methods
std::string Alert::to_string() const {
    std::stringstream ss;

    // Timestamp
    auto time_t_val = std::chrono::system_clock::to_time_t(timestamp);
    ss << "[" << std::put_time(std::localtime(&time_t_val), "%Y-%m-%d %H:%M:%S") << "] ";

    // Severity
    const char* severity_str[] = {"LOW", "MEDIUM", "HIGH", "CRITICAL"};
    ss << "[" << severity_str[static_cast<int>(severity)] << "] ";

    // Rule info
    ss << rule_name << " (Rule ID: " << rule_id << ")\n";

    // Connection info
    ss << "  " << src_ip << ":" << src_port
       << " -> " << dst_ip << ":" << dst_port
       << " [" << protocol << "]\n";

    // Description
    ss << "  " << description << "\n";

    if (!matched_content.empty()) {
        ss << "  Matched: " << matched_content << "\n";
    }

    return ss.str();
}

std::string Alert::to_json() const {
    std::stringstream ss;
    auto time_t_val = std::chrono::system_clock::to_time_t(timestamp);
    char time_buf[32];
    strftime(time_buf, sizeof(time_buf), "%Y-%m-%dT%H:%M:%SZ", gmtime(&time_t_val));

    const char* severity_str[] = {"low", "medium", "high", "critical"};

    ss << "{"
       << "\"alert_id\":" << alert_id << ","
       << "\"timestamp\":\"" << time_buf << "\","
       << "\"rule_id\":" << rule_id << ","
       << "\"rule_name\":\"" << rule_name << "\","
       << "\"severity\":\"" << severity_str[static_cast<int>(severity)] << "\","
       << "\"src_ip\":\"" << src_ip << "\","
       << "\"src_port\":" << src_port << ","
       << "\"dst_ip\":\"" << dst_ip << "\","
       << "\"dst_port\":" << dst_port << ","
       << "\"protocol\":\"" << protocol << "\","
       << "\"description\":\"" << description << "\""
       << "}";

    return ss.str();
}

// Statistics methods
void Statistics::update() {
    auto now = std::chrono::system_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::seconds>(now - start_time).count();

    if (duration > 0) {
        packets_per_second = static_cast<double>(total_packets) / duration;
        mbits_per_second = (static_cast<double>(total_bytes) * 8) / (duration * 1000000);
    }

    last_update = now;
}

void Statistics::print() const {
    std::cout << to_string();
}

std::string Statistics::to_string() const {
    std::stringstream ss;

    ss << "\n========================================\n";
    ss << "  S-IDS Statistics\n";
    ss << "========================================\n";
    ss << "Total Packets:    " << total_packets << "\n";
    ss << "Total Bytes:      " << total_bytes << " ("
       << (total_bytes / 1024.0 / 1024.0) << " MB)\n";
    ss << "\nBy Protocol:\n";
    ss << "  TCP:            " << tcp_packets << "\n";
    ss << "  UDP:            " << udp_packets << "\n";
    ss << "  ICMP:           " << icmp_packets << "\n";
    ss << "  Other:          " << other_packets << "\n";
    ss << "\nPerformance:\n";
    ss << "  Packets/sec:    " << std::fixed << std::setprecision(2)
       << packets_per_second << "\n";
    ss << "  Throughput:     " << std::fixed << std::setprecision(2)
       << mbits_per_second << " Mbps\n";
    ss << "\nAlerts:\n";
    ss << "  Total:          " << alerts_generated << "\n";
    ss << "  Low:            " << alerts_by_severity[0] << "\n";
    ss << "  Medium:         " << alerts_by_severity[1] << "\n";
    ss << "  High:           " << alerts_by_severity[2] << "\n";
    ss << "  Critical:       " << alerts_by_severity[3] << "\n";
    ss << "========================================\n\n";

    return ss.str();
}

} // namespace hybrid_ids
