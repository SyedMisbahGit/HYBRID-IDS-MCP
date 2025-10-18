// zmq_publisher.h
// ZeroMQ publisher for sending flow features to AI engine

#ifndef NIDS_IPC_ZMQ_PUBLISHER_H
#define NIDS_IPC_ZMQ_PUBLISHER_H

#include <string>
#include <memory>
#include "../features/feature_extractor.h"

namespace nids {
namespace ipc {

/**
 * ZMQ Publisher for sending feature vectors to AI engine
 * Uses PUB-SUB pattern for high-throughput, low-latency communication
 */
class ZMQPublisher {
public:
    /**
     * Constructor
     * @param endpoint ZeroMQ endpoint (e.g., "tcp://*:5555")
     * @param high_water_mark Maximum queued messages (default 10000)
     */
    ZMQPublisher(const std::string& endpoint, int high_water_mark = 10000);

    /**
     * Destructor - cleans up ZMQ context and socket
     */
    ~ZMQPublisher();

    /**
     * Initialize ZeroMQ connection
     * @return true if successful, false otherwise
     */
    bool init();

    /**
     * Publish a feature vector to subscribers
     * @param features The feature vector to publish
     * @param topic Optional topic for pub-sub filtering (default: "features")
     * @return true if sent successfully, false otherwise
     */
    bool publish(const features::FeatureVector& features, const std::string& topic = "features");

    /**
     * Publish raw JSON message
     * @param json_msg JSON string to publish
     * @param topic Optional topic
     * @return true if sent successfully
     */
    bool publish_json(const std::string& json_msg, const std::string& topic = "features");

    /**
     * Get statistics
     */
    uint64_t get_sent_count() const { return sent_count_; }
    uint64_t get_error_count() const { return error_count_; }

    /**
     * Check if publisher is connected
     */
    bool is_connected() const { return connected_; }

    /**
     * Close connection
     */
    void close();

private:
    std::string endpoint_;
    int high_water_mark_;
    bool connected_;

    // ZMQ context and socket (using void* to avoid exposing ZMQ headers)
    void* context_;
    void* socket_;

    // Statistics
    uint64_t sent_count_;
    uint64_t error_count_;

    // Disable copy/assignment
    ZMQPublisher(const ZMQPublisher&) = delete;
    ZMQPublisher& operator=(const ZMQPublisher&) = delete;
};

} // namespace ipc
} // namespace nids

#endif // NIDS_IPC_ZMQ_PUBLISHER_H
