#ifndef HYBRID_IDS_CONNECTION_TRACKER_H
#define HYBRID_IDS_CONNECTION_TRACKER_H

#include "../common/types.h"
#include <unordered_map>
#include <string>
#include <vector>
#include <chrono>

namespace hybrid_ids {

/**
 * @brief Connection 5-tuple identifier
 */
struct ConnectionKey {
    uint32_t src_ip;
    uint32_t dst_ip;
    uint16_t src_port;
    uint16_t dst_port;
    uint8_t protocol;

    bool operator==(const ConnectionKey& other) const {
        return src_ip == other.src_ip &&
               dst_ip == other.dst_ip &&
               src_port == other.src_port &&
               dst_port == other.dst_port &&
               protocol == other.protocol;
    }
};

/**
 * @brief Hash function for ConnectionKey
 */
struct ConnectionKeyHash {
    size_t operator()(const ConnectionKey& key) const {
        // Simple hash combination
        size_t h1 = std::hash<uint32_t>()(key.src_ip);
        size_t h2 = std::hash<uint32_t>()(key.dst_ip);
        size_t h3 = std::hash<uint16_t>()(key.src_port);
        size_t h4 = std::hash<uint16_t>()(key.dst_port);
        size_t h5 = std::hash<uint8_t>()(key.protocol);

        return h1 ^ (h2 << 1) ^ (h3 << 2) ^ (h4 << 3) ^ (h5 << 4);
    }
};

/**
 * @brief Connection state
 */
enum class ConnectionState {
    SYN_SENT,
    SYN_RECEIVED,
    ESTABLISHED,
    FIN_WAIT,
    CLOSED,
    UNKNOWN
};

/**
 * @brief Flow statistics for a connection
 */
struct FlowStats {
    // Timing
    std::chrono::system_clock::time_point start_time;
    std::chrono::system_clock::time_point last_seen;
    double duration;  // seconds

    // Forward direction (src -> dst)
    uint64_t fwd_packets;
    uint64_t fwd_bytes;
    std::vector<double> fwd_iat;  // Inter-arrival times
    std::vector<uint32_t> fwd_pkt_lengths;

    // Backward direction (dst -> src)
    uint64_t bwd_packets;
    uint64_t bwd_bytes;
    std::vector<double> bwd_iat;
    std::vector<uint32_t> bwd_pkt_lengths;

    // TCP specific
    uint32_t syn_count;
    uint32_t ack_count;
    uint32_t fin_count;
    uint32_t rst_count;
    uint32_t psh_count;
    uint32_t urg_count;

    // Connection state
    ConnectionState state;

    // Computed features (calculated on demand)
    double fwd_packet_rate;
    double bwd_packet_rate;
    double fwd_iat_mean;
    double fwd_iat_std;
    double bwd_iat_mean;
    double bwd_iat_std;
    double fwd_pkt_len_mean;
    double fwd_pkt_len_std;
    double bwd_pkt_len_mean;
    double bwd_pkt_len_std;

    // Methods
    void update_computed_features();
    double calculate_mean(const std::vector<double>& values);
    double calculate_std(const std::vector<double>& values, double mean);
    double calculate_mean_uint(const std::vector<uint32_t>& values);
    double calculate_std_uint(const std::vector<uint32_t>& values, double mean);
};

/**
 * @brief Connection tracking for stateful analysis
 */
class ConnectionTracker {
public:
    ConnectionTracker(uint32_t timeout_seconds = 120, uint32_t max_connections = 100000);
    ~ConnectionTracker() = default;

    /**
     * @brief Update connection state with new packet
     */
    void update(const ParsedPacket& packet);

    /**
     * @brief Get flow statistics for a connection
     */
    FlowStats* get_flow(const ParsedPacket& packet);

    /**
     * @brief Remove expired connections
     */
    void cleanup_expired();

    /**
     * @brief Get number of active connections
     */
    size_t get_active_connections() const { return connections_.size(); }

    /**
     * @brief Get all active flows (for export to AI engine)
     */
    std::vector<FlowStats> get_all_flows();

    /**
     * @brief Clear all connections
     */
    void clear();

private:
    // Create connection key from packet
    ConnectionKey create_key(const ParsedPacket& packet);

    // Update TCP connection state
    void update_tcp_state(FlowStats& flow, uint8_t flags);

    // Check if connection is expired
    bool is_expired(const FlowStats& flow);

    // Connection map
    std::unordered_map<ConnectionKey, FlowStats, ConnectionKeyHash> connections_;

    // Configuration
    uint32_t timeout_seconds_;
    uint32_t max_connections_;

    // Statistics
    uint64_t total_connections_;
    uint64_t expired_connections_;
};

} // namespace hybrid_ids

#endif // HYBRID_IDS_CONNECTION_TRACKER_H
