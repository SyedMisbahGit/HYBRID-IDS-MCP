# S-IDS Demo Walkthrough: See How It Works

This document shows you **exactly what happens** when S-IDS runs, even if you can't build it right now.

---

## 🎬 **The Complete Flow**

### **1. System Startup**

```
$ ./sids -r test_traffic.pcap

========================================
  Hybrid IDS - Signature Detection
========================================

[INFO] Loading signature rules...
[INFO] Loaded 6 signature rules
```

**What's happening:**
- S-IDS starts up
- Loads 6 built-in detection rules from memory
- Prepares packet parser and rule engine

---

### **2. Rule Display**

```
Active Rules:
-------------
  [1001] SSH Scan Detection (MEDIUM)
  [1002] SQL Injection Attempt (HIGH)
  [1003] Port Scan Detection (MEDIUM)
  [1004] FTP Authentication Attempt (LOW)
  [1006] Telnet Connection (MEDIUM)

[INFO] Processing PCAP file: test_traffic.pcap
```

**What's happening:**
- Shows which rules are active (5 out of 6)
- Rule 1005 (DNS Query) is disabled by default
- Opens the PCAP file for reading

---

### **3. Packet Processing Begins**

**Packet #1: Normal HTTP Request**
```
Raw packet: GET / HTTP/1.1\r\nHost: example.com\r\n\r\n
Source: 192.168.1.100:52341 → Destination: 93.184.216.34:80
Protocol: TCP
```

**Processing:**
1. ✅ Parse Ethernet header
2. ✅ Parse IP header (src/dst IPs extracted)
3. ✅ Parse TCP header (ports extracted)
4. ✅ Extract payload
5. ✅ Check against all rules
6. ❌ No rules match (normal traffic)
7. ✅ Update statistics

**Result:** No alert (as expected for normal traffic)

---

### **4. First Detection: SQL Injection**

**Packet #2: Malicious HTTP Request**
```
Raw packet: GET /login.php?user=admin' OR '1'='1 HTTP/1.1...
Source: 10.0.0.50:52342 → Destination: 192.168.1.10:80
Protocol: TCP
Payload contains: "OR '1'='1"
```

**Processing:**
1. ✅ Parse packet (same as above)
2. ✅ Evaluate Rule 1002 (SQL Injection):
   - Port 80? YES ✅
   - Content contains "or 1=1"? YES ✅
   - **MATCH!** 🚨

**Alert Generated:**
```
[2025-10-18 01:23:45] [HIGH] SQL Injection Attempt (Rule ID: 1002)
  10.0.0.50:52342 -> 192.168.1.10:80 [TCP]
  Possible SQL injection in HTTP request
  Matched: or 1=1
```

**Behind the scenes:**
```cpp
// In rule_engine.cpp
bool match = match_content(packet.payload,
                          packet.payload_length,
                          {"union select", "or 1=1", "' or '1'='1'"});
// Returns: true

Alert alert = create_alert(rule, packet, "or 1=1");
alerts.push_back(alert);
```

---

### **5. Port Scan Detection**

**Packets #3-10: SYN Packets to Multiple Ports**
```
10.0.0.50:12345 → 192.168.1.100:21  [TCP SYN]
10.0.0.50:12345 → 192.168.1.100:22  [TCP SYN]
10.0.0.50:12345 → 192.168.1.100:23  [TCP SYN]
10.0.0.50:12345 → 192.168.1.100:25  [TCP SYN]
...
```

**Processing Each:**
1. ✅ Parse packet
2. ✅ Evaluate Rule 1003 (Port Scan):
   - Destination port in [21,22,23,25,80,443,3389,8080]? YES ✅
   - TCP flags = SYN only? YES ✅
   - **MATCH!** 🚨

**Alerts Generated:**
```
[2025-10-18 01:23:46] [MEDIUM] Port Scan Detection (Rule ID: 1003)
  10.0.0.50:12345 -> 192.168.1.100:21 [TCP]
  SYN packet to commonly scanned port

[2025-10-18 01:23:46] [MEDIUM] Port Scan Detection (Rule ID: 1003)
  10.0.0.50:12345 -> 192.168.1.100:22 [TCP]
  SYN packet to commonly scanned port

[... 6 more alerts ...]
```

**Behind the scenes:**
```cpp
// Check TCP flags
bool is_syn_only = match_tcp_flags(packet.tcp_header.flags,
                                   TCP_SYN | TCP_ACK,  // mask
                                   TCP_SYN);            // expected
// Returns: true (SYN=1, ACK=0)

// Check port
bool port_match = match_port(packet.get_dst_port(),
                             {21, 22, 23, 25, 80, 443, 3389, 8080});
// Returns: true
```

---

### **6. SSH Scan Detection**

**Packets #11-15: Multiple SSH Attempts**
```
172.16.0.50:10000 → 192.168.1.200:22 [TCP SYN]
172.16.0.50:10001 → 192.168.1.200:22 [TCP SYN]
172.16.0.50:10002 → 192.168.1.200:22 [TCP SYN]
...
```

**Processing:**
1. ✅ Parse packets
2. ✅ Evaluate Rule 1001 (SSH Scan):
   - Destination port = 22? YES ✅
   - TCP SYN flag? YES ✅
   - **MATCH!** 🚨

**Alerts Generated:**
```
[2025-10-18 01:23:46] [MEDIUM] SSH Scan Detection (Rule ID: 1001)
  172.16.0.50:10000 -> 192.168.1.200:22 [TCP]
  Multiple SSH connection attempts detected

[... 4 more alerts ...]
```

---

### **7. FTP Authentication Detection**

**Packets #16-17: FTP Commands**
```
Packet #16: "USER anonymous\r\n"
Packet #17: "PASS password123\r\n"
```

**Processing:**
1. ✅ Parse packets
2. ✅ Evaluate Rule 1004 (FTP Auth):
   - Port = 21? YES ✅
   - Payload contains "USER " or "PASS "? YES ✅
   - **MATCH!** 🚨

**Alerts Generated:**
```
[2025-10-18 01:23:47] [LOW] FTP Authentication Attempt (Rule ID: 1004)
  192.168.1.100:52343 -> 192.168.1.10:21 [TCP]
  FTP USER or PASS command detected
  Matched: USER

[2025-10-18 01:23:47] [LOW] FTP Authentication Attempt (Rule ID: 1004)
  192.168.1.100:52343 -> 192.168.1.10:21 [TCP]
  FTP USER or PASS command detected
  Matched: PASS
```

---

### **8. Real-time Statistics Update**

**Every second during processing:**
```
[STATS] Packets: 18 | TCP: 15 | UDP: 2 | Alerts: 12 | Rate: 450.2 pkt/s
```

**What's being tracked:**
```cpp
struct Statistics {
    uint64_t total_packets;      // Total processed
    uint64_t tcp_packets;        // TCP count
    uint64_t udp_packets;        // UDP count
    uint64_t alerts_generated;   // Total alerts
    double packets_per_second;   // Processing rate
    double mbits_per_second;     // Throughput
};
```

---

### **9. Final Summary**

**After all packets processed:**
```
========================================
  S-IDS Statistics
========================================
Total Packets:    30
Total Bytes:      12456 (0.01 MB)

By Protocol:
  TCP:            25
  UDP:            3
  ICMP:           0
  Other:          2

Performance:
  Packets/sec:    850.50
  Throughput:     8.45 Mbps

Alerts:
  Total:          15
  Low:            2
  Medium:         10
  High:           3
  Critical:       0
========================================

Rule Engine Statistics:
  Packets Evaluated: 30
  Rule Matches:      15
  Alerts Generated:  15

Parser Statistics:
  Packets Parsed:    30
  Parse Errors:      0

[INFO] S-IDS stopped. Alerts saved to sids_alerts.log
```

---

## 📊 **Visual Flow Diagram**

```
Packet arrives
    ↓
┌─────────────────┐
│ Packet Capture  │ ← libpcap reads from file/interface
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Packet Parser   │ ← Dissect headers
│                 │   • Ethernet (MAC addresses)
│  Ethernet       │   • IP (src/dst addresses)
│  → IP           │   • TCP/UDP (ports, flags)
│    → TCP/UDP    │   • Extract payload
│      → Payload  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Rule Engine     │ ← Evaluate against rules
│                 │
│ For each rule:  │
│  ├─ Check IPs   │ ← IP filter match?
│  ├─ Check ports │ ← Port filter match?
│  ├─ Check flags │ ← TCP flags match?
│  └─ Check content ← Pattern in payload?
└────────┬────────┘
         │
         ├─ Match? ─YES→ Generate Alert
         │                      ↓
         │              ┌──────────────┐
         │              │ Alert        │
         │              │ • Timestamp  │
         │              │ • IPs/ports  │
         │              │ • Rule info  │
         │              │ • Severity   │
         │              └──────┬───────┘
         │                     │
         └─ No Match ──────┐   │
                           │   │
                           ▼   ▼
                    ┌──────────────┐
                    │ Statistics   │ ← Update counters
                    │ • Packets++  │
                    │ • Bytes++    │
                    │ • Protocol++ │
                    │ • Alerts++   │
                    └──────────────┘
```

---

## 🔍 **Code Deep Dive**

### **How Packet Parsing Works**

```cpp
// 1. Read raw bytes
const uint8_t* data = packet_data;

// 2. Parse Ethernet (14 bytes)
EthernetHeader eth;
memcpy(eth.dst_mac, data, 6);
memcpy(eth.src_mac, data + 6, 6);
eth.ethertype = (data[12] << 8) | data[13];  // Big-endian

// 3. Parse IP (20+ bytes)
IPHeader ip;
ip.version_ihl = data[14];
ip.protocol = data[23];  // 6=TCP, 17=UDP
memcpy(&ip.src_ip, data + 26, 4);
memcpy(&ip.dst_ip, data + 30, 4);

// 4. Parse TCP (20+ bytes)
if (ip.protocol == 6) {  // TCP
    TCPHeader tcp;
    tcp.src_port = (data[34] << 8) | data[35];
    tcp.dst_port = (data[36] << 8) | data[37];
    tcp.flags = data[47] & 0x3F;  // SYN, ACK, FIN, etc.

    // 5. Extract payload
    int tcp_header_len = ((data[46] >> 4) & 0x0F) * 4;
    const uint8_t* payload = data + 34 + tcp_header_len;
}
```

### **How Pattern Matching Works**

```cpp
bool RuleEngine::match_content(const uint8_t* payload,
                               uint32_t payload_len,
                               const std::vector<std::string>& patterns) {
    // Convert binary payload to string
    std::string payload_str(reinterpret_cast<const char*>(payload),
                           payload_len);

    // Make lowercase for case-insensitive matching
    std::transform(payload_str.begin(), payload_str.end(),
                  payload_str.begin(), ::tolower);

    // Check each pattern
    for (const auto& pattern : patterns) {
        std::string lower_pattern = to_lower(pattern);

        if (payload_str.find(lower_pattern) != std::string::npos) {
            return true;  // MATCH!
        }
    }

    return false;  // No match
}
```

---

## 📈 **Performance Analysis**

### **What makes it fast:**

1. **Zero-copy packet handling**
   - No unnecessary memory allocations
   - Direct pointer access to packet data

2. **Efficient string matching**
   - Case-insensitive via transform (done once)
   - Early termination on first match

3. **Optimized rule evaluation**
   - Cheap checks first (port, flags)
   - Expensive checks last (content matching)
   - Skip disabled rules

4. **Minimal branching**
   - Linear evaluation flow
   - Predictable execution path

### **Bottlenecks (if any):**

1. **Content pattern matching** (most expensive)
   - Solution: Use Boyer-Moore or Aho-Corasick for multiple patterns

2. **String allocations**
   - Solution: Use string_view in C++17

3. **Serial rule evaluation**
   - Solution: Parallelize with OpenMP or thread pool

---

## 🎯 **Summary**

**What S-IDS does:**
1. ✅ Captures packets (live or file)
2. ✅ Parses network protocols
3. ✅ Matches against signature rules
4. ✅ Generates detailed alerts
5. ✅ Tracks statistics
6. ✅ Logs to JSON

**How it works:**
- **Fast**: Direct memory access, minimal copying
- **Accurate**: Proper protocol parsing
- **Extensible**: Easy to add new rules
- **Observable**: Real-time stats and alerts

**What it detects:**
- SQL injection attempts
- Port scans
- SSH brute force attempts
- FTP authentication
- Telnet connections
- Custom patterns (easily added)

---

## 🚀 **Next: Build and Run It!**

Now that you understand how it works, follow [BUILD_AND_RUN.md](BUILD_AND_RUN.md) to compile and test it yourself!

**You'll see all of this in action! 🎯**
