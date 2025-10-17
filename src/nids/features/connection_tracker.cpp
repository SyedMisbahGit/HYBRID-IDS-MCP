#include "connection_tracker.h"
#include <cmath>
#include <numeric>
#include <algorithm>

namespace hybrid_ids {

// TCP flag constants
constexpr uint8_t TCP_FIN = 0x01;
constexpr uint8_t TCP_SYN = 0x02;
constexpr uint8_t TCP_RST = 0x04;
constexpr uint8_t TCP_PSH = 0x08;
constexpr uint8_t TCP_ACK = 0x10;
constexpr uint8_t TCP_URG = 0x20;

ConnectionTracker::ConnectionTracker(uint32_t timeout_seconds, uint32_t max_connections)
    : timeout_seconds_(timeout_seconds)
    , max_connections_(max_connections)
    , total_connections_(0)
    , expired_connections_(0) {
}

ConnectionKey ConnectionTracker::create_key(const ParsedPacket& packet) {
    ConnectionKey key;
    key.src_ip = packet.ip_header.src_ip;
    key.dst_ip = packet.ip_header.dst_ip;
    key.src_port = packet.get_src_port();
    key.dst_port = packet.get_dst_port();
    key.protocol = packet.ip_header.protocol;

    return key;
}

void ConnectionTracker::update(const ParsedPacket& packet) {
    ConnectionKey key = create_key(packet);

    // Find or create connection
    auto it = connections_.find(key);

    if (it == connections_.end()) {
        // New connection
        if (connections_.size() >= max_connections_) {
            // Remove oldest connection
            cleanup_expired();
        }

        FlowStats flow = {};
        flow.start_time = packet.timestamp;
        flow.last_seen = packet.timestamp;
        flow.state = ConnectionState::UNKNOWN;

        // Initialize counters
        flow.fwd_packets = 0;
        flow.fwd_bytes = 0;
        flow.bwd_packets = 0;
        flow.bwd_bytes = 0;
        flow.syn_count = 0;
        flow.ack_count = 0;
        flow.fin_count = 0;
        flow.rst_count = 0;
        flow.psh_count = 0;
        flow.urg_count = 0;

        connections_[key] = flow;
        total_connections_++;
        it = connections_.find(key);
    }

    FlowStats& flow = it->second;

    // Update timing
    auto duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        packet.timestamp - flow.last_seen).count();
    double iat = duration_ms / 1000.0;  // Convert to seconds

    // Determine direction (simplified: always forward for now)
    bool is_forward = true;

    if (is_forward) {
        flow.fwd_packets++;
        flow.fwd_bytes += packet.raw_length;

        if (flow.fwd_packets > 1) {
            flow.fwd_iat.push_back(iat);
        }
        flow.fwd_pkt_lengths.push_back(packet.raw_length);
    } else {
        flow.bwd_packets++;
        flow.bwd_bytes += packet.raw_length;

        if (flow.bwd_packets > 1) {
            flow.bwd_iat.push_back(iat);
        }
        flow.bwd_pkt_lengths.push_back(packet.raw_length);
    }

    // Update TCP flags
    if (packet.has_tcp) {
        uint8_t flags = packet.tcp_header.flags;

        if (flags & TCP_SYN) flow.syn_count++;
        if (flags & TCP_ACK) flow.ack_count++;
        if (flags & TCP_FIN) flow.fin_count++;
        if (flags & TCP_RST) flow.rst_count++;
        if (flags & TCP_PSH) flow.psh_count++;
        if (flags & TCP_URG) flow.urg_count++;

        update_tcp_state(flow, flags);
    }

    flow.last_seen = packet.timestamp;

    // Update duration
    flow.duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        flow.last_seen - flow.start_time).count() / 1000.0;
}

void ConnectionTracker::update_tcp_state(FlowStats& flow, uint8_t flags) {
    switch (flow.state) {
        case ConnectionState::UNKNOWN:
            if (flags & TCP_SYN && !(flags & TCP_ACK)) {
                flow.state = ConnectionState::SYN_SENT;
            }
            break;

        case ConnectionState::SYN_SENT:
            if (flags & TCP_SYN && flags & TCP_ACK) {
                flow.state = ConnectionState::SYN_RECEIVED;
            }
            break;

        case ConnectionState::SYN_RECEIVED:
            if (flags & TCP_ACK) {
                flow.state = ConnectionState::ESTABLISHED;
            }
            break;

        case ConnectionState::ESTABLISHED:
            if (flags & TCP_FIN) {
                flow.state = ConnectionState::FIN_WAIT;
            } else if (flags & TCP_RST) {
                flow.state = ConnectionState::CLOSED;
            }
            break;

        case ConnectionState::FIN_WAIT:
            if (flags & TCP_FIN || flags & TCP_RST) {
                flow.state = ConnectionState::CLOSED;
            }
            break;

        default:
            break;
    }
}

FlowStats* ConnectionTracker::get_flow(const ParsedPacket& packet) {
    ConnectionKey key = create_key(packet);
    auto it = connections_.find(key);

    if (it != connections_.end()) {
        // Update computed features before returning
        it->second.update_computed_features();
        return &it->second;
    }

    return nullptr;
}

void ConnectionTracker::cleanup_expired() {
    auto now = std::chrono::system_clock::now();

    for (auto it = connections_.begin(); it != connections_.end(); ) {
        if (is_expired(it->second)) {
            it = connections_.erase(it);
            expired_connections_++;
        } else {
            ++it;
        }
    }
}

bool ConnectionTracker::is_expired(const FlowStats& flow) {
    auto now = std::chrono::system_clock::now();
    auto age = std::chrono::duration_cast<std::chrono::seconds>(
        now - flow.last_seen).count();

    return age > timeout_seconds_ || flow.state == ConnectionState::CLOSED;
}

std::vector<FlowStats> ConnectionTracker::get_all_flows() {
    std::vector<FlowStats> flows;
    flows.reserve(connections_.size());

    for (auto& pair : connections_) {
        pair.second.update_computed_features();
        flows.push_back(pair.second);
    }

    return flows;
}

void ConnectionTracker::clear() {
    connections_.clear();
}

// FlowStats methods

void FlowStats::update_computed_features() {
    // Calculate rates
    if (duration > 0) {
        fwd_packet_rate = fwd_packets / duration;
        bwd_packet_rate = bwd_packets / duration;
    } else {
        fwd_packet_rate = 0;
        bwd_packet_rate = 0;
    }

    // Calculate IAT statistics
    if (!fwd_iat.empty()) {
        fwd_iat_mean = calculate_mean(fwd_iat);
        fwd_iat_std = calculate_std(fwd_iat, fwd_iat_mean);
    } else {
        fwd_iat_mean = 0;
        fwd_iat_std = 0;
    }

    if (!bwd_iat.empty()) {
        bwd_iat_mean = calculate_mean(bwd_iat);
        bwd_iat_std = calculate_std(bwd_iat, bwd_iat_mean);
    } else {
        bwd_iat_mean = 0;
        bwd_iat_std = 0;
    }

    // Calculate packet length statistics
    if (!fwd_pkt_lengths.empty()) {
        fwd_pkt_len_mean = calculate_mean_uint(fwd_pkt_lengths);
        fwd_pkt_len_std = calculate_std_uint(fwd_pkt_lengths, fwd_pkt_len_mean);
    } else {
        fwd_pkt_len_mean = 0;
        fwd_pkt_len_std = 0;
    }

    if (!bwd_pkt_lengths.empty()) {
        bwd_pkt_len_mean = calculate_mean_uint(bwd_pkt_lengths);
        bwd_pkt_len_std = calculate_std_uint(bwd_pkt_lengths, bwd_pkt_len_mean);
    } else {
        bwd_pkt_len_mean = 0;
        bwd_pkt_len_std = 0;
    }
}

double FlowStats::calculate_mean(const std::vector<double>& values) {
    if (values.empty()) return 0.0;
    return std::accumulate(values.begin(), values.end(), 0.0) / values.size();
}

double FlowStats::calculate_std(const std::vector<double>& values, double mean) {
    if (values.size() < 2) return 0.0;

    double sum_sq = 0.0;
    for (double val : values) {
        double diff = val - mean;
        sum_sq += diff * diff;
    }

    return std::sqrt(sum_sq / (values.size() - 1));
}

double FlowStats::calculate_mean_uint(const std::vector<uint32_t>& values) {
    if (values.empty()) return 0.0;

    uint64_t sum = std::accumulate(values.begin(), values.end(), 0ULL);
    return static_cast<double>(sum) / values.size();
}

double FlowStats::calculate_std_uint(const std::vector<uint32_t>& values, double mean) {
    if (values.size() < 2) return 0.0;

    double sum_sq = 0.0;
    for (uint32_t val : values) {
        double diff = val - mean;
        sum_sq += diff * diff;
    }

    return std::sqrt(sum_sq / (values.size() - 1));
}

} // namespace hybrid_ids
