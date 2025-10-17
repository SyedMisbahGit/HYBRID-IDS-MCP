#include "common/types.h"
#include "parser/packet_parser.h"
#include "rules/rule_engine.h"

#include <iostream>
#include <fstream>
#include <csignal>
#include <atomic>
#include <thread>
#include <chrono>
#include <iomanip>

#include <pcap.h>

namespace hybrid_ids {

// Global flag for graceful shutdown
std::atomic<bool> g_running(true);

// Signal handler
void signal_handler(int signal) {
    if (signal == SIGINT || signal == SIGTERM) {
        std::cout << "\n[INFO] Received shutdown signal. Stopping..." << std::endl;
        g_running = false;
    }
}

/**
 * @brief Main S-IDS (Signature-based Intrusion Detection System) class
 */
class SignatureIDS {
public:
    SignatureIDS() : stats_{} {
        parser_ = std::make_unique<PacketParser>();
        rule_engine_ = std::make_unique<RuleEngine>();

        stats_.start_time = std::chrono::system_clock::now();
        stats_.last_update = stats_.start_time;

        // Initialize statistics
        stats_.total_packets = 0;
        stats_.total_bytes = 0;
        stats_.tcp_packets = 0;
        stats_.udp_packets = 0;
        stats_.icmp_packets = 0;
        stats_.other_packets = 0;
        stats_.alerts_generated = 0;
        for (int i = 0; i < 4; i++) {
            stats_.alerts_by_severity[i] = 0;
        }
    }

    /**
     * @brief Initialize S-IDS with rules
     */
    bool initialize() {
        std::cout << "========================================\n";
        std::cout << "  Hybrid IDS - Signature Detection\n";
        std::cout << "========================================\n\n";

        // Load rules
        std::cout << "[INFO] Loading signature rules..." << std::endl;
        int rules_loaded = rule_engine_->load_rules("");
        std::cout << "[INFO] Loaded " << rules_loaded << " signature rules\n" << std::endl;

        // Display loaded rules
        const auto& rules = rule_engine_->get_rules();
        std::cout << "Active Rules:\n";
        std::cout << "-------------\n";
        for (const auto& rule : rules) {
            if (rule.enabled) {
                const char* sev[] = {"LOW", "MEDIUM", "HIGH", "CRITICAL"};
                std::cout << "  [" << rule.rule_id << "] "
                         << rule.name << " ("
                         << sev[static_cast<int>(rule.severity)] << ")\n";
            }
        }
        std::cout << std::endl;

        return true;
    }

    /**
     * @brief Process packets from PCAP file
     */
    bool process_pcap_file(const std::string& pcap_file) {
        char errbuf[PCAP_ERRBUF_SIZE];

        // Open PCAP file
        pcap_t* handle = pcap_open_offline(pcap_file.c_str(), errbuf);
        if (handle == nullptr) {
            std::cerr << "[ERROR] Could not open PCAP file: " << errbuf << std::endl;
            return false;
        }

        std::cout << "[INFO] Processing PCAP file: " << pcap_file << "\n" << std::endl;

        // Process packets
        struct pcap_pkthdr* header;
        const u_char* data;
        int result;

        auto last_stats_update = std::chrono::steady_clock::now();

        while ((result = pcap_next_ex(handle, &header, &data)) >= 0 && g_running) {
            if (result == 0) continue;  // Timeout

            // Create timestamp
            auto timestamp = std::chrono::system_clock::time_point(
                std::chrono::seconds(header->ts.tv_sec) +
                std::chrono::microseconds(header->ts.tv_usec)
            );

            // Parse packet
            ParsedPacket packet = parser_->parse(data, header->caplen, timestamp);

            // Update statistics
            stats_.total_packets++;
            stats_.total_bytes += header->caplen;

            if (packet.has_tcp) stats_.tcp_packets++;
            else if (packet.has_udp) stats_.udp_packets++;
            else if (packet.ip_header.protocol == 1) stats_.icmp_packets++;
            else stats_.other_packets++;

            // Evaluate against rules
            std::vector<Alert> alerts = rule_engine_->evaluate(packet);

            // Handle alerts
            for (const auto& alert : alerts) {
                handle_alert(alert);
            }

            // Print progress every second
            auto now = std::chrono::steady_clock::now();
            if (std::chrono::duration_cast<std::chrono::seconds>(now - last_stats_update).count() >= 1) {
                print_progress();
                last_stats_update = now;
            }
        }

        pcap_close(handle);

        // Final statistics
        stats_.update();
        print_final_stats();

        return true;
    }

    /**
     * @brief Capture packets from network interface
     */
    bool capture_live(const std::string& interface) {
        char errbuf[PCAP_ERRBUF_SIZE];

        // Open device
        pcap_t* handle = pcap_open_live(interface.c_str(), 65535, 1, 1000, errbuf);
        if (handle == nullptr) {
            std::cerr << "[ERROR] Could not open interface: " << errbuf << std::endl;
            std::cerr << "[HINT] Try running with sudo or as administrator" << std::endl;
            return false;
        }

        std::cout << "[INFO] Capturing on interface: " << interface << "\n" << std::endl;
        std::cout << "[INFO] Press Ctrl+C to stop\n" << std::endl;

        // Start statistics update thread
        std::thread stats_thread([this]() {
            while (g_running) {
                std::this_thread::sleep_for(std::chrono::seconds(5));
                if (g_running) {
                    stats_.update();
                    print_progress();
                }
            }
        });

        // Process packets
        struct pcap_pkthdr* header;
        const u_char* data;
        int result;

        while ((result = pcap_next_ex(handle, &header, &data)) >= 0 && g_running) {
            if (result == 0) continue;  // Timeout

            auto timestamp = std::chrono::system_clock::now();

            // Parse packet
            ParsedPacket packet = parser_->parse(data, header->caplen, timestamp);

            // Update statistics
            stats_.total_packets++;
            stats_.total_bytes += header->caplen;

            if (packet.has_tcp) stats_.tcp_packets++;
            else if (packet.has_udp) stats_.udp_packets++;
            else if (packet.ip_header.protocol == 1) stats_.icmp_packets++;
            else stats_.other_packets++;

            // Evaluate against rules
            std::vector<Alert> alerts = rule_engine_->evaluate(packet);

            // Handle alerts
            for (const auto& alert : alerts) {
                handle_alert(alert);
            }
        }

        pcap_close(handle);

        if (stats_thread.joinable()) {
            stats_thread.join();
        }

        // Final statistics
        stats_.update();
        print_final_stats();

        return true;
    }

private:
    void handle_alert(const Alert& alert) {
        stats_.alerts_generated++;
        stats_.alerts_by_severity[static_cast<int>(alert.severity)]++;

        // Print alert to console
        std::cout << "\n" << alert.to_string();

        // Log to file (optional)
        log_alert(alert);
    }

    void log_alert(const Alert& alert) {
        std::ofstream logfile("sids_alerts.log", std::ios::app);
        if (logfile.is_open()) {
            logfile << alert.to_json() << std::endl;
            logfile.close();
        }
    }

    void print_progress() {
        stats_.update();

        std::cout << "\r[STATS] Packets: " << stats_.total_packets
                 << " | TCP: " << stats_.tcp_packets
                 << " | UDP: " << stats_.udp_packets
                 << " | Alerts: " << stats_.alerts_generated
                 << " | Rate: " << std::fixed << std::setprecision(1)
                 << stats_.packets_per_second << " pkt/s"
                 << std::flush;
    }

    void print_final_stats() {
        std::cout << "\n" << stats_.to_string();

        std::cout << "\nRule Engine Statistics:\n";
        std::cout << "  Packets Evaluated: " << rule_engine_->get_packets_evaluated() << "\n";
        std::cout << "  Rule Matches:      " << rule_engine_->get_rule_matches() << "\n";
        std::cout << "  Alerts Generated:  " << rule_engine_->get_alerts_generated() << "\n";

        std::cout << "\nParser Statistics:\n";
        std::cout << "  Packets Parsed:    " << parser_->get_packets_parsed() << "\n";
        std::cout << "  Parse Errors:      " << parser_->get_parse_errors() << "\n";
    }

    std::unique_ptr<PacketParser> parser_;
    std::unique_ptr<RuleEngine> rule_engine_;
    Statistics stats_;
};

} // namespace hybrid_ids

// Main function
int main(int argc, char* argv[]) {
    using namespace hybrid_ids;

    // Register signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // Parse command line arguments
    if (argc < 2) {
        std::cout << "Usage:\n";
        std::cout << "  " << argv[0] << " -r <pcap_file>         # Read from PCAP file\n";
        std::cout << "  " << argv[0] << " -i <interface>         # Capture from interface\n";
        std::cout << "\nExamples:\n";
        std::cout << "  " << argv[0] << " -r traffic.pcap\n";
        std::cout << "  " << argv[0] << " -i eth0\n";
        return 1;
    }

    // Create S-IDS instance
    SignatureIDS sids;

    // Initialize
    if (!sids.initialize()) {
        std::cerr << "[ERROR] Failed to initialize S-IDS" << std::endl;
        return 1;
    }

    // Process based on mode
    std::string mode = argv[1];
    if (mode == "-r" && argc >= 3) {
        // Read from PCAP file
        std::string pcap_file = argv[2];
        if (!sids.process_pcap_file(pcap_file)) {
            return 1;
        }
    } else if (mode == "-i" && argc >= 3) {
        // Capture live
        std::string interface = argv[2];
        if (!sids.capture_live(interface)) {
            return 1;
        }
    } else {
        std::cerr << "[ERROR] Invalid arguments" << std::endl;
        return 1;
    }

    std::cout << "\n[INFO] S-IDS stopped. Alerts saved to sids_alerts.log\n" << std::endl;

    return 0;
}
