#include "rule_engine.h"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cstring>
#include <arpa/inet.h>

namespace hybrid_ids {

// TCP flag constants
constexpr uint8_t TCP_FIN = 0x01;
constexpr uint8_t TCP_SYN = 0x02;
constexpr uint8_t TCP_RST = 0x04;
constexpr uint8_t TCP_PSH = 0x08;
constexpr uint8_t TCP_ACK = 0x10;
constexpr uint8_t TCP_URG = 0x20;

RuleEngine::RuleEngine()
    : packets_evaluated_(0)
    , alerts_generated_(0)
    , rule_matches_(0)
    , next_alert_id_(1) {
}

int RuleEngine::load_rules(const std::string& rules_file) {
    // For now, we'll create some default rules programmatically
    // TODO: Implement YAML parsing in future version

    // Rule 1: Detect SSH brute force (multiple connections)
    SignatureRule ssh_scan;
    ssh_scan.rule_id = 1001;
    ssh_scan.name = "SSH Scan Detection";
    ssh_scan.description = "Multiple SSH connection attempts detected";
    ssh_scan.protocol = Protocol::TCP;
    ssh_scan.src_ip_filter = "any";
    ssh_scan.dst_ip_filter = "any";
    ssh_scan.dst_ports = {22};
    ssh_scan.tcp_flags_mask = TCP_SYN;
    ssh_scan.tcp_flags_value = TCP_SYN;
    ssh_scan.severity = Severity::MEDIUM;
    ssh_scan.action = "alert";
    ssh_scan.enabled = true;
    add_rule(ssh_scan);

    // Rule 2: Detect HTTP GET with suspicious patterns
    SignatureRule sql_injection;
    sql_injection.rule_id = 1002;
    sql_injection.name = "SQL Injection Attempt";
    sql_injection.description = "Possible SQL injection in HTTP request";
    sql_injection.protocol = Protocol::TCP;
    sql_injection.src_ip_filter = "any";
    sql_injection.dst_ip_filter = "any";
    sql_injection.dst_ports = {80, 443, 8080};
    sql_injection.content_patterns = {"union select", "or 1=1", "' or '1'='1"};
    sql_injection.severity = Severity::HIGH;
    sql_injection.action = "alert";
    sql_injection.enabled = true;
    add_rule(sql_injection);

    // Rule 3: Port scan detection (SYN to common ports)
    SignatureRule port_scan;
    port_scan.rule_id = 1003;
    port_scan.name = "Port Scan Detection";
    port_scan.description = "SYN packet to commonly scanned port";
    port_scan.protocol = Protocol::TCP;
    port_scan.src_ip_filter = "any";
    port_scan.dst_ip_filter = "any";
    port_scan.dst_ports = {21, 22, 23, 25, 80, 443, 3389, 8080};
    port_scan.tcp_flags_mask = TCP_SYN | TCP_ACK;
    port_scan.tcp_flags_value = TCP_SYN;  // SYN=1, ACK=0
    port_scan.severity = Severity::MEDIUM;
    port_scan.action = "alert";
    port_scan.enabled = true;
    add_rule(port_scan);

    // Rule 4: FTP authentication attempt
    SignatureRule ftp_auth;
    ftp_auth.rule_id = 1004;
    ftp_auth.name = "FTP Authentication Attempt";
    ftp_auth.description = "FTP USER or PASS command detected";
    ftp_auth.protocol = Protocol::TCP;
    ftp_auth.src_ip_filter = "any";
    ftp_auth.dst_ip_filter = "any";
    ftp_auth.dst_ports = {21};
    ftp_auth.content_patterns = {"USER ", "PASS "};
    ftp_auth.severity = Severity::LOW;
    ftp_auth.action = "alert";
    ftp_auth.enabled = true;
    add_rule(ftp_auth);

    // Rule 5: DNS query
    SignatureRule dns_query;
    dns_query.rule_id = 1005;
    dns_query.name = "DNS Query";
    dns_query.description = "DNS query packet detected";
    dns_query.protocol = Protocol::UDP;
    dns_query.src_ip_filter = "any";
    dns_query.dst_ip_filter = "any";
    dns_query.dst_ports = {53};
    dns_query.severity = Severity::LOW;
    dns_query.action = "log";  // Just log, don't alert
    dns_query.enabled = false;  // Disabled by default (too noisy)
    add_rule(dns_query);

    // Rule 6: Telnet connection
    SignatureRule telnet;
    telnet.rule_id = 1006;
    telnet.name = "Telnet Connection";
    telnet.description = "Unencrypted Telnet connection detected";
    telnet.protocol = Protocol::TCP;
    telnet.src_ip_filter = "any";
    telnet.dst_ip_filter = "any";
    telnet.dst_ports = {23};
    telnet.severity = Severity::MEDIUM;
    telnet.action = "alert";
    telnet.enabled = true;
    add_rule(telnet);

    return rules_.size();
}

void RuleEngine::add_rule(const SignatureRule& rule) {
    rules_.push_back(rule);
}

void RuleEngine::enable_rule(uint32_t rule_id, bool enabled) {
    for (auto& rule : rules_) {
        if (rule.rule_id == rule_id) {
            rule.enabled = enabled;
            break;
        }
    }
}

std::vector<Alert> RuleEngine::evaluate(const ParsedPacket& packet) {
    packets_evaluated_++;

    std::vector<Alert> alerts;

    // Check each enabled rule
    for (const auto& rule : rules_) {
        if (!rule.enabled) continue;

        bool matched = true;

        // Check protocol
        if (rule.protocol == Protocol::TCP && !packet.has_tcp) continue;
        if (rule.protocol == Protocol::UDP && !packet.has_udp) continue;

        // Check IP filters
        if (rule.src_ip_filter != "any") {
            if (!match_ip_filter(packet.get_src_ip(), rule.src_ip_filter)) {
                continue;
            }
        }

        if (rule.dst_ip_filter != "any") {
            if (!match_ip_filter(packet.get_dst_ip(), rule.dst_ip_filter)) {
                continue;
            }
        }

        // Check ports
        if (!rule.src_ports.empty()) {
            if (!match_port(packet.get_src_port(), rule.src_ports)) {
                continue;
            }
        }

        if (!rule.dst_ports.empty()) {
            if (!match_port(packet.get_dst_port(), rule.dst_ports)) {
                continue;
            }
        }

        // Check TCP flags
        if (packet.has_tcp && rule.tcp_flags_mask != 0) {
            if (!match_tcp_flags(packet.tcp_header.flags,
                               rule.tcp_flags_mask,
                               rule.tcp_flags_value)) {
                continue;
            }
        }

        // Check content patterns
        std::string matched_content;
        if (!rule.content_patterns.empty()) {
            if (packet.payload && packet.payload_length > 0) {
                if (!match_content(packet.payload, packet.payload_length,
                                 rule.content_patterns)) {
                    continue;
                } else {
                    // Find which pattern matched (for alert message)
                    for (const auto& pattern : rule.content_patterns) {
                        if (match_content(packet.payload, packet.payload_length, {pattern})) {
                            matched_content = pattern;
                            break;
                        }
                    }
                }
            } else {
                continue;  // No payload to match
            }
        }

        // If we got here, all conditions matched
        rule_matches_++;
        alerts.push_back(create_alert(rule, packet, matched_content));
    }

    alerts_generated_ += alerts.size();
    return alerts;
}

bool RuleEngine::match_ip_filter(const std::string& ip, const std::string& filter) const {
    if (filter == "any") return true;
    if (filter == ip) return true;

    // TODO: Implement CIDR matching (e.g., 192.168.1.0/24)
    return false;
}

bool RuleEngine::match_port(uint16_t port, const std::vector<uint16_t>& port_list) const {
    if (port_list.empty()) return true;
    return std::find(port_list.begin(), port_list.end(), port) != port_list.end();
}

bool RuleEngine::match_tcp_flags(uint8_t packet_flags, uint8_t mask, uint8_t value) const {
    return (packet_flags & mask) == value;
}

bool RuleEngine::match_content(const uint8_t* payload, uint32_t payload_len,
                               const std::vector<std::string>& patterns) const {
    if (patterns.empty() || !payload || payload_len == 0) {
        return false;
    }

    // Convert payload to string for easier searching
    std::string payload_str(reinterpret_cast<const char*>(payload),
                           std::min(payload_len, 1024u));  // Limit search to first 1KB

    // Convert to lowercase for case-insensitive matching
    std::transform(payload_str.begin(), payload_str.end(), payload_str.begin(), ::tolower);

    // Check if any pattern matches
    for (const auto& pattern : patterns) {
        std::string lower_pattern = pattern;
        std::transform(lower_pattern.begin(), lower_pattern.end(),
                      lower_pattern.begin(), ::tolower);

        if (payload_str.find(lower_pattern) != std::string::npos) {
            return true;
        }
    }

    return false;
}

bool RuleEngine::match_regex(const uint8_t* payload, uint32_t payload_len,
                             const std::vector<std::string>& patterns) const {
    if (patterns.empty() || !payload || payload_len == 0) {
        return false;
    }

    std::string payload_str(reinterpret_cast<const char*>(payload),
                           std::min(payload_len, 1024u));

    for (const auto& pattern : patterns) {
        try {
            // Check if regex is cached
            auto it = regex_cache_.find(pattern);
            if (it != regex_cache_.end()) {
                if (std::regex_search(payload_str, it->second)) {
                    return true;
                }
            } else {
                // Compile and cache regex
                std::regex re(pattern, std::regex::icase);
                regex_cache_[pattern] = re;
                if (std::regex_search(payload_str, re)) {
                    return true;
                }
            }
        } catch (const std::regex_error&) {
            // Invalid regex, skip
            continue;
        }
    }

    return false;
}

Alert RuleEngine::create_alert(const SignatureRule& rule, const ParsedPacket& packet,
                               const std::string& matched_content) const {
    Alert alert;

    alert.alert_id = next_alert_id_++;
    alert.timestamp = packet.timestamp;
    alert.rule_id = rule.rule_id;
    alert.rule_name = rule.name;
    alert.severity = rule.severity;

    alert.packet_id = packet.packet_id;
    alert.src_ip = packet.get_src_ip();
    alert.dst_ip = packet.get_dst_ip();
    alert.src_port = packet.get_src_port();
    alert.dst_port = packet.get_dst_port();
    alert.protocol = packet.get_protocol();

    alert.description = rule.description;
    alert.matched_content = matched_content;

    return alert;
}

} // namespace hybrid_ids
