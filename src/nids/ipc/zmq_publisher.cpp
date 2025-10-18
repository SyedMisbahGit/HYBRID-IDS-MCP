// zmq_publisher.cpp
// ZeroMQ publisher implementation

#include "zmq_publisher.h"
#include <iostream>
#include <cstring>

// Note: This is a simplified implementation without ZMQ dependency
// In production, you would link against libzmq and use proper ZMQ API
// For now, we'll provide a mock implementation that logs to console

namespace nids {
namespace ipc {

ZMQPublisher::ZMQPublisher(const std::string& endpoint, int high_water_mark)
    : endpoint_(endpoint)
    , high_water_mark_(high_water_mark)
    , connected_(false)
    , context_(nullptr)
    , socket_(nullptr)
    , sent_count_(0)
    , error_count_(0) {
}

ZMQPublisher::~ZMQPublisher() {
    close();
}

bool ZMQPublisher::init() {
    // In production, initialize ZMQ context and socket here:
    // context_ = zmq_ctx_new();
    // socket_ = zmq_socket(context_, ZMQ_PUB);
    // zmq_setsockopt(socket_, ZMQ_SNDHWM, &high_water_mark_, sizeof(high_water_mark_));
    // zmq_bind(socket_, endpoint_.c_str());

    std::cout << "[ZMQ] Initializing publisher at " << endpoint_ << std::endl;
    std::cout << "[ZMQ] High water mark: " << high_water_mark_ << std::endl;

    // Mock: simulate successful connection
    connected_ = true;

    return true;
}

bool ZMQPublisher::publish(const features::FeatureVector& features, const std::string& topic) {
    if (!connected_) {
        std::cerr << "[ZMQ] Not connected, cannot publish" << std::endl;
        error_count_++;
        return false;
    }

    // Convert features to JSON
    features::FeatureExtractor extractor;
    std::string json_msg = extractor.to_json(features);

    return publish_json(json_msg, topic);
}

bool ZMQPublisher::publish_json(const std::string& json_msg, const std::string& topic) {
    if (!connected_) {
        error_count_++;
        return false;
    }

    // In production, send via ZMQ:
    // 1. Send topic as first frame
    // zmq_send(socket_, topic.c_str(), topic.length(), ZMQ_SNDMORE);
    // 2. Send JSON as second frame
    // zmq_send(socket_, json_msg.c_str(), json_msg.length(), 0);

    // Mock: log to console (in production this would be sent over network)
    std::cout << "[ZMQ] Publishing to topic '" << topic << "'" << std::endl;
    std::cout << "[ZMQ] Message: " << json_msg.substr(0, 100) << "..." << std::endl;

    sent_count_++;
    return true;
}

void ZMQPublisher::close() {
    if (connected_) {
        std::cout << "[ZMQ] Closing publisher connection" << std::endl;
        std::cout << "[ZMQ] Stats - Sent: " << sent_count_ << ", Errors: " << error_count_ << std::endl;

        // In production, cleanup ZMQ:
        // if (socket_) zmq_close(socket_);
        // if (context_) zmq_ctx_destroy(context_);

        connected_ = false;
        socket_ = nullptr;
        context_ = nullptr;
    }
}

} // namespace ipc
} // namespace nids
