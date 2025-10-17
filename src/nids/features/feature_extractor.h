#ifndef HYBRID_IDS_FEATURE_EXTRACTOR_H
#define HYBRID_IDS_FEATURE_EXTRACTOR_H

#include "../common/types.h"
#include "connection_tracker.h"
#include <vector>
#include <string>

namespace hybrid_ids {

/**
 * @brief Feature vector for ML/AI engine
 * Based on CIC-IDS2017 and NSL-KDD feature sets
 */
struct FeatureVector {
    // Basic flow information
    std::string src_ip;
    std::string dst_ip;
    uint16_t src_port;
    uint16_t dst_port;
    uint8_t protocol;

    // Duration and timing (1)
    double duration;

    // Forward/backward packet counts (2-3)
    double total_fwd_packets;
    double total_bwd_packets;

    // Forward/backward byte counts (4-5)
    double total_length_fwd_packets;
    double total_length_bwd_packets;

    // Packet length statistics (6-11)
    double fwd_packet_length_max;
    double fwd_packet_length_min;
    double fwd_packet_length_mean;
    double fwd_packet_length_std;
    double bwd_packet_length_max;
    double bwd_packet_length_min;

    double bwd_packet_length_mean;
    double bwd_packet_length_std;

    // Flow bytes and packets per second (12-13)
    double flow_bytes_per_second;
    double flow_packets_per_second;

    // Flow IAT (Inter-Arrival Time) statistics (14-21)
    double flow_iat_mean;
    double flow_iat_std;
    double flow_iat_max;
    double flow_iat_min;
    double fwd_iat_total;
    double fwd_iat_mean;
    double fwd_iat_std;
    double fwd_iat_max;

    double fwd_iat_min;
    double bwd_iat_total;
    double bwd_iat_mean;
    double bwd_iat_std;
    double bwd_iat_max;
    double bwd_iat_min;

    // TCP flags (22-27)
    double fwd_psh_flags;
    double bwd_psh_flags;
    double fwd_urg_flags;
    double bwd_urg_flags;
    double fwd_header_length;
    double bwd_header_length;

    // Packet rates (28-29)
    double fwd_packets_per_second;
    double bwd_packets_per_second;

    // Packet length statistics (30-33)
    double min_packet_length;
    double max_packet_length;
    double packet_length_mean;
    double packet_length_std;

    double packet_length_variance;

    // Flag counts (34-39)
    double fin_flag_count;
    double syn_flag_count;
    double rst_flag_count;
    double psh_flag_count;
    double ack_flag_count;
    double urg_flag_count;

    double cwe_flag_count;
    double ece_flag_count;

    // Down/Up ratio (40)
    double down_up_ratio;

    // Average packet size (41)
    double average_packet_size;

    // Segment size average (42-43)
    double avg_fwd_segment_size;
    double avg_bwd_segment_size;

    // Additional features
    double fwd_header_length_total;
    double fwd_avg_bytes_bulk;
    double fwd_avg_packets_bulk;
    double fwd_avg_bulk_rate;

    double bwd_avg_bytes_bulk;
    double bwd_avg_packets_bulk;
    double bwd_avg_bulk_rate;

    // Subflow statistics
    double subflow_fwd_packets;
    double subflow_fwd_bytes;
    double subflow_bwd_packets;
    double subflow_bwd_bytes;

    // Initial window sizes
    double init_win_bytes_forward;
    double init_win_bytes_backward;

    // Active/Idle times
    double act_data_pkt_fwd;
    double min_seg_size_forward;
    double active_mean;
    double active_std;

    double active_max;
    double active_min;
    double idle_mean;
    double idle_std;
    double idle_max;
    double idle_min;

    // Methods
    std::vector<double> to_vector() const;
    std::string to_csv() const;
    std::string to_json() const;
};

/**
 * @brief Extract ML features from network flows
 */
class FeatureExtractor {
public:
    FeatureExtractor();
    ~FeatureExtractor() = default;

    /**
     * @brief Extract features from a flow
     */
    FeatureVector extract(const FlowStats& flow, const ParsedPacket& latest_packet);

    /**
     * @brief Extract features from multiple flows
     */
    std::vector<FeatureVector> extract_batch(const std::vector<FlowStats>& flows);

    /**
     * @brief Get feature names (for CSV header)
     */
    static std::vector<std::string> get_feature_names();

    /**
     * @brief Get number of features
     */
    static constexpr size_t get_feature_count() { return 78; }

private:
    // Helper functions
    double safe_divide(double numerator, double denominator);
    double calculate_variance(double std_dev);
};

} // namespace hybrid_ids

#endif // HYBRID_IDS_FEATURE_EXTRACTOR_H
