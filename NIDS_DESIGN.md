# NIDS (Network Intrusion Detection System) - Design & Architecture

**Final Year B.Tech Project**
**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Department:** CSE - Cybersecurity

---

## Table of Contents
1. [Overview](#overview)
2. [Two-Tier NIDS Architecture](#two-tier-nids-architecture)
3. [Component Design](#component-design)
4. [Implementation Details](#implementation-details)
5. [Data Flow](#data-flow)
6. [Performance Optimizations](#performance-optimizations)

---

## Overview

The NIDS component is the core of my Hybrid IDS project, implementing a **two-tier detection pipeline**:
- **Tier 1 (S-IDS)**: Fast signature-based detection
- **Tier 2 (A-IDS)**: ML-based anomaly detection

### Design Goals

1. **High Performance**: Process 50,000+ packets/second
2. **Low Latency**: <1ms for signature matching, <5ms for ML inference
3. **Modularity**: Separate components for easy maintenance
4. **Extensibility**: Easy to add new protocols and rules
5. **Accuracy**: Minimize false positives while catching threats

---

## Two-Tier NIDS Architecture

```
┌─────────────────────────────────────────────────────┐
│                  NETWORK TRAFFIC                     │
└─────────────────────┬───────────────────────────────┘
                      │
                      ↓
        ┌─────────────────────────┐
        │   Packet Capture        │
        │   (libpcap/Npcap)       │
        │   • Promiscuous mode    │
        │   • BPF filtering       │
        └────────────┬────────────┘
                     │
                     ↓
        ┌─────────────────────────┐
        │   Packet Parser         │
        │   • Ethernet frame      │
        │   • IP header           │
        │   • TCP/UDP/ICMP        │
        │   • Application layer   │
        └────────────┬────────────┘
                     │
                     ↓
        ┌─────────────────────────┐
        │  TIER 1: S-IDS          │
        │  • Rule matching        │
        │  • Pattern detection    │
        │  • Signature database   │
        └────┬────────────────┬───┘
             │                │
        MATCH (Known)    NO MATCH (Unknown)
             │                │
             ↓                ↓
     ┌──────────────┐  ┌─────────────────────┐
     │ Alert Logger │  │ Feature Extractor   │
     │ nids_alerts  │  │ • Flow tracking     │
     │    .log      │  │ • 78 features       │
     └──────────────┘  │ • Statistical calc  │
                       └──────────┬──────────┘
                                  │
                                  ↓
                       ┌─────────────────────┐
                       │ TIER 2: A-IDS       │
                       │ • ZMQ publisher     │
                       │ • Send to ML engine │
                       └─────────────────────┘
```

---

## Component Design

### 1. Packet Capture Module

**Location:** `src/nids/capture/`

**Responsibilities:**
- Initialize network interface or PCAP file
- Apply BPF (Berkeley Packet Filter) if needed
- Capture packets in real-time or offline mode
- Handle packet buffering

**Key Classes:**
```cpp
class PacketCapture {
public:
    // Initialize capture from network interface
    bool init_live_capture(const std::string& interface);

    // Initialize capture from PCAP file
    bool init_offline_capture(const std::string& pcap_file);

    // Start packet capture loop
    void start_capture(PacketCallback callback);

    // Stop capture
    void stop_capture();
};
```

**Technologies:**
- **libpcap** (Linux) / **Npcap** (Windows)
- Promiscuous mode for capturing all traffic
- BPF for efficient kernel-level filtering

---

### 2. Packet Parser Module

**Location:** `src/nids/parser/`

**Responsibilities:**
- Decode Ethernet frames
- Parse IP headers (IPv4/IPv6)
- Parse transport layer (TCP/UDP/ICMP)
- Extract application layer data (HTTP, DNS, etc.)
- Validate packet integrity

**Key Classes:**
```cpp
class PacketParser {
public:
    // Parse complete packet
    ParsedPacket parse(const u_char* data, uint32_t length);

private:
    // Layer-specific parsers
    bool parse_ethernet(const u_char* data, ParsedPacket& packet);
    bool parse_ip(const u_char* data, ParsedPacket& packet);
    bool parse_tcp(const u_char* data, ParsedPacket& packet);
    bool parse_udp(const u_char* data, ParsedPacket& packet);
    bool parse_http(const u_char* data, ParsedPacket& packet);
};

struct ParsedPacket {
    // Ethernet
    std::string src_mac;
    std::string dst_mac;

    // IP
    std::string src_ip;
    std::string dst_ip;
    uint8_t protocol;

    // Transport
    uint16_t src_port;
    uint16_t dst_port;
    uint32_t seq_num;    // TCP
    uint32_t ack_num;    // TCP
    uint8_t tcp_flags;   // TCP

    // Application
    std::string payload;
    std::map<std::string, std::string> http_headers;
};
```

---

### 3. Rule Engine (S-IDS - Tier 1)

**Location:** `src/nids/rules/`

**Responsibilities:**
- Load signature rules from files
- Match packets against signatures
- Generate alerts for matches
- Classify threats by severity

**Rule Format (Snort-like):**
```
alert tcp any any -> any 80 (msg:"SQL Injection Attempt"; content:"' OR '1'='1"; sid:1002; severity:HIGH;)
alert tcp any any -> any any (msg:"Port Scan Detected"; flags:S; threshold:count 100, seconds 60; sid:1001; severity:MEDIUM;)
```

**Key Classes:**
```cpp
struct Rule {
    uint32_t rule_id;
    std::string name;
    std::string protocol;      // tcp, udp, icmp
    std::string src_ip;        // IP or "any"
    uint16_t src_port;         // Port or 0 for any
    std::string dst_ip;
    uint16_t dst_port;
    std::vector<std::string> patterns;  // Content to match
    Severity severity;         // LOW, MEDIUM, HIGH, CRITICAL
    bool enabled;
};

class RuleEngine {
public:
    // Load rules from file or use defaults
    int load_rules(const std::string& rules_file);

    // Match packet against all rules
    std::vector<Alert> match(const ParsedPacket& packet);

    // Get rule by ID
    const Rule* get_rule(uint32_t rule_id) const;
};
```

**Built-in Rules:**
1. **Port Scan Detection** (SID: 1001)
2. **SQL Injection** (SID: 1002)
3. **XSS Attack** (SID: 1003)
4. **Directory Traversal** (SID: 1004)
5. **Suspicious User-Agent** (SID: 1005)
6. **Large Payload** (SID: 1006)

---

### 4. Feature Extractor (A-IDS - Tier 2)

**Location:** `src/nids/features/`

**Responsibilities:**
- Track network flows (bidirectional connections)
- Calculate 78 statistical features per flow
- Maintain flow state and timeouts
- Export features for ML analysis

**Flow Tracking:**
```cpp
struct Flow {
    std::string flow_id;        // src_ip:src_port-dst_ip:dst_port
    uint64_t start_time;
    uint64_t last_seen;

    // Packet counts
    uint32_t fwd_packets;
    uint32_t bwd_packets;

    // Byte counts
    uint64_t fwd_bytes;
    uint64_t bwd_bytes;

    // Timing
    std::vector<uint64_t> fwd_iat;  // Inter-arrival times
    std::vector<uint64_t> bwd_iat;

    // Flags
    uint32_t fwd_psh_flags;
    uint32_t fwd_urg_flags;
    // ... more statistics
};

class ConnectionTracker {
public:
    // Update flow with new packet
    void update_flow(const ParsedPacket& packet);

    // Get features for completed flows
    std::vector<FlowFeatures> get_completed_flows();

    // Timeout old flows
    void cleanup_old_flows(uint64_t timeout_seconds);
};
```

**78 CIC-IDS2017 Features:**
1. Flow Duration
2. Total Forward Packets
3. Total Backward Packets
4. Forward Packet Length (Total, Max, Min, Mean, Std)
5. Backward Packet Length (Total, Max, Min, Mean, Std)
6. Flow Bytes/s
7. Flow Packets/s
8. Flow IAT (Mean, Std, Max, Min)
9. Forward IAT (Total, Mean, Std, Max, Min)
10. Backward IAT (Total, Mean, Std, Max, Min)
11. PSH Flags (Forward, Backward)
12. URG Flags (Forward, Backward)
13. ... (up to 78 features)

---

### 5. IPC Module (Communication with A-IDS)

**Location:** `src/nids/ipc/`

**Responsibilities:**
- Publish extracted features to ML engine
- Use ZeroMQ for high-performance messaging
- Handle connection failures gracefully

**Key Classes:**
```cpp
class ZMQPublisher {
public:
    // Initialize ZMQ publisher
    bool init(const std::string& endpoint);

    // Send features to ML engine
    bool send_features(const FlowFeatures& features);

    // Send batch of features
    bool send_batch(const std::vector<FlowFeatures>& batch);
};
```

**Communication:**
- **Protocol**: ZeroMQ PUB-SUB pattern
- **Endpoint**: `tcp://localhost:5555`
- **Format**: JSON or MessagePack
- **Direction**: NIDS (Publisher) → AI Engine (Subscriber)

---

## Implementation Details

### Main Programs

**1. S-IDS (Tier 1 Only)**

**File:** `src/nids/sids_main.cpp`

**Purpose:** Standalone signature-based detection

**Usage:**
```bash
./sids -i eth0                    # Live capture
./sids -r capture.pcap           # Offline analysis
./sids -i eth0 -o alerts.log    # Custom output
```

**Flow:**
```
Capture → Parse → Rule Match → Alert (if match) → Log
```

---

**2. NIDS (Full Two-Tier)**

**File:** `src/nids/nids_main.cpp`

**Purpose:** Complete NIDS with both S-IDS and A-IDS

**Usage:**
```bash
./nids -i eth0 --extract-features              # Two-tier mode
./nids -r capture.pcap --export-csv features.csv
./nids -i eth0 --zmq tcp://localhost:5555
```

**Flow:**
```
Capture → Parse → Rule Match (S-IDS)
                      ↓
              No Match? → Extract Features → Send to A-IDS
```

---

### Configuration

**File:** `config/nids.yaml`

```yaml
nids:
  # Capture settings
  interface: "eth0"
  promiscuous_mode: true
  snapshot_length: 65535
  timeout_ms: 100
  buffer_size: 268435456  # 256MB

  # S-IDS settings
  rules:
    file: "config/rules.txt"
    auto_reload: false
    reload_interval: 300

  # A-IDS feature extraction
  features:
    enabled: true
    flow_timeout: 120        # seconds
    export_interval: 1       # seconds
    export_format: "json"    # json or csv

  # IPC settings
  ipc:
    enabled: true
    endpoint: "tcp://localhost:5555"
    high_water_mark: 10000

  # Logging
  logging:
    alerts_file: "nids_alerts.log"
    level: "INFO"            # DEBUG, INFO, WARN, ERROR
    max_size_mb: 100
    rotate: true
```

---

## Data Flow

### Live Capture Mode

```
Network Interface
    ↓
libpcap (kernel-level capture)
    ↓
PacketCapture class (userspace)
    ↓
PacketParser (decode layers)
    ↓
RuleEngine (S-IDS - Tier 1)
    ├─→ Match found? → Alert Logger → nids_alerts.log
    └─→ No match? → FeatureExtractor
                        ↓
                   ConnectionTracker (aggregate by flow)
                        ↓
                   Flow timeout or interval?
                        ↓
                   ZMQPublisher → AI Engine (A-IDS - Tier 2)
```

### Offline PCAP Mode

```
PCAP File
    ↓
pcap_open_offline()
    ↓
Same flow as live capture
    ↓
Process all packets
    ↓
Final statistics
```

---

## Performance Optimizations

### 1. Efficient Packet Processing

**Optimization:** Zero-copy where possible
```cpp
// Direct access to packet data without copying
const u_char* packet_data = pcap_next(handle, &header);
// Parse in-place
```

**Optimization:** Early rejection
```cpp
// Check basic criteria first before deep inspection
if (packet.protocol != IPPROTO_TCP) {
    return;  // Skip non-TCP packets for HTTP rules
}
```

### 2. Rule Matching

**Optimization:** Trie-based pattern matching
- Build prefix tree for pattern matching
- O(m) complexity where m = pattern length

**Optimization:** Bloom filters for quick rejection
- Test if content might match before full regex
- Reduces false positives in first pass

### 3. Flow Tracking

**Optimization:** Hash map with timeout cleanup
```cpp
std::unordered_map<std::string, Flow> active_flows_;
// Periodic cleanup of old flows
void cleanup() {
    auto now = current_time();
    for (auto it = active_flows_.begin(); it != active_flows_.end();) {
        if (now - it->second.last_seen > FLOW_TIMEOUT) {
            it = active_flows_.erase(it);
        } else {
            ++it;
        }
    }
}
```

### 4. Memory Management

**Optimization:** Object pooling for packets
```cpp
class PacketPool {
    std::vector<ParsedPacket*> pool_;

public:
    ParsedPacket* acquire();
    void release(ParsedPacket* packet);
};
```

**Optimization:** Ring buffer for packet queue
- Fixed-size circular buffer
- Avoids dynamic memory allocation

### 5. Multi-threading

**Thread Model:**
```
Thread 1: Packet Capture (main thread)
Thread 2: Packet Processing (parse + S-IDS)
Thread 3: Feature Extraction (A-IDS)
Thread 4: IPC / Logging
```

**Synchronization:** Lock-free queues between threads

---

## Monitoring & Statistics

### Runtime Statistics

```
Hybrid IDS - Signature Detection
=====================================

Active Rules: 6
  [1001] Port Scan Detection (MEDIUM)
  [1002] SQL Injection Attempt (HIGH)
  [1003] XSS Attack Attempt (HIGH)
  [1004] Directory Traversal (HIGH)
  [1005] Suspicious User-Agent (LOW)
  [1006] Large Payload (MEDIUM)

Statistics (Last 60 seconds):
-----------------------------
  Total Packets: 125,432
  Total Bytes: 98.5 MB
  Packets/sec: 2,090

  Protocol Distribution:
    TCP: 89,456 (71.3%)
    UDP: 32,112 (25.6%)
    ICMP: 3,864 (3.1%)

  Alerts Generated: 12
    CRITICAL: 0
    HIGH: 8
    MEDIUM: 3
    LOW: 1
```

---

## Error Handling

### Graceful Degradation

1. **Capture Errors**: Log and attempt recovery
2. **Parse Errors**: Skip malformed packets
3. **IPC Errors**: Buffer features locally
4. **Memory Pressure**: Throttle processing

### Signal Handling

```cpp
signal(SIGINT, signal_handler);   // Ctrl+C
signal(SIGTERM, signal_handler);  // Termination request

void signal_handler(int signal) {
    g_running = false;  // Graceful shutdown
    // Flush buffers
    // Close files
    // Save state
}
```

---

## Testing Considerations

1. **Unit Tests**: Test each module independently
2. **Integration Tests**: Test S-IDS + A-IDS together
3. **Performance Tests**: Measure throughput and latency
4. **Stress Tests**: High packet rates, many flows
5. **PCAP Replay**: Known attack samples

See [NIDS_TESTING.md](NIDS_TESTING.md) for comprehensive testing guide.

---

**Author:** Syed Misbah Uddin
**Institution:** Central University of Jammu
**Project:** Final Year B.Tech - Hybrid IDS
**Last Updated:** October 2025
**Document Purpose:** Technical design documentation for NIDS component
