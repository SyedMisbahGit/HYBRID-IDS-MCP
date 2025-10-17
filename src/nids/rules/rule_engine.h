#ifndef HYBRID_IDS_RULE_ENGINE_H
#define HYBRID_IDS_RULE_ENGINE_H

#include "../common/types.h"
#include <vector>
#include <memory>
#include <regex>
#include <unordered_map>

namespace hybrid_ids {

/**
 * @brief Signature-based rule matching engine
 *
 * Loads rules from YAML files and matches packets against signatures.
 * Generates alerts when rules match.
 */
class RuleEngine {
public:
    RuleEngine();
    ~RuleEngine() = default;

    /**
     * @brief Load rules from YAML file
     *
     * @param rules_file Path to rules YAML file
     * @return Number of rules loaded
     */
    int load_rules(const std::string& rules_file);

    /**
     * @brief Add a single rule programmatically
     */
    void add_rule(const SignatureRule& rule);

    /**
     * @brief Evaluate packet against all active rules
     *
     * @param packet Parsed packet to check
     * @return Vector of generated alerts (empty if no matches)
     */
    std::vector<Alert> evaluate(const ParsedPacket& packet);

    /**
     * @brief Enable or disable a rule by ID
     */
    void enable_rule(uint32_t rule_id, bool enabled);

    /**
     * @brief Get all loaded rules
     */
    const std::vector<SignatureRule>& get_rules() const { return rules_; }

    /**
     * @brief Get statistics
     */
    uint64_t get_packets_evaluated() const { return packets_evaluated_; }
    uint64_t get_alerts_generated() const { return alerts_generated_; }
    uint64_t get_rule_matches() const { return rule_matches_; }

private:
    // Rule matching methods
    bool match_ip_filter(const std::string& ip, const std::string& filter) const;
    bool match_port(uint16_t port, const std::vector<uint16_t>& port_list) const;
    bool match_tcp_flags(uint8_t packet_flags, uint8_t mask, uint8_t value) const;
    bool match_content(const uint8_t* payload, uint32_t payload_len,
                      const std::vector<std::string>& patterns) const;
    bool match_regex(const uint8_t* payload, uint32_t payload_len,
                    const std::vector<std::string>& patterns) const;

    // Alert generation
    Alert create_alert(const SignatureRule& rule, const ParsedPacket& packet,
                      const std::string& matched_content = "") const;

    // Compiled regex cache
    std::unordered_map<std::string, std::regex> regex_cache_;

    // Rules storage
    std::vector<SignatureRule> rules_;

    // Statistics
    uint64_t packets_evaluated_;
    uint64_t alerts_generated_;
    uint64_t rule_matches_;
    uint64_t next_alert_id_;
};

} // namespace hybrid_ids

#endif // HYBRID_IDS_RULE_ENGINE_H
