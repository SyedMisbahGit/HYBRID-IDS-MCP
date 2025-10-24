# Hybrid IDS - System Architecture

Complete architecture documentation for the integrated NIDS + HIDS system.

---

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Layers](#architecture-layers)
- [Component Interactions](#component-interactions)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Deployment Architecture](#deployment-architecture)
- [Scalability](#scalability)

---

## System Overview

The Hybrid IDS implements a **four-layer architecture** combining network and host-based intrusion detection with unified alerting, event correlation, and visualization.

### Design Principles

1. **Modularity**: Independent components with clear interfaces
2. **Scalability**: Horizontal scaling for increased load
3. **Performance**: Optimized for high-throughput packet processing
4. **Reliability**: Fault-tolerant with graceful degradation
5. **Extensibility**: Easy to add new detection rules and features

---

## Architecture Layers

```
┌──────────────────────────────────────────────────────────────────────┐
│                         LAYER 4: VISUALIZATION                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                      Kibana Dashboards                          │  │
│  │  • Alert Timeline  • Geographic Maps  • Attack Analysis        │  │
│  └───────────────────────────────┬──────────────────────────────────┘  │
└────────────────────────────────────┼─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────┐
│                       LAYER 3: INTEGRATION                           │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │           Unified Alert Manager (Python)                       │  │
│  │  • Multi-source ingestion  • Normalization  • Enrichment       │  │
│  └──────────────────┬─────────────────────────────────────────────┘  │
│  ┌──────────────────▼─────────────────────────────────────────────┐  │
│  │           Event Correlator (Python)                            │  │
│  │  • 10 Correlation Rules  • Multi-stage Attack Detection       │  │
│  └──────────────────┬─────────────────────────────────────────────┘  │
│  ┌──────────────────▼─────────────────────────────────────────────┐  │
│  │           Integration Controller (Python)                      │  │
│  │  • Component Orchestration  • Health Monitoring  • Stats       │  │
│  └──────────────────┬─────────────────────────────────────────────┘  │
└────────────────────────┼────────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼────────────────────┐  ┌────────▼──────────────────────────┐
│   LAYER 2: DETECTION       │  │   LAYER 2: DETECTION               │
│                            │  │                                    │
│  ┌──────────────────────┐  │  │  ┌───────────────────────────┐   │
│  │  NIDS (C++)          │  │  │  │  HIDS (Python)            │   │
│  │                      │  │  │  │                           │   │
│  │  ┌────────────────┐  │  │  │  │  ┌──────────────────┐   │   │
│  │  │ S-IDS          │  │  │  │  │  │ File Monitor     │   │   │
│  │  │ (Signature)    │  │  │  │  │  │ • SHA256 hashing │   │   │
│  │  │ • 30+ rules    │  │  │  │  │  │ • Real-time scan │   │   │
│  │  └────────────────┘  │  │  │  │  └──────────────────┘   │   │
│  │  ┌────────────────┐  │  │  │  │  ┌──────────────────┐   │   │
│  │  │ A-IDS          │  │  │  │  │  │ Process Monitor  │   │   │
│  │  │ (Anomaly ML)   │  │  │  │  │  │ • Baseline       │   │   │
│  │  │ • Random Forest│  │  │  │  │  │ • Suspicious     │   │   │
│  │  │ • Isolation F. │  │  │  │  │  └──────────────────┘   │   │
│  │  └────────────────┘  │  │  │  │  ┌──────────────────┐   │   │
│  │  ┌────────────────┐  │  │  │  │  │ Log Analyzer     │   │   │
│  │  │ Features       │  │  │  │  │  │ • 12 rules       │   │   │
│  │  │ • 78 CIC       │  │  │  │  │  │ • Brute force    │   │   │
│  │  └────────────────┘  │  │  │  │  └──────────────────┘   │   │
│  └──────┬───────────────┘  │  │  └──────┬─────────────────┘   │
│         │ ZMQ:5556         │  │         │ ZMQ:5557            │
└─────────┼──────────────────┘  └─────────┼─────────────────────┘
          │                               │
┌─────────▼───────────────────────────────▼─────────────────────────┐
│                      LAYER 1: DATA SOURCES                         │
│  ┌──────────────────────────┐  ┌────────────────────────────────┐ │
│  │  Network Traffic         │  │  Host Activity                 │ │
│  │  • Ethernet/WiFi         │  │  • File system events          │ │
│  │  • TCP/UDP/ICMP          │  │  • Process creation            │ │
│  │  • HTTP/DNS/ARP          │  │  • Log entries                 │ │
│  └──────────────────────────┘  └────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

---

## Component Interactions

### 1. Detection Layer → Integration Layer

**NIDS to Alert Manager**:
```
NIDS (C++) → ZMQ PUB (port 5556) → Alert Manager SUB
```

**HIDS to Alert Manager**:
```
HIDS (Python) → ZMQ PUB (port 5557) → Alert Manager SUB
```

**Message Format** (JSON):
```json
{
  "type": "signature|anomaly|file|process|log",
  "severity": "INFO|LOW|MEDIUM|HIGH|CRITICAL",
  "name": "Attack Name",
  "description": "Detailed description",
  "src_ip": "192.168.1.100",
  "dst_ip": "10.0.0.50",
  "timestamp": "2025-10-20T12:34:56.789Z",
  "metadata": {
    "rule_id": 1001,
    "confidence": 0.95,
    "protocol": "TCP"
  }
}
```

### 2. Integration Layer Workflow

```
┌──────────────────────────────────────────────────────────────┐
│                  Unified Alert Manager                        │
│                                                                │
│  1. Receive alert (from NIDS or HIDS)                        │
│          ↓                                                     │
│  2. Normalize to common schema                                │
│          ↓                                                     │
│  3. Enrich (GeoIP, DNS lookup)                               │
│          ↓                                                     │
│  4. Deduplicate (60-second window)                           │
│          ↓                                                     │
│  5. Add to processing queue                                   │
│          ↓                                                     │
│  ┌──────▼──────────────────────────────────┐                │
│  │  Worker Thread Pool (4 threads)         │                │
│  │  • Dequeue alert                        │                │
│  │  • Output to destinations                │                │
│  │  • Update statistics                     │                │
│  └──────┬──────────────┬──────────┬────────┘                │
│         ↓              ↓          ↓                          │
│     Console          File      Elasticsearch                 │
└──────────────────────────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│                    Event Correlator                           │
│                                                                │
│  1. Receive normalized alert                                  │
│          ↓                                                     │
│  2. Create event context (extract IPs, hostname)             │
│          ↓                                                     │
│  3. Index event (by IP, hostname, source)                    │
│          ↓                                                     │
│  4. Check correlation rules (10 rules)                       │
│          ↓                                                     │
│  5. If match found → Create correlated alert                 │
│          ↓                                                     │
│  6. Send back to Alert Manager                               │
│          ↓                                                     │
│  7. Cleanup old events (sliding window)                      │
└──────────────────────────────────────────────────────────────┘
```

### 3. Output Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    Alert Outputs                              │
│                                                                │
│  Console Output:                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ [HIGH] [nids_signature] SQL Injection Attempt        │   │
│  │   Description: Potential SQL injection detected      │   │
│  │   Time: 2025-10-20T12:34:56                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                                │
│  File Output (JSON Lines):                                    │
│  logs/alerts/unified_alerts.jsonl                            │
│                                                                │
│  Elasticsearch Output:                                        │
│  Index: hybrid-ids-alerts-2025.10.20                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ {                                                     │   │
│  │   "@timestamp": "2025-10-20T12:34:56.789Z",         │   │
│  │   "alertId": "nids_signature_1698765432000000",      │   │
│  │   "source": "nids_signature",                        │   │
│  │   "severity": "HIGH",                                │   │
│  │   "severity_num": 4,                                 │   │
│  │   ...                                                │   │
│  │ }                                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### End-to-End Alert Flow

```
1. Network packet arrives
         ↓
2. NIDS libpcap captures packet
         ↓
3. S-IDS checks signatures
         ↓ (if match)
4. Alert created with rule details
         ↓
5. ZMQ publishes alert (port 5556)
         ↓
6. Alert Manager subscribes and receives
         ↓
7. Alert normalized to unified schema
         ↓
8. Alert enriched (GeoIP, severity mapping)
         ↓
9. Alert deduplicated (check if seen recently)
         ↓
10. Alert added to processing queue
         ↓
11. Worker thread picks up alert
         ↓
12. Alert sent to Event Correlator
         ↓
13. Correlator checks for related events
         ↓ (if correlation found)
14. Correlated alert created (CRITICAL severity)
         ↓
15. Alerts output to 3 destinations:
    ├─→ Console (real-time display)
    ├─→ File (JSON log)
    └─→ Elasticsearch (indexed)
         ↓
16. Logstash processes from Elasticsearch input
         ↓
17. Logstash enriches further (GeoIP, MITRE)
         ↓
18. Logstash indexes to Elasticsearch
         ↓
19. Kibana queries Elasticsearch
         ↓
20. Dashboard displays alert with visualizations
```

### Correlation Flow Example

```
Time: 10:00:00
Event: Port Scan detected from 192.168.1.100
       ↓
Event Correlator:
- Stores event in history
- Indexes by IP: 192.168.1.100
- No correlation (first event)
       ↓
Output: Regular alert (MEDIUM severity)

─────────────────────────────────────

Time: 10:05:30 (5 minutes later)
Event: SQL Injection from 192.168.1.100
       ↓
Event Correlator:
- Receives new event
- Indexes by IP: 192.168.1.100
- Checks rules:
  ✓ Rule CR001 matches:
    - Port Scan (pattern: "port.*scan")
    - + SQL Injection (pattern: "injection")
    - Same IP: 192.168.1.100
    - Within 10-minute window: ✓
       ↓
Correlation Triggered!
       ↓
Create Correlated Alert:
- Source: correlation
- Severity: CRITICAL (elevated)
- Title: "Port Scan to Exploitation"
- Description: Includes both events
- Metadata: Related alert IDs, rule ID
       ↓
Output: Correlated alert + Original alert
```

---

## Technology Stack

### Layer-by-Layer Technology Choices

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Data Sources** | libpcap, OS APIs | Industry standard for packet capture and system monitoring |
| **NIDS Core** | C++17 | High performance, low latency for packet processing |
| **HIDS Core** | Python 3.10+ | Rapid development, rich libraries (psutil, watchdog) |
| **Integration** | Python 3.10+ | Flexibility, ML libraries, easy prototyping |
| **IPC** | ZeroMQ | High-throughput, low-latency message queue |
| **ML Framework** | scikit-learn | Mature, well-documented, production-ready |
| **Storage** | Elasticsearch | Scalable, full-text search, time-series optimized |
| **Processing** | Logstash | Pipeline-based log processing, rich filters |
| **Visualization** | Kibana | Purpose-built for Elasticsearch, rich dashboards |
| **Containerization** | Docker | Easy deployment, environment isolation |
| **Build System** | CMake | Cross-platform C++ build automation |

### Inter-Process Communication

```
┌──────────────┐                    ┌──────────────┐
│   NIDS       │                    │   HIDS       │
│   (C++)      │                    │   (Python)   │
└──────┬───────┘                    └──────┬───────┘
       │ ZMQ PUB                           │ ZMQ PUB
       │ tcp://*:5556                      │ tcp://*:5557
       │                                    │
       └────────────┬──────────────────────┘
                    │
            ┌───────▼────────┐
            │  Alert Manager │
            │  ZMQ SUB       │
            │  (Python)      │
            └───────┬────────┘
                    │
            ┌───────▼────────┐
            │  Correlator    │
            │  (Python)      │
            └───────┬────────┘
                    │
       ┌────────────┼────────────┐
       │            │            │
┌──────▼─────┐ ┌───▼────┐ ┌────▼─────────┐
│  Console   │ │  File  │ │ Elasticsearch│
└────────────┘ └────────┘ └──────────────┘
```

**Why ZeroMQ?**
- **Performance**: 1M+ messages/sec
- **Patterns**: PUB/SUB for broadcasting
- **Language-agnostic**: C++ ↔ Python
- **No broker**: Direct socket communication
- **Reliability**: Built-in message queuing

---

## Deployment Architecture

### Single-Node Deployment (Development/Testing)

```
┌────────────────────────────────────────────────────────────┐
│                     Host Machine                            │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────────────┐  │
│  │  NIDS    │  │  HIDS    │  │  Integration Layer      │  │
│  │  (C++)   │  │ (Python) │  │  (Python)               │  │
│  └──────────┘  └──────────┘  └─────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ELK Stack (Docker)                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │Elastics- │  │Logstash  │  │ Kibana   │          │  │
│  │  │ earch    │  │          │  │          │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Ports:                                                      │
│  - 5556: NIDS alerts                                        │
│  - 5557: HIDS alerts                                        │
│  - 9200: Elasticsearch                                      │
│  - 5601: Kibana                                             │
└────────────────────────────────────────────────────────────┘
```

### Multi-Node Deployment (Production)

```
┌──────────────────────────────────────────────────────────────┐
│                    Network Perimeter                          │
│                                                                │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                │
│  │ NIDS Node │  │ NIDS Node │  │ NIDS Node │                │
│  │    #1     │  │    #2     │  │    #3     │                │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘                │
│        │              │              │                        │
└────────┼──────────────┼──────────────┼────────────────────────┘
         │              │              │
         └──────────────┴──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  Load Balancer / Message    │
         │  Broker (optional)          │
         └──────────────┬──────────────┘
                        │
┌───────────────────────▼────────────────────────────────────────┐
│                   Central Processing Node                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Integration Layer (Python)                            │   │
│  │  - Unified Alert Manager                               │   │
│  │  - Event Correlator                                    │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  ELK Cluster                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │   ES     │  │   ES     │  │   ES     │  (3 nodes) │   │
│  │  │  Master  │  │  Data    │  │  Data    │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘            │   │
│  │  ┌────────────────────┐  ┌────────────────────┐      │   │
│  │  │  Logstash (2x)     │  │  Kibana            │      │   │
│  │  └────────────────────┘  └────────────────────┘      │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
         │                              │
┌────────▼────────────┐  ┌──────────────▼─────────────┐
│  Protected Hosts    │  │  Security Analysts         │
│  (HIDS deployed)    │  │  (Dashboard access)        │
│  - Server 1         │  │  - View alerts             │
│  - Server 2         │  │  - Investigate incidents   │
│  - Server 3         │  │  - Create rules            │
└─────────────────────┘  └────────────────────────────┘
```

---

## Scalability

### Horizontal Scaling

**NIDS Scaling**:
```
1 NIDS instance:
- Throughput: 100,000 packets/sec
- Coverage: Single network segment

3 NIDS instances (load balanced):
- Throughput: 300,000 packets/sec
- Coverage: Multiple network segments
```

**HIDS Scaling**:
```
Distributed deployment:
- 1 HIDS per protected host
- Central aggregation point
- Scales linearly with hosts
```

**Integration Layer Scaling**:
```
Current: Single-threaded alert manager with worker pool
Scale-out: Multiple alert manager instances behind load balancer
```

**ELK Scaling**:
```
Small deployment:
- 1 ES node, 1 Logstash, 1 Kibana
- ~1K alerts/sec

Medium deployment:
- 3 ES nodes (1 master, 2 data)
- 2 Logstash instances
- 1 Kibana
- ~10K alerts/sec

Large deployment:
- 5+ ES nodes (dedicated master/data/ingest)
- 5+ Logstash instances
- 2+ Kibana instances
- 100K+ alerts/sec
```

### Performance Characteristics

| Component | Latency | Throughput | Scalability |
|-----------|---------|------------|-------------|
| NIDS S-IDS | <1ms | 100K pkt/s | Horizontal (add nodes) |
| NIDS A-IDS | ~5ms | 10K flows/s | Horizontal (add nodes) |
| HIDS | ~30s scan | 5K files/min | Per-host (linear) |
| Alert Manager | <10ms | 1K alerts/s | Vertical (add threads) |
| Correlator | <5ms | 500 events/s | Vertical (memory-bound) |
| Elasticsearch | ~50ms | 10K docs/s | Horizontal (cluster) |

---

## Security Considerations

### Component Isolation

```
┌────────────────────────────────────────────────────┐
│  Security Zones                                     │
│                                                      │
│  ┌───────────────────────────────────────────┐     │
│  │  DMZ (NIDS sensors)                       │     │
│  │  - Read-only network access               │     │
│  │  - No management interfaces               │     │
│  │  - Outbound: ZMQ only (5556)              │     │
│  └───────────────────────────────────────────┘     │
│                                                      │
│  ┌───────────────────────────────────────────┐     │
│  │  Protected Hosts (HIDS agents)            │     │
│  │  - Local file system access               │     │
│  │  - No network access except ZMQ (5557)    │     │
│  └───────────────────────────────────────────┘     │
│                                                      │
│  ┌───────────────────────────────────────────┐     │
│  │  Management Network (Integration + ELK)   │     │
│  │  - Isolated VLAN                          │     │
│  │  - Firewall rules                         │     │
│  │  - SSL/TLS enabled                        │     │
│  └───────────────────────────────────────────┘     │
└────────────────────────────────────────────────────┘
```

### Data Protection

- **In-Transit**: TLS for Elasticsearch/Kibana, ZMQ encryption (optional)
- **At-Rest**: Elasticsearch encryption, encrypted file logs
- **Access Control**: Kibana authentication, API keys, role-based access

---

## Conclusion

The Hybrid IDS architecture provides:

✅ **Comprehensive Coverage**: Network + Host detection
✅ **Real-time Processing**: Sub-second alert generation
✅ **Advanced Correlation**: Multi-stage attack detection
✅ **Scalable Design**: Horizontal and vertical scaling options
✅ **Production Ready**: Fault-tolerant, monitored, documented

**Next**: See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for deployment instructions.
