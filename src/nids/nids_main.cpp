// nids_main.cpp
// Complete Network Intrusion Detection System
// Integrates: Packet Capture, Parsing, Protocol Decoding, Connection Tracking,
//             Feature Extraction, Signature Detection, and AI Communication

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <memory>
#include <csignal>
#include <ctime>
#include <iomanip>
#include <unistd.h>
#include <pcap.h>

#include "common/types.h"
#include "parser/packet_parser.h"
#include "parser/protocol_decoder.h"
#include "rules/rule_engine.h"
#include "features/connection_tracker.h"
#include "features/feature_extractor.h"
#include "ipc/zmq_publisher.h"

using namespace nids;

// ============================================
// Global State
// ============================================

volatile sig_atomic_t stop_capture = 0;
Statistics global_stats;
std::ofstream alert_log;
std::ofstream feature_log;

// Configuration
struct NIDSConfig {
    std::string interface;
    std::string pcap_file;
    bool live_capture = false;
    bool extract_features = true;
    bool track_connections = true;
    bool decode_protocols = true;
    bool enable_signatures = true;
    bool export_features = false;
    std::string feature_export_file;
    std::string zmq_endpoint = "tcp://*:5555";
    bool use_zmq = false;
    int stats_interval = 5; // seconds
};

NIDSConfig config;

// Component instances
std::unique_ptr<PacketParser> parser;
std::unique_ptr<parser::ProtocolDecoder> decoder;
std::unique_ptr<RuleEngine> rule_engine;
std::unique_ptr<features::ConnectionTracker> conn_tracker;
std::unique_ptr<features::FeatureExtractor> feature_extractor;
std::unique_ptr<ipc::ZMQPublisher> zmq_pub;

// ============================================
// Signal Handler
// ============================================

void signal_handler(int signum) {
    std::cout << "\n[SIGNAL] Received signal " << signum << ", stopping NIDS..." << std::endl;
    stop_capture = 1;
}

// ============================================
// Utility Functions
// ============================================

std::string get_timestamp() {
    auto t = std::time(nullptr);
    auto tm = *std::localtime(&t);
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

void print_alert(const Alert& alert) {
    // Color codes
    const char* color = "\033[0m";
    switch (alert.severity) {
        case Severity::CRITICAL: color = "\033[1;31m"; break; // Bold Red
        case Severity::HIGH:     color = "\033[0;31m"; break; // Red
        case Severity::MEDIUM:   color = "\033[0;33m"; break; // Yellow
        case Severity::LOW:      color = "\033[0;32m"; break; // Green
    }

    std::cout << color << "[" << get_timestamp() << "] "
              << "[" << severity_to_string(alert.severity) << "] "
              << alert.message << " (Rule ID: " << alert.rule_id << ")"
              << "\033[0m" << std::endl;

    std::cout << "  " << alert.src_ip << ":" << alert.src_port << " -> "
              << alert.dst_ip << ":" << alert.dst_port << " ["
              << protocol_to_string(alert.protocol) << "]" << std::endl;

    if (!alert.details.empty()) {
        std::cout << "  " << alert.details << std::endl;
    }

    std::cout << std::endl;
}

void log_alert_json(const Alert& alert) {
    if (alert_log.is_open()) {
        alert_log << alert.to_json() << std::endl;
    }
}

void export_features_csv(const features::FeatureVector& features) {
    if (feature_log.is_open()) {
        feature_log << feature_extractor->to_csv(features) << std::endl;
    }
}

// ============================================
// Packet Processing Callback
// ============================================

void packet_handler(u_char* user_data, const struct pcap_pkthdr* pkthdr, const u_char* packet) {
    (void)user_data; // Unused

    // Update statistics
    global_stats.total_packets++;
    global_stats.total_bytes += pkthdr->len;

    // Parse packet
    ParsedPacket parsed = parser->parse(packet, pkthdr->len, pkthdr->ts);

    if (!parsed.is_valid) {
        return;
    }

    // Update protocol stats
    switch (parsed.protocol) {
        case Protocol::TCP:  global_stats.tcp_packets++; break;
        case Protocol::UDP:  global_stats.udp_packets++; break;
        case Protocol::ICMP: global_stats.icmp_packets++; break;
        default: global_stats.other_packets++; break;
    }

    // Protocol decoding (if enabled)
    if (config.decode_protocols && decoder) {
        if (parsed.protocol == Protocol::TCP) {
            // Check for HTTP
            if (parsed.dst_port == 80 || parsed.src_port == 80) {
                parser::HTTPData http;
                if (decoder->decode_http(parsed.payload, parsed.payload_len, http)) {
                    std::cout << "[HTTP] " << http.method << " " << http.uri << std::endl;
                }
            }
        } else if (parsed.protocol == Protocol::UDP) {
            // Check for DNS
            if (parsed.dst_port == 53 || parsed.src_port == 53) {
                parser::DNSData dns;
                if (decoder->decode_dns(parsed.payload, parsed.payload_len, dns)) {
                    std::cout << "[DNS] Query: " << dns.query_name
                              << " Type: " << dns.query_type << std::endl;
                }
            }
        }
    }

    // Connection tracking (if enabled)
    features::FlowStats* flow = nullptr;
    if (config.track_connections && conn_tracker) {
        conn_tracker->update(parsed);
        flow = conn_tracker->get_flow(parsed);
    }

    // Feature extraction (if enabled and flow exists)
    if (config.extract_features && flow && feature_extractor) {
        // Extract features from flow
        features::FeatureVector features = feature_extractor->extract(*flow, parsed);

        // Export to CSV if enabled
        if (config.export_features) {
            export_features_csv(features);
        }

        // Send to AI engine via ZMQ
        if (config.use_zmq && zmq_pub && zmq_pub->is_connected()) {
            zmq_pub->publish(features);
        }
    }

    // Signature detection (if enabled)
    if (config.enable_signatures && rule_engine) {
        std::vector<Alert> alerts = rule_engine->evaluate(parsed);

        for (const auto& alert : alerts) {
            global_stats.alert_count++;

            // Update severity counts
            switch (alert.severity) {
                case Severity::LOW:      global_stats.low_alerts++; break;
                case Severity::MEDIUM:   global_stats.medium_alerts++; break;
                case Severity::HIGH:     global_stats.high_alerts++; break;
                case Severity::CRITICAL: global_stats.critical_alerts++; break;
            }

            // Print and log alert
            print_alert(alert);
            log_alert_json(alert);
        }
    }
}

// ============================================
// Statistics Display
// ============================================

void print_statistics() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "  NIDS Real-time Statistics" << std::endl;
    std::cout << "========================================" << std::endl;
    global_stats.display();
    std::cout << "========================================" << std::endl;
}

// ============================================
// Initialization
// ============================================

bool initialize_components() {
    std::cout << "[INFO] Initializing NIDS components..." << std::endl;

    // Initialize parser
    parser = std::make_unique<PacketParser>();
    std::cout << "[OK] Packet parser initialized" << std::endl;

    // Initialize protocol decoder
    if (config.decode_protocols) {
        decoder = std::make_unique<parser::ProtocolDecoder>();
        std::cout << "[OK] Protocol decoder initialized" << std::endl;
    }

    // Initialize rule engine
    if (config.enable_signatures) {
        rule_engine = std::make_unique<RuleEngine>();
        std::cout << "[OK] Rule engine initialized with " << rule_engine->get_rule_count() << " rules" << std::endl;
    }

    // Initialize connection tracker
    if (config.track_connections) {
        conn_tracker = std::make_unique<features::ConnectionTracker>(120); // 2 min timeout
        std::cout << "[OK] Connection tracker initialized" << std::endl;
    }

    // Initialize feature extractor
    if (config.extract_features) {
        feature_extractor = std::make_unique<features::FeatureExtractor>();
        std::cout << "[OK] Feature extractor initialized" << std::endl;

        // Open feature export file if needed
        if (config.export_features && !config.feature_export_file.empty()) {
            feature_log.open(config.feature_export_file);
            if (feature_log.is_open()) {
                // Write CSV header
                feature_log << feature_extractor->get_csv_header() << std::endl;
                std::cout << "[OK] Feature export file: " << config.feature_export_file << std::endl;
            } else {
                std::cerr << "[ERROR] Failed to open feature export file" << std::endl;
                return false;
            }
        }
    }

    // Initialize ZMQ publisher
    if (config.use_zmq) {
        zmq_pub = std::make_unique<ipc::ZMQPublisher>(config.zmq_endpoint);
        if (zmq_pub->init()) {
            std::cout << "[OK] ZMQ publisher initialized at " << config.zmq_endpoint << std::endl;
        } else {
            std::cerr << "[ERROR] Failed to initialize ZMQ publisher" << std::endl;
            return false;
        }
    }

    // Open alert log
    alert_log.open("nids_alerts.log");
    if (!alert_log.is_open()) {
        std::cerr << "[ERROR] Failed to open alert log file" << std::endl;
        return false;
    }
    std::cout << "[OK] Alert log: nids_alerts.log" << std::endl;

    return true;
}

// ============================================
// Cleanup
// ============================================

void cleanup() {
    std::cout << "\n[INFO] Cleaning up..." << std::endl;

    // Cleanup connection tracker
    if (conn_tracker) {
        conn_tracker->cleanup_expired_flows();
        std::cout << "[INFO] Connection tracker cleaned up" << std::endl;
    }

    // Close ZMQ
    if (zmq_pub) {
        zmq_pub->close();
    }

    // Close logs
    if (alert_log.is_open()) {
        alert_log.close();
        std::cout << "[INFO] Alert log closed" << std::endl;
    }

    if (feature_log.is_open()) {
        feature_log.close();
        std::cout << "[INFO] Feature log closed" << std::endl;
    }

    // Print final statistics
    print_statistics();
}

// ============================================
// Main Function
// ============================================

void print_usage(const char* prog_name) {
    std::cout << "Usage: " << prog_name << " [options]" << std::endl;
    std::cout << "\nOptions:" << std::endl;
    std::cout << "  -i <interface>     Network interface for live capture" << std::endl;
    std::cout << "  -r <file>          Read packets from PCAP file" << std::endl;
    std::cout << "  --extract-features Extract ML features from flows" << std::endl;
    std::cout << "  --export-csv <file> Export features to CSV file" << std::endl;
    std::cout << "  --no-signatures    Disable signature-based detection" << std::endl;
    std::cout << "  --no-connections   Disable connection tracking" << std::endl;
    std::cout << "  --no-protocols     Disable protocol decoding" << std::endl;
    std::cout << "  --zmq <endpoint>   Enable ZMQ publishing (e.g., tcp://*:5555)" << std::endl;
    std::cout << "  -h, --help         Show this help message" << std::endl;
    std::cout << "\nExamples:" << std::endl;
    std::cout << "  " << prog_name << " -r traffic.pcap" << std::endl;
    std::cout << "  " << prog_name << " -i eth0 --extract-features --export-csv features.csv" << std::endl;
    std::cout << "  " << prog_name << " -r capture.pcap --zmq tcp://*:5555" << std::endl;
}

int main(int argc, char* argv[]) {
    // Print banner
    std::cout << "========================================" << std::endl;
    std::cout << "  Hybrid IDS - Complete NIDS" << std::endl;
    std::cout << "  Version 1.0.0" << std::endl;
    std::cout << "========================================\n" << std::endl;

    // Parse command-line arguments
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "-h" || arg == "--help") {
            print_usage(argv[0]);
            return 0;
        } else if (arg == "-i" && i + 1 < argc) {
            config.interface = argv[++i];
            config.live_capture = true;
        } else if (arg == "-r" && i + 1 < argc) {
            config.pcap_file = argv[++i];
            config.live_capture = false;
        } else if (arg == "--extract-features") {
            config.extract_features = true;
        } else if (arg == "--export-csv" && i + 1 < argc) {
            config.export_features = true;
            config.feature_export_file = argv[++i];
        } else if (arg == "--no-signatures") {
            config.enable_signatures = false;
        } else if (arg == "--no-connections") {
            config.track_connections = false;
        } else if (arg == "--no-protocols") {
            config.decode_protocols = false;
        } else if (arg == "--zmq" && i + 1 < argc) {
            config.use_zmq = true;
            config.zmq_endpoint = argv[++i];
        } else {
            std::cerr << "Unknown option: " << arg << std::endl;
            print_usage(argv[0]);
            return 1;
        }
    }

    // Validate configuration
    if (!config.live_capture && config.pcap_file.empty()) {
        std::cerr << "Error: Must specify either -i <interface> or -r <file>" << std::endl;
        print_usage(argv[0]);
        return 1;
    }

    // Setup signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // Initialize components
    if (!initialize_components()) {
        std::cerr << "[ERROR] Failed to initialize components" << std::endl;
        return 1;
    }

    // Start packet capture
    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t* handle = nullptr;

    if (config.live_capture) {
        std::cout << "\n[INFO] Starting live capture on interface: " << config.interface << std::endl;
        handle = pcap_open_live(config.interface.c_str(), 65535, 1, 100, errbuf);
    } else {
        std::cout << "\n[INFO] Processing PCAP file: " << config.pcap_file << std::endl;
        handle = pcap_open_offline(config.pcap_file.c_str(), errbuf);
    }

    if (handle == nullptr) {
        std::cerr << "[ERROR] Failed to open capture: " << errbuf << std::endl;
        cleanup();
        return 1;
    }

    std::cout << "[INFO] Capture started successfully" << std::endl;
    std::cout << "\nPress Ctrl+C to stop...\n" << std::endl;

    // Start packet processing
    global_stats.start_time = std::time(nullptr);

    // Process packets
    time_t last_stats = time(nullptr);
    while (!stop_capture) {
        // Process a batch of packets
        int ret = pcap_dispatch(handle, 100, packet_handler, nullptr);

        if (ret < 0) {
            std::cerr << "[ERROR] pcap_dispatch failed: " << pcap_geterr(handle) << std::endl;
            break;
        }

        if (ret == 0 && !config.live_capture) {
            // End of PCAP file
            break;
        }

        // Print periodic statistics
        time_t now = time(nullptr);
        if (now - last_stats >= config.stats_interval) {
            print_statistics();
            last_stats = now;
        }

        // Cleanup expired flows periodically
        if (conn_tracker && now % 30 == 0) {
            conn_tracker->cleanup_expired_flows();
        }
    }

    // Close pcap handle
    pcap_close(handle);

    // Cleanup and print final stats
    cleanup();

    std::cout << "\n[INFO] NIDS stopped successfully" << std::endl;

    return 0;
}
