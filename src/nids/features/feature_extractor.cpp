// feature_extractor.cpp
// Implementation of network flow feature extraction for ML/AI analysis

#include "feature_extractor.h"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <sstream>
#include <iomanip>

namespace nids {
namespace features {

// ============================================
// Helper Functions
// ============================================

// Calculate mean of a vector
static double calculate_mean(const std::vector<double>& values) {
    if (values.empty()) return 0.0;
    return std::accumulate(values.begin(), values.end(), 0.0) / values.size();
}

// Calculate standard deviation
static double calculate_std(const std::vector<double>& values) {
    if (values.size() < 2) return 0.0;
    double mean = calculate_mean(values);
    double sq_sum = 0.0;
    for (double val : values) {
        sq_sum += (val - mean) * (val - mean);
    }
    return std::sqrt(sq_sum / values.size());
}

// Calculate variance
static double calculate_variance(const std::vector<double>& values) {
    double std = calculate_std(values);
    return std * std;
}

// Get min value
static double get_min(const std::vector<double>& values) {
    if (values.empty()) return 0.0;
    return *std::min_element(values.begin(), values.end());
}

// Get max value
static double get_max(const std::vector<double>& values) {
    if (values.empty()) return 0.0;
    return *std::max_element(values.begin(), values.end());
}

// ============================================
// FeatureExtractor Implementation
// ============================================

FeatureExtractor::FeatureExtractor() {
    // Initialize any required state
}

FeatureVector FeatureExtractor::extract(const FlowStats& flow, const ParsedPacket& packet) {
    FeatureVector features;

    // Calculate timing features
    features.duration = flow.duration;

    // Forward IAT statistics
    features.fwd_iat_total = std::accumulate(flow.fwd_iat.begin(), flow.fwd_iat.end(), 0.0);
    features.fwd_iat_mean = calculate_mean(flow.fwd_iat);
    features.fwd_iat_std = calculate_std(flow.fwd_iat);
    features.fwd_iat_max = get_max(flow.fwd_iat);
    features.fwd_iat_min = get_min(flow.fwd_iat);

    // Backward IAT statistics
    features.bwd_iat_total = std::accumulate(flow.bwd_iat.begin(), flow.bwd_iat.end(), 0.0);
    features.bwd_iat_mean = calculate_mean(flow.bwd_iat);
    features.bwd_iat_std = calculate_std(flow.bwd_iat);
    features.bwd_iat_max = get_max(flow.bwd_iat);
    features.bwd_iat_min = get_min(flow.bwd_iat);

    // Flow IAT statistics
    features.flow_iat_mean = calculate_mean(flow.flow_iat);
    features.flow_iat_std = calculate_std(flow.flow_iat);
    features.flow_iat_max = get_max(flow.flow_iat);
    features.flow_iat_min = get_min(flow.flow_iat);

    // Packet counts
    features.total_fwd_packets = flow.fwd_packets;
    features.total_bwd_packets = flow.bwd_packets;

    // Byte counts
    features.total_fwd_bytes = flow.fwd_bytes;
    features.total_bwd_bytes = flow.bwd_bytes;

    // Packet length statistics
    features.fwd_pkt_len_max = get_max(flow.fwd_packet_lengths);
    features.fwd_pkt_len_min = get_min(flow.fwd_packet_lengths);
    features.fwd_pkt_len_mean = calculate_mean(flow.fwd_packet_lengths);
    features.fwd_pkt_len_std = calculate_std(flow.fwd_packet_lengths);

    features.bwd_pkt_len_max = get_max(flow.bwd_packet_lengths);
    features.bwd_pkt_len_min = get_min(flow.bwd_packet_lengths);
    features.bwd_pkt_len_mean = calculate_mean(flow.bwd_packet_lengths);
    features.bwd_pkt_len_std = calculate_std(flow.bwd_packet_lengths);

    // Flow bytes/packets per second
    if (flow.duration > 0) {
        features.flow_bytes_per_sec = (flow.fwd_bytes + flow.bwd_bytes) / flow.duration;
        features.flow_packets_per_sec = (flow.fwd_packets + flow.bwd_packets) / flow.duration;
        features.fwd_packets_per_sec = flow.fwd_packets / flow.duration;
        features.bwd_packets_per_sec = flow.bwd_packets / flow.duration;
    } else {
        features.flow_bytes_per_sec = 0.0;
        features.flow_packets_per_sec = 0.0;
        features.fwd_packets_per_sec = 0.0;
        features.bwd_packets_per_sec = 0.0;
    }

    // TCP flag counts
    features.fin_flag_count = flow.fin_count;
    features.syn_flag_count = flow.syn_count;
    features.rst_flag_count = flow.rst_count;
    features.psh_flag_count = flow.psh_count;
    features.ack_flag_count = flow.ack_count;
    features.urg_flag_count = flow.urg_count;
    features.cwe_flag_count = flow.cwe_count;
    features.ece_flag_count = flow.ece_count;

    // Down/up ratio
    if (flow.fwd_bytes > 0) {
        features.down_up_ratio = static_cast<double>(flow.bwd_bytes) / flow.fwd_bytes;
    } else {
        features.down_up_ratio = 0.0;
    }

    // Average packet size
    uint32_t total_packets = flow.fwd_packets + flow.bwd_packets;
    uint64_t total_bytes = flow.fwd_bytes + flow.bwd_bytes;
    if (total_packets > 0) {
        features.avg_packet_size = static_cast<double>(total_bytes) / total_packets;
    } else {
        features.avg_packet_size = 0.0;
    }

    // Forward/backward segment sizes
    if (flow.fwd_packets > 0) {
        features.avg_fwd_segment_size = static_cast<double>(flow.fwd_bytes) / flow.fwd_packets;
    } else {
        features.avg_fwd_segment_size = 0.0;
    }

    if (flow.bwd_packets > 0) {
        features.avg_bwd_segment_size = static_cast<double>(flow.bwd_bytes) / flow.bwd_packets;
    } else {
        features.avg_bwd_segment_size = 0.0;
    }

    // Header lengths
    features.fwd_header_len = flow.fwd_header_bytes;
    features.bwd_header_len = flow.bwd_header_bytes;

    // Forward PSH/URG flags
    features.fwd_psh_flags = flow.fwd_psh_count;
    features.bwd_psh_flags = flow.bwd_psh_count;
    features.fwd_urg_flags = flow.fwd_urg_count;
    features.bwd_urg_flags = flow.bwd_urg_count;

    // Packet length variance
    std::vector<double> all_lengths;
    all_lengths.insert(all_lengths.end(), flow.fwd_packet_lengths.begin(), flow.fwd_packet_lengths.end());
    all_lengths.insert(all_lengths.end(), flow.bwd_packet_lengths.begin(), flow.bwd_packet_lengths.end());
    features.pkt_len_variance = calculate_variance(all_lengths);
    features.pkt_len_mean = calculate_mean(all_lengths);
    features.pkt_len_std = calculate_std(all_lengths);
    features.pkt_len_max = get_max(all_lengths);
    features.pkt_len_min = get_min(all_lengths);

    // Initial window bytes
    features.init_fwd_win_bytes = flow.init_fwd_win_bytes;
    features.init_bwd_win_bytes = flow.init_bwd_win_bytes;

    // Minimum segment size forward
    features.min_seg_size_fwd = get_min(flow.fwd_packet_lengths);

    // Active/Idle statistics
    features.active_mean = calculate_mean(flow.active_times);
    features.active_std = calculate_std(flow.active_times);
    features.active_max = get_max(flow.active_times);
    features.active_min = get_min(flow.active_times);

    features.idle_mean = calculate_mean(flow.idle_times);
    features.idle_std = calculate_std(flow.idle_times);
    features.idle_max = get_max(flow.idle_times);
    features.idle_min = get_min(flow.idle_times);

    // Subflow features (simplified - using full flow as one subflow)
    features.subflow_fwd_packets = flow.fwd_packets;
    features.subflow_fwd_bytes = flow.fwd_bytes;
    features.subflow_bwd_packets = flow.bwd_packets;
    features.subflow_bwd_bytes = flow.bwd_bytes;

    // Bulk transfer features (simplified)
    // Bulk is defined as consecutive packets > threshold
    features.fwd_bulk_rate_avg = 0.0;
    features.bwd_bulk_rate_avg = 0.0;
    features.fwd_bulk_size_avg = 0.0;
    features.bwd_bulk_size_avg = 0.0;
    features.fwd_bulk_packets_avg = 0.0;
    features.bwd_bulk_packets_avg = 0.0;

    // Calculate bulk features (simple heuristic)
    if (flow.fwd_packets >= 4 && flow.duration > 0) {
        features.fwd_bulk_rate_avg = flow.fwd_bytes / flow.duration;
        features.fwd_bulk_size_avg = features.avg_fwd_segment_size;
        features.fwd_bulk_packets_avg = flow.fwd_packets / 4.0; // Approximate
    }

    if (flow.bwd_packets >= 4 && flow.duration > 0) {
        features.bwd_bulk_rate_avg = flow.bwd_bytes / flow.duration;
        features.bwd_bulk_size_avg = features.avg_bwd_segment_size;
        features.bwd_bulk_packets_avg = flow.bwd_packets / 4.0; // Approximate
    }

    // Act data packets forward (packets with payload)
    features.act_data_pkt_fwd = flow.fwd_packets; // Simplified: assume all have data

    return features;
}

std::vector<double> FeatureExtractor::to_vector(const FeatureVector& features) {
    std::vector<double> vec;
    vec.reserve(78);

    // Add features in order (matching CIC-IDS2017 / NSL-KDD format)
    vec.push_back(features.duration);
    vec.push_back(features.total_fwd_packets);
    vec.push_back(features.total_bwd_packets);
    vec.push_back(features.total_fwd_bytes);
    vec.push_back(features.total_bwd_bytes);

    vec.push_back(features.fwd_pkt_len_max);
    vec.push_back(features.fwd_pkt_len_min);
    vec.push_back(features.fwd_pkt_len_mean);
    vec.push_back(features.fwd_pkt_len_std);

    vec.push_back(features.bwd_pkt_len_max);
    vec.push_back(features.bwd_pkt_len_min);
    vec.push_back(features.bwd_pkt_len_mean);
    vec.push_back(features.bwd_pkt_len_std);

    vec.push_back(features.flow_bytes_per_sec);
    vec.push_back(features.flow_packets_per_sec);
    vec.push_back(features.flow_iat_mean);
    vec.push_back(features.flow_iat_std);
    vec.push_back(features.flow_iat_max);
    vec.push_back(features.flow_iat_min);

    vec.push_back(features.fwd_iat_total);
    vec.push_back(features.fwd_iat_mean);
    vec.push_back(features.fwd_iat_std);
    vec.push_back(features.fwd_iat_max);
    vec.push_back(features.fwd_iat_min);

    vec.push_back(features.bwd_iat_total);
    vec.push_back(features.bwd_iat_mean);
    vec.push_back(features.bwd_iat_std);
    vec.push_back(features.bwd_iat_max);
    vec.push_back(features.bwd_iat_min);

    vec.push_back(features.fwd_psh_flags);
    vec.push_back(features.bwd_psh_flags);
    vec.push_back(features.fwd_urg_flags);
    vec.push_back(features.bwd_urg_flags);

    vec.push_back(features.fwd_header_len);
    vec.push_back(features.bwd_header_len);
    vec.push_back(features.fwd_packets_per_sec);
    vec.push_back(features.bwd_packets_per_sec);

    vec.push_back(features.pkt_len_min);
    vec.push_back(features.pkt_len_max);
    vec.push_back(features.pkt_len_mean);
    vec.push_back(features.pkt_len_std);
    vec.push_back(features.pkt_len_variance);

    vec.push_back(features.fin_flag_count);
    vec.push_back(features.syn_flag_count);
    vec.push_back(features.rst_flag_count);
    vec.push_back(features.psh_flag_count);
    vec.push_back(features.ack_flag_count);
    vec.push_back(features.urg_flag_count);
    vec.push_back(features.cwe_flag_count);
    vec.push_back(features.ece_flag_count);

    vec.push_back(features.down_up_ratio);
    vec.push_back(features.avg_packet_size);
    vec.push_back(features.avg_fwd_segment_size);
    vec.push_back(features.avg_bwd_segment_size);

    vec.push_back(features.fwd_bulk_rate_avg);
    vec.push_back(features.fwd_bulk_size_avg);
    vec.push_back(features.fwd_bulk_packets_avg);
    vec.push_back(features.bwd_bulk_rate_avg);
    vec.push_back(features.bwd_bulk_size_avg);
    vec.push_back(features.bwd_bulk_packets_avg);

    vec.push_back(features.subflow_fwd_packets);
    vec.push_back(features.subflow_fwd_bytes);
    vec.push_back(features.subflow_bwd_packets);
    vec.push_back(features.subflow_bwd_bytes);

    vec.push_back(features.init_fwd_win_bytes);
    vec.push_back(features.init_bwd_win_bytes);
    vec.push_back(features.act_data_pkt_fwd);
    vec.push_back(features.min_seg_size_fwd);

    vec.push_back(features.active_mean);
    vec.push_back(features.active_std);
    vec.push_back(features.active_max);
    vec.push_back(features.active_min);

    vec.push_back(features.idle_mean);
    vec.push_back(features.idle_std);
    vec.push_back(features.idle_max);
    vec.push_back(features.idle_min);

    return vec;
}

std::string FeatureExtractor::to_csv(const FeatureVector& features) {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(6);

    std::vector<double> vec = to_vector(features);
    for (size_t i = 0; i < vec.size(); ++i) {
        oss << vec[i];
        if (i < vec.size() - 1) {
            oss << ",";
        }
    }

    return oss.str();
}

std::string FeatureExtractor::to_json(const FeatureVector& features) {
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(6);

    oss << "{\n";
    oss << "  \"duration\": " << features.duration << ",\n";
    oss << "  \"total_fwd_packets\": " << features.total_fwd_packets << ",\n";
    oss << "  \"total_bwd_packets\": " << features.total_bwd_packets << ",\n";
    oss << "  \"total_fwd_bytes\": " << features.total_fwd_bytes << ",\n";
    oss << "  \"total_bwd_bytes\": " << features.total_bwd_bytes << ",\n";

    oss << "  \"fwd_pkt_len_max\": " << features.fwd_pkt_len_max << ",\n";
    oss << "  \"fwd_pkt_len_min\": " << features.fwd_pkt_len_min << ",\n";
    oss << "  \"fwd_pkt_len_mean\": " << features.fwd_pkt_len_mean << ",\n";
    oss << "  \"fwd_pkt_len_std\": " << features.fwd_pkt_len_std << ",\n";

    oss << "  \"bwd_pkt_len_max\": " << features.bwd_pkt_len_max << ",\n";
    oss << "  \"bwd_pkt_len_min\": " << features.bwd_pkt_len_min << ",\n";
    oss << "  \"bwd_pkt_len_mean\": " << features.bwd_pkt_len_mean << ",\n";
    oss << "  \"bwd_pkt_len_std\": " << features.bwd_pkt_len_std << ",\n";

    oss << "  \"flow_bytes_per_sec\": " << features.flow_bytes_per_sec << ",\n";
    oss << "  \"flow_packets_per_sec\": " << features.flow_packets_per_sec << ",\n";

    oss << "  \"fin_flag_count\": " << features.fin_flag_count << ",\n";
    oss << "  \"syn_flag_count\": " << features.syn_flag_count << ",\n";
    oss << "  \"rst_flag_count\": " << features.rst_flag_count << ",\n";
    oss << "  \"psh_flag_count\": " << features.psh_flag_count << ",\n";
    oss << "  \"ack_flag_count\": " << features.ack_flag_count << ",\n";
    oss << "  \"urg_flag_count\": " << features.urg_flag_count << ",\n";

    oss << "  \"down_up_ratio\": " << features.down_up_ratio << ",\n";
    oss << "  \"avg_packet_size\": " << features.avg_packet_size << ",\n";
    oss << "  \"avg_fwd_segment_size\": " << features.avg_fwd_segment_size << ",\n";
    oss << "  \"avg_bwd_segment_size\": " << features.avg_bwd_segment_size << ",\n";

    oss << "  \"init_fwd_win_bytes\": " << features.init_fwd_win_bytes << ",\n";
    oss << "  \"init_bwd_win_bytes\": " << features.init_bwd_win_bytes << ",\n";

    oss << "  \"active_mean\": " << features.active_mean << ",\n";
    oss << "  \"idle_mean\": " << features.idle_mean << "\n";

    oss << "}";

    return oss.str();
}

std::string FeatureExtractor::get_csv_header() {
    return "duration,total_fwd_packets,total_bwd_packets,total_fwd_bytes,total_bwd_bytes,"
           "fwd_pkt_len_max,fwd_pkt_len_min,fwd_pkt_len_mean,fwd_pkt_len_std,"
           "bwd_pkt_len_max,bwd_pkt_len_min,bwd_pkt_len_mean,bwd_pkt_len_std,"
           "flow_bytes_per_sec,flow_packets_per_sec,flow_iat_mean,flow_iat_std,flow_iat_max,flow_iat_min,"
           "fwd_iat_total,fwd_iat_mean,fwd_iat_std,fwd_iat_max,fwd_iat_min,"
           "bwd_iat_total,bwd_iat_mean,bwd_iat_std,bwd_iat_max,bwd_iat_min,"
           "fwd_psh_flags,bwd_psh_flags,fwd_urg_flags,bwd_urg_flags,"
           "fwd_header_len,bwd_header_len,fwd_packets_per_sec,bwd_packets_per_sec,"
           "pkt_len_min,pkt_len_max,pkt_len_mean,pkt_len_std,pkt_len_variance,"
           "fin_flag_count,syn_flag_count,rst_flag_count,psh_flag_count,ack_flag_count,urg_flag_count,cwe_flag_count,ece_flag_count,"
           "down_up_ratio,avg_packet_size,avg_fwd_segment_size,avg_bwd_segment_size,"
           "fwd_bulk_rate_avg,fwd_bulk_size_avg,fwd_bulk_packets_avg,bwd_bulk_rate_avg,bwd_bulk_size_avg,bwd_bulk_packets_avg,"
           "subflow_fwd_packets,subflow_fwd_bytes,subflow_bwd_packets,subflow_bwd_bytes,"
           "init_fwd_win_bytes,init_bwd_win_bytes,act_data_pkt_fwd,min_seg_size_fwd,"
           "active_mean,active_std,active_max,active_min,"
           "idle_mean,idle_std,idle_max,idle_min";
}

} // namespace features
} // namespace nids
