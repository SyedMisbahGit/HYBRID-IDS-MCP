# System Architecture Specification

**Document Version:** 1.0
**Last Updated:** 2025-10-18
**Status:** Design Phase

---

## Table of Contents

1. [Overview](#overview)
2. [Component Architecture](#component-architecture)
3. [Communication Architecture](#communication-architecture)
4. [Data Architecture](#data-architecture)
5. [Deployment Architecture](#deployment-architecture)
6. [Security Architecture](#security-architecture)

---

## 1. Overview

The Hybrid IDS system follows a **multi-layer architecture** that separates concerns across three primary layers:

1. **Data Acquisition Layer** (NIDS Engine - C++)
2. **Intelligence Layer** (AI Analysis Engine - Python)
3. **Control Layer** (MCP Orchestrator - Python)

### Architecture Principles

- **Separation of Concerns:** Each component has well-defined responsibilities
- **Loose Coupling:** Components communicate via standardized interfaces
- **High Cohesion:** Related functionalities are grouped together
- **Scalability:** Horizontal scaling through distributed sensors
- **Fault Tolerance:** Graceful degradation and automatic recovery
- **Performance:** Optimized for low-latency, high-throughput processing

---

## 2. Component Architecture

### 2.1 NIDS Engine (C++ Core)

#### Architecture Pattern
**Pipeline Architecture** with concurrent stages

```
┌─────────────────────────────────────────────────────────┐
│                    NIDS ENGINE                          │
│                                                         │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐          │
│  │ Capture  │──>│  Parse   │──>│  Decode   │          │
│  │ Thread   │   │  Queue   │   │  Thread   │          │
│  └──────────┘   └──────────┘   └─────┬─────┘          │
│                                       │                 │
│                          ┌────────────┴────────────┐   │
│                          │                         │   │
│                  ┌───────▼────────┐   ┌───────────▼─┐ │
│                  │ Feature        │   │ Signature   │ │
│                  │ Extraction     │   │ Matching    │ │
│                  └───────┬────────┘   └───────┬─────┘ │
│                          │                    │        │
│                          └─────┬──────────────┘        │
│                                │                       │
│                        ┌───────▼───────┐               │
│                        │  IPC Client   │               │
│                        │  (ZeroMQ)     │               │
│                        └───────────────┘               │
└─────────────────────────────────────────────────────────┘
```

#### Component Breakdown

##### 2.1.1 Packet Capture Module
**File:** `src/nids/capture/packet_capture.cpp`

**Responsibilities:**
- Initialize network interface in promiscuous mode
- Set BPF filters for traffic selection
- Capture packets using libpcap
- Handle packet buffers efficiently (zero-copy when possible)

**Key Classes:**
```cpp
class PacketCapture {
public:
    PacketCapture(const std::string& interface,
                  const std::string& filter);
    void start();
    void stop();
    void setCallback(PacketCallback callback);

private:
    pcap_t* handle_;
    std::thread capture_thread_;
    std::atomic<bool> running_;
};
```

**Configuration:**
- Interface: Network device name (e.g., "eth0")
- Snapshot length: 65535 bytes (full packet)
- Timeout: 100ms
- Buffer size: 256MB

##### 2.1.2 Packet Parser Module
**File:** `src/nids/parser/packet_parser.cpp`

**Responsibilities:**
- Parse Ethernet frames
- Extract IP headers (IPv4/IPv6)
- Parse transport layer (TCP/UDP/ICMP)
- Identify application layer protocols

**Key Classes:**
```cpp
class PacketParser {
public:
    ParsedPacket parse(const u_char* packet, int length);

private:
    EthernetHeader parseEthernet(const u_char* data);
    IPHeader parseIP(const u_char* data);
    TCPHeader parseTCP(const u_char* data);
    UDPHeader parseUDP(const u_char* data);
};

struct ParsedPacket {
    uint64_t timestamp;
    EthernetHeader eth;
    IPHeader ip;
    TransportHeader transport;
    uint8_t* payload;
    size_t payload_length;
};
```

##### 2.1.3 Protocol Decoder Module
**File:** `src/nids/parser/protocol_decoder.cpp`

**Responsibilities:**
- Decode application-layer protocols (HTTP, DNS, TLS, etc.)
- Extract protocol-specific features
- Detect protocol anomalies

**Supported Protocols:**
- HTTP/HTTPS (method, URI, status codes)
- DNS (query types, response codes)
- TLS (handshake patterns, cipher suites)
- SMTP, FTP (command sequences)

##### 2.1.4 Feature Extraction Module
**File:** `src/nids/features/feature_extractor.cpp`

**Responsibilities:**
- Compute statistical features from packets
- Aggregate flow-level features
- Maintain connection state tables

**Feature Categories:**

**Basic Features (per packet):**
```cpp
struct BasicFeatures {
    uint32_t src_ip;
    uint32_t dst_ip;
    uint16_t src_port;
    uint16_t dst_port;
    uint8_t protocol;
    uint16_t packet_length;
    uint8_t ttl;
    uint32_t tcp_window;
    uint8_t tcp_flags;
};
```

**Flow Features (aggregated):**
```cpp
struct FlowFeatures {
    // Duration
    double duration;

    // Volume
    uint64_t total_fwd_packets;
    uint64_t total_bwd_packets;
    uint64_t total_fwd_bytes;
    uint64_t total_bwd_bytes;

    // Rate
    double fwd_packet_rate;
    double bwd_packet_rate;

    // Inter-arrival times
    double fwd_iat_mean;
    double fwd_iat_std;
    double bwd_iat_mean;
    double bwd_iat_std;

    // Flags
    uint32_t syn_count;
    uint32_t ack_count;
    uint32_t fin_count;
    uint32_t rst_count;
};
```

##### 2.1.5 Signature Rule Engine
**File:** `src/nids/rules/rule_engine.cpp`

**Responsibilities:**
- Load rules from YAML configuration
- Perform pattern matching on packets
- Generate alerts for matching signatures

**Rule Format (YAML):**
```yaml
rules:
  - id: SID-10001
    name: "SQL Injection Attempt"
    protocol: tcp
    dst_port: [80, 443, 8080]
    content:
      - pattern: "(?i)(union.*select|insert.*into|delete.*from)"
        type: regex
    severity: high
    action: alert

  - id: SID-10002
    name: "Port Scan Detection"
    protocol: tcp
    flags: [SYN]
    threshold:
      count: 20
      window: 10  # seconds
      track_by: src_ip
    severity: medium
    action: alert
```

**Rule Engine Class:**
```cpp
class RuleEngine {
public:
    void loadRules(const std::string& rules_file);
    std::vector<Alert> evaluate(const ParsedPacket& packet);

private:
    std::vector<Rule> rules_;
    std::unordered_map<std::string, ThresholdTracker> trackers_;
};
```

##### 2.1.6 IPC Communication Module
**File:** `src/nids/ipc/zmq_client.cpp`

**Responsibilities:**
- Serialize packet data to JSON
- Send data to AI engine via ZeroMQ
- Handle connection failures and retries

**Message Format:**
```json
{
  "msg_type": "packet_data",
  "timestamp": "2025-10-18T12:34:56.789Z",
  "packet_id": "uuid-v4",
  "basic_features": {
    "src_ip": "192.168.1.100",
    "dst_ip": "10.0.0.50",
    "src_port": 52341,
    "dst_port": 443,
    "protocol": "TCP"
  },
  "flow_features": {
    "duration": 5.234,
    "total_fwd_packets": 120,
    "fwd_packet_rate": 23.5
  },
  "signature_match": {
    "matched": false,
    "rule_ids": []
  }
}
```

---

### 2.2 AI Analysis Engine (Python)

#### Architecture Pattern
**Microservice Architecture** with async request handling

```
┌─────────────────────────────────────────────────────┐
│              AI ANALYSIS ENGINE                     │
│                                                     │
│  ┌──────────────┐      ┌───────────────┐          │
│  │ IPC Server   │─────>│ Message Queue │          │
│  │ (ZeroMQ SUB) │      │  (asyncio)    │          │
│  └──────────────┘      └───────┬───────┘          │
│                                 │                  │
│                        ┌────────▼────────┐         │
│                        │ Preprocessor    │         │
│                        └────────┬────────┘         │
│                                 │                  │
│                 ┌───────────────┴───────────────┐  │
│                 │                               │  │
│         ┌───────▼────────┐          ┌──────────▼─┐│
│         │ Autoencoder    │          │ Random     ││
│         │ (Anomaly Det.) │          │ Forest     ││
│         └───────┬────────┘          └──────┬─────┘│
│                 │                          │      │
│                 └──────────┬───────────────┘      │
│                            │                      │
│                   ┌────────▼──────────┐           │
│                   │ Ensemble Fusion   │           │
│                   └────────┬──────────┘           │
│                            │                      │
│                   ┌────────▼──────────┐           │
│                   │  Alert Generator  │           │
│                   └───────────────────┘           │
└─────────────────────────────────────────────────────┘
```

#### Component Breakdown

##### 2.2.1 IPC Server
**File:** `src/ai/inference/ipc_server.py`

```python
import zmq
import asyncio
from typing import Callable

class IPCServer:
    def __init__(self, endpoint: str = "tcp://*:5555"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.bind(endpoint)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.running = False

    async def start(self, callback: Callable):
        self.running = True
        while self.running:
            message = await self.socket.recv_json()
            await callback(message)

    def stop(self):
        self.running = False
        self.socket.close()
        self.context.term()
```

##### 2.2.2 Feature Preprocessor
**File:** `src/ai/preprocessing/preprocessor.py`

```python
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib

class FeaturePreprocessor:
    def __init__(self, scaler_path: str = None):
        self.scaler = joblib.load(scaler_path) if scaler_path else StandardScaler()
        self.feature_names = [
            'duration', 'total_fwd_packets', 'total_bwd_packets',
            'fwd_packet_rate', 'bwd_packet_rate', 'fwd_iat_mean',
            # ... (total 41 features)
        ]

    def transform(self, raw_features: dict) -> np.ndarray:
        """Transform raw features to model input format"""
        feature_vector = self._extract_features(raw_features)
        scaled_features = self.scaler.transform(feature_vector.reshape(1, -1))
        return scaled_features

    def _extract_features(self, raw: dict) -> np.ndarray:
        """Extract and order features from raw packet data"""
        features = []
        for name in self.feature_names:
            features.append(raw.get(name, 0.0))
        return np.array(features)
```

##### 2.2.3 Autoencoder Model
**File:** `src/ai/models/autoencoder.py`

```python
import torch
import torch.nn as nn

class Autoencoder(nn.Module):
    def __init__(self, input_dim: int = 41):
        super().__init__()

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU()
        )

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

    def reconstruction_error(self, x):
        """Calculate reconstruction error (anomaly score)"""
        with torch.no_grad():
            reconstructed = self.forward(x)
            mse = torch.mean((x - reconstructed) ** 2, dim=1)
        return mse.numpy()
```

##### 2.2.4 Random Forest Classifier
**File:** `src/ai/models/random_forest.py`

```python
from sklearn.ensemble import RandomForestClassifier
import joblib
import numpy as np

class AttackClassifier:
    def __init__(self, model_path: str):
        self.model: RandomForestClassifier = joblib.load(model_path)
        self.attack_labels = [
            'Normal', 'DoS', 'Probe', 'R2L', 'U2R', 'DDoS', 'Botnet'
        ]

    def predict(self, features: np.ndarray) -> tuple[str, float]:
        """Predict attack type and confidence"""
        probabilities = self.model.predict_proba(features)[0]
        predicted_class = np.argmax(probabilities)
        confidence = probabilities[predicted_class]

        attack_type = self.attack_labels[predicted_class]
        return attack_type, confidence

    def predict_batch(self, features: np.ndarray) -> list[tuple[str, float]]:
        """Batch prediction for multiple samples"""
        predictions = []
        probabilities = self.model.predict_proba(features)

        for probs in probabilities:
            predicted_class = np.argmax(probs)
            confidence = probs[predicted_class]
            attack_type = self.attack_labels[predicted_class]
            predictions.append((attack_type, confidence))

        return predictions
```

##### 2.2.5 Ensemble Fusion
**File:** `src/ai/models/ensemble.py`

```python
import numpy as np
from typing import Tuple

class EnsembleFusion:
    def __init__(self,
                 anomaly_threshold: float = 0.15,
                 classifier_threshold: float = 0.7):
        self.anomaly_threshold = anomaly_threshold
        self.classifier_threshold = classifier_threshold

        # Weights for ensemble (tunable)
        self.weights = {
            'autoencoder': 0.4,
            'random_forest': 0.4,
            'signature': 0.2
        }

    def fuse_predictions(self,
                        reconstruction_error: float,
                        attack_type: str,
                        classifier_confidence: float,
                        signature_matched: bool) -> Tuple[bool, float, str]:
        """
        Fuse predictions from all models

        Returns:
            is_attack (bool): Whether traffic is malicious
            risk_score (float): Overall risk score (0-100)
            attack_type (str): Predicted attack type
        """

        # Score from autoencoder (anomaly detection)
        anomaly_score = min(reconstruction_error / self.anomaly_threshold, 1.0)

        # Score from random forest
        classifier_score = classifier_confidence if attack_type != 'Normal' else 0.0

        # Score from signature matching
        signature_score = 1.0 if signature_matched else 0.0

        # Weighted fusion
        risk_score = (
            self.weights['autoencoder'] * anomaly_score +
            self.weights['random_forest'] * classifier_score +
            self.weights['signature'] * signature_score
        ) * 100

        # Decision logic
        is_attack = (
            signature_matched or
            (anomaly_score > 0.8 and classifier_score > 0.5) or
            classifier_score > self.classifier_threshold
        )

        return is_attack, risk_score, attack_type
```

##### 2.2.6 Alert Generator
**File:** `src/ai/inference/alert_generator.py`

```python
from datetime import datetime
from typing import Dict
import json

class AlertGenerator:
    def __init__(self, alert_queue):
        self.alert_queue = alert_queue
        self.alert_id_counter = 0

    def generate_alert(self,
                      packet_data: Dict,
                      risk_score: float,
                      attack_type: str,
                      confidence: float) -> Dict:
        """Generate structured alert"""

        self.alert_id_counter += 1

        alert = {
            'alert_id': f"ALERT-{self.alert_id_counter:08d}",
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'severity': self._compute_severity(risk_score),
            'risk_score': round(risk_score, 2),
            'attack_type': attack_type,
            'confidence': round(confidence, 3),

            'source': {
                'ip': packet_data['basic_features']['src_ip'],
                'port': packet_data['basic_features']['src_port']
            },

            'destination': {
                'ip': packet_data['basic_features']['dst_ip'],
                'port': packet_data['basic_features']['dst_port']
            },

            'protocol': packet_data['basic_features']['protocol'],

            'indicators': {
                'anomaly_detected': packet_data.get('anomaly_score', 0) > 0.7,
                'signature_matched': packet_data.get('signature_match', {}).get('matched', False),
                'ml_classification': attack_type
            },

            'recommended_actions': self._get_recommendations(attack_type, risk_score)
        }

        # Push to alert queue
        self.alert_queue.put(alert)

        return alert

    def _compute_severity(self, risk_score: float) -> str:
        if risk_score >= 80:
            return 'critical'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        else:
            return 'low'

    def _get_recommendations(self, attack_type: str, risk_score: float) -> list:
        recommendations = {
            'DoS': [
                'Block source IP temporarily',
                'Activate rate limiting',
                'Notify network administrator'
            ],
            'Probe': [
                'Monitor source IP for further activity',
                'Review firewall rules',
                'Check for unauthorized access attempts'
            ],
            # ... more attack types
        }

        return recommendations.get(attack_type, ['Investigate further'])
```

---

### 2.3 MCP Controller

#### Architecture Pattern
**Service-Oriented Architecture** with REST API

```
┌──────────────────────────────────────────────────┐
│            MCP CONTROLLER                        │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │        REST API (FastAPI)                 │  │
│  │  /api/v1/health  /api/v1/alerts  ...     │  │
│  └──────────────┬────────────────────────────┘  │
│                 │                                │
│  ┌──────────────▼─────────────┐                 │
│  │    Orchestrator Service    │                 │
│  │  - Start/Stop Components   │                 │
│  │  - Health Monitoring       │                 │
│  │  - Config Management       │                 │
│  └──────────┬────────┬────────┘                 │
│             │        │                           │
│   ┌─────────▼──┐  ┌─▼──────────┐                │
│   │ NIDS Mgr   │  │ AI Mgr     │                │
│   └────────────┘  └────────────┘                │
│                                                  │
│  ┌────────────────────────────────────┐         │
│  │  Data Store (SQLite/PostgreSQL)    │         │
│  │  - Alerts  - Metrics  - Config     │         │
│  └────────────────────────────────────┘         │
└──────────────────────────────────────────────────┘
```

#### Component Breakdown

##### 2.3.1 Orchestrator Service
**File:** `src/mcp/orchestrator/orchestrator.py`

```python
import subprocess
import psutil
from typing import Dict, Optional

class Orchestrator:
    def __init__(self, config: Dict):
        self.config = config
        self.processes = {}
        self.status = {}

    def start_nids(self) -> bool:
        """Start NIDS engine"""
        try:
            cmd = [self.config['nids']['binary_path'],
                   '--config', self.config['nids']['config_path']]

            proc = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

            self.processes['nids'] = proc
            self.status['nids'] = 'running'
            return True
        except Exception as e:
            self.status['nids'] = f'error: {str(e)}'
            return False

    def start_ai_engine(self) -> bool:
        """Start AI analysis engine"""
        try:
            cmd = ['python', self.config['ai']['main_script'],
                   '--config', self.config['ai']['config_path']]

            proc = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

            self.processes['ai_engine'] = proc
            self.status['ai_engine'] = 'running'
            return True
        except Exception as e:
            self.status['ai_engine'] = f'error: {str(e)}'
            return False

    def health_check(self) -> Dict:
        """Check health of all components"""
        health = {}

        for component, proc in self.processes.items():
            if proc.poll() is None:  # Process is running
                try:
                    process = psutil.Process(proc.pid)
                    health[component] = {
                        'status': 'healthy',
                        'cpu_percent': process.cpu_percent(),
                        'memory_mb': process.memory_info().rss / 1024 / 1024,
                        'uptime_seconds': time.time() - process.create_time()
                    }
                except:
                    health[component] = {'status': 'unknown'}
            else:
                health[component] = {'status': 'stopped'}

        return health

    def stop_all(self):
        """Gracefully stop all components"""
        for component, proc in self.processes.items():
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=10)
```

##### 2.3.2 REST API
**File:** `src/mcp/api/main.py`

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Hybrid IDS MCP API", version="1.0.0")

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    components: dict
    timestamp: str

class AlertQuery(BaseModel):
    severity: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100

# Endpoints
@app.get("/api/v1/health", response_model=HealthResponse)
async def get_health():
    """Get system health status"""
    health = orchestrator.health_check()
    return {
        'status': 'healthy' if all(h['status'] == 'healthy' for h in health.values()) else 'degraded',
        'components': health,
        'timestamp': datetime.utcnow().isoformat()
    }

@app.get("/api/v1/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Query alerts from database"""
    alerts = db.query_alerts(severity=severity, limit=limit)
    return {'count': len(alerts), 'alerts': alerts}

@app.post("/api/v1/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    success = db.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {'status': 'acknowledged', 'alert_id': alert_id}

@app.post("/api/v1/config/reload")
async def reload_config():
    """Reload system configuration"""
    success = orchestrator.reload_config()
    return {'status': 'reloaded' if success else 'failed'}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 3. Communication Architecture

### 3.1 IPC Protocol

**Transport:** ZeroMQ
**Pattern:** PUB/SUB (NIDS → AI), REQ/REP (Control)
**Serialization:** JSON

#### Message Types

1. **Packet Data Message**
   - From: NIDS → AI Engine
   - Frequency: Per packet (or batched)
   - Size: ~500 bytes/packet

2. **Alert Message**
   - From: AI Engine → MCP
   - Frequency: On detection
   - Size: ~1KB/alert

3. **Control Message**
   - From: MCP → Components
   - Frequency: On-demand
   - Types: START, STOP, RELOAD_CONFIG, HEALTH_CHECK

4. **Status Message**
   - From: Components → MCP
   - Frequency: Every 30 seconds
   - Size: ~200 bytes

### 3.2 API Communication

**Protocol:** HTTP/REST
**Authentication:** JWT tokens (future)
**Endpoints:** See MCP API section

---

## 4. Data Architecture

### 4.1 Database Schema

**Technology:** SQLite (development), PostgreSQL (production)

```sql
-- Alerts table
CREATE TABLE alerts (
    alert_id VARCHAR(32) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    severity VARCHAR(10) NOT NULL,
    risk_score FLOAT NOT NULL,
    attack_type VARCHAR(50),
    confidence FLOAT,
    src_ip VARCHAR(45),
    dst_ip VARCHAR(45),
    protocol VARCHAR(10),
    acknowledged BOOLEAN DEFAULT FALSE,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_src_ip ON alerts(src_ip);

-- System metrics table
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    component VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100),
    metric_value FLOAT,
    unit VARCHAR(20)
);

-- Configuration history
CREATE TABLE config_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    component VARCHAR(50),
    config_snapshot JSON,
    changed_by VARCHAR(100)
);
```

### 4.2 File Storage

```
/opt/hybrid-ids/
├── models/
│   ├── autoencoder_v1.pt
│   ├── random_forest_v1.pkl
│   └── scaler.pkl
├── rules/
│   ├── signatures.yaml
│   └── custom_rules.yaml
├── logs/
│   ├── nids.log
│   ├── ai_engine.log
│   └── mcp.log
└── data/
    ├── pcaps/          # Captured traffic
    └── training/       # Training datasets
```

---

## 5. Deployment Architecture

### 5.1 Single-Node Deployment

```
┌───────────────────────────────────────┐
│         Physical/Virtual Host         │
│  ┌────────────────────────────────┐   │
│  │  Docker Container: NIDS        │   │
│  │  - C++ binary                  │   │
│  │  - libpcap mounted             │   │
│  └────────────────────────────────┘   │
│  ┌────────────────────────────────┐   │
│  │  Docker Container: AI Engine   │   │
│  │  - Python + PyTorch            │   │
│  │  - Models volume mounted       │   │
│  └────────────────────────────────┘   │
│  ┌────────────────────────────────┐   │
│  │  Docker Container: MCP         │   │
│  │  - Python + FastAPI            │   │
│  │  - PostgreSQL                  │   │
│  └────────────────────────────────┘   │
└───────────────────────────────────────┘
```

### 5.2 Distributed Deployment

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ Sensor Node 1│       │ Sensor Node 2│       │ Sensor Node N│
│  - NIDS only │       │  - NIDS only │       │  - NIDS only │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                       │
       └──────────────┬───────┴───────────────────────┘
                      │ (ZeroMQ/gRPC)
            ┌─────────▼──────────┐
            │  Central Analysis  │
            │  - AI Engine       │
            │  - MCP Controller  │
            │  - Database        │
            └────────────────────┘
```

---

## 6. Security Architecture

### 6.1 Threat Model

**Assets:**
- Network traffic data
- ML models
- Alert database
- Configuration files

**Threats:**
- Unauthorized access to API
- Tampering with alerts
- Model poisoning attacks
- Resource exhaustion (DoS)

### 6.2 Security Controls

1. **Authentication & Authorization**
   - API key-based authentication
   - JWT tokens for session management
   - Role-based access control (RBAC)

2. **Encryption**
   - TLS 1.3 for API communication
   - Encrypted storage for sensitive configs
   - Encrypted IPC channels (optional)

3. **Integrity**
   - Signed model files
   - Checksum verification for config files
   - Audit logging for all administrative actions

4. **Availability**
   - Rate limiting on API endpoints
   - Resource quotas for containers
   - Automatic restart on failure

---

## Conclusion

This architecture provides a solid foundation for building a high-performance, scalable, and secure Hybrid IDS system. The modular design allows for independent development and testing of components while maintaining clean interfaces for integration.

**Next Steps:**
1. Review and validate architecture with stakeholders
2. Define detailed API contracts
3. Begin Phase 1 implementation (NIDS engine)
4. Set up development and testing environments

---

**Document Approval:**
- [ ] Architecture Review
- [ ] Security Review
- [ ] Performance Review
- [ ] Stakeholder Sign-off
