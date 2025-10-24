# Hybrid IDS - Deployment Guide

Complete deployment guide for production and development environments.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Hybrid IDS can be deployed in multiple configurations:

1. **Development**: Single machine, all components local
2. **Production**: Multi-node, distributed deployment
3. **Docker**: Containerized deployment for easy management
4. **Cloud**: AWS/Azure/GCP deployment

---

## Prerequisites

### Hardware Requirements

| Deployment | CPU | RAM | Disk | Network |
|-----------|-----|-----|------|---------|
| Development | 2 cores | 4GB | 20GB | 100Mbps |
| Small Production | 4 cores | 8GB | 100GB | 1Gbps |
| Medium Production | 8 cores | 16GB | 500GB | 10Gbps |
| Large Production | 16+ cores | 32GB+ | 1TB+ | 10Gbps+ |

### Software Requirements

**Operating System**:
- Ubuntu 22.04 LTS (recommended)
- CentOS 8 / RHEL 8
- Windows 10/11 (development only)
- macOS 12+ (development only)

**Required Software**:
- Python 3.10+
- GCC/G++ 8+ or Clang 10+
- CMake 3.15+
- Docker 20.10+ (for ELK stack)
- libpcap / Npcap

**Optional Software**:
- Docker Compose
- Kubernetes (for large deployments)
- Terraform (for cloud deployments)

---

## Development Deployment

### Quick Setup (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/SyedMisbahGit/HYBRID-IDS-MCP.git
cd HYBRID-IDS-MCP

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build NIDS
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j4
cd ..

# 4. Start ELK stack
cd elk && docker-compose up -d && cd ..

# 5. Start system
sudo ./scripts/start_hybrid_ids.sh
```

### Manual Component Start

```bash
# Terminal 1: NIDS
cd build
sudo ./sids -i eth0

# Terminal 2: HIDS + Integration
cd src/integration
python3 hybrid_ids.py -c ../../config/hybrid_ids_config.yaml
```

---

## Production Deployment

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Load Balancer                          │
│                    (NIDS Traffic)                         │
└─────────────┬─────────────────┬──────────────┬──────────┘
              │                 │              │
     ┌────────▼────┐   ┌───────▼─────┐  ┌────▼─────────┐
     │  NIDS Node  │   │  NIDS Node  │  │  NIDS Node   │
     │      #1     │   │      #2     │  │      #3      │
     └─────────────┘   └─────────────┘  └──────────────┘
              │                 │              │
              └─────────────────┴──────────────┘
                                │
                     ┌──────────▼──────────┐
                     │  Central Processing │
                     │  (Integration Layer)│
                     └──────────┬──────────┘
                                │
                     ┌──────────▼──────────┐
                     │    ELK Cluster      │
                     │  (3 ES nodes)       │
                     └─────────────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │                                     │
     ┌────────▼────────┐                  ┌───────▼────────┐
     │  Protected Hosts│                  │  SOC Analysts  │
     │   (HIDS agents) │                  │   (Kibana)     │
     └─────────────────┘                  └────────────────┘
```

### Step 1: Prepare Infrastructure

**Network Requirements**:
```bash
# Create isolated management network
sudo ip link add name mgmt-br type bridge
sudo ip addr add 10.100.0.1/24 dev mgmt-br
sudo ip link set mgmt-br up

# Configure firewall
sudo ufw allow from 10.100.0.0/24 to any port 5556
sudo ufw allow from 10.100.0.0/24 to any port 5557
sudo ufw allow from 10.100.0.0/24 to any port 9200
sudo ufw allow from 10.100.0.0/24 to any port 5601
```

### Step 2: Deploy NIDS Sensors

**On each NIDS node**:

```bash
# 1. Install dependencies
sudo apt update
sudo apt install build-essential cmake libpcap-dev

# 2. Clone and build
git clone https://github.com/SyedMisbahGit/HYBRID-IDS-MCP.git
cd HYBRID-IDS-MCP
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -march=native"
make -j$(nproc)

# 3. Create systemd service
sudo cat > /etc/systemd/system/hybrid-ids-nids.service <<EOF
[Unit]
Description=Hybrid IDS - NIDS Sensor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hybrid-ids/build
ExecStart=/opt/hybrid-ids/build/sids -i eth0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable hybrid-ids-nids
sudo systemctl start hybrid-ids-nids
```

### Step 3: Deploy Integration Layer

**On central processing node**:

```bash
# 1. Install Python dependencies
pip3 install -r requirements.txt

# 2. Configure for production
cp config/hybrid_ids_config.yaml config/hybrid_ids_config.prod.yaml

# Edit configuration
nano config/hybrid_ids_config.prod.yaml
# Set:
# - alert_manager.outputs.elasticsearch.enabled: true
# - notifications.email.enabled: true
# - monitoring.enabled: true

# 3. Create systemd service
sudo cat > /etc/systemd/system/hybrid-ids-integration.service <<EOF
[Unit]
Description=Hybrid IDS - Integration Layer
After=network.target elasticsearch.service

[Service]
Type=simple
User=hybrid-ids
WorkingDirectory=/opt/hybrid-ids/src/integration
ExecStart=/usr/bin/python3 hybrid_ids.py -c /opt/hybrid-ids/config/hybrid_ids_config.prod.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 4. Create dedicated user
sudo useradd -r -s /bin/false hybrid-ids
sudo chown -R hybrid-ids:hybrid-ids /opt/hybrid-ids

# 5. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable hybrid-ids-integration
sudo systemctl start hybrid-ids-integration
```

### Step 4: Deploy ELK Cluster

**Elasticsearch cluster (3 nodes)**:

```yaml
# docker-compose-elasticsearch.yml
version: '3.8'
services:
  es-master:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - node.name=es-master
      - cluster.name=hybrid-ids-cluster
      - discovery.seed_hosts=es-data1,es-data2
      - cluster.initial_master_nodes=es-master
      - node.roles=master
      - "ES_JAVA_OPTS=-Xms4g -Xmx4g"
    volumes:
      - es_master_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  es-data1:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - node.name=es-data1
      - cluster.name=hybrid-ids-cluster
      - discovery.seed_hosts=es-master,es-data2
      - cluster.initial_master_nodes=es-master
      - node.roles=data,ingest
      - "ES_JAVA_OPTS=-Xms8g -Xmx8g"
    volumes:
      - es_data1_data:/usr/share/elasticsearch/data

  es-data2:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - node.name=es-data2
      - cluster.name=hybrid-ids-cluster
      - discovery.seed_hosts=es-master,es-data1
      - cluster.initial_master_nodes=es-master
      - node.roles=data,ingest
      - "ES_JAVA_OPTS=-Xms8g -Xmx8g"
    volumes:
      - es_data2_data:/usr/share/elasticsearch/data

volumes:
  es_master_data:
  es_data1_data:
  es_data2_data:
```

```bash
docker-compose -f docker-compose-elasticsearch.yml up -d
```

### Step 5: Deploy HIDS Agents

**On each protected host**:

```bash
# 1. Install Python and dependencies
sudo apt install python3 python3-pip
pip3 install psutil watchdog pyyaml pyzmq

# 2. Deploy HIDS code
scp -r user@central-server:/opt/hybrid-ids/src/hids /opt/hybrid-ids/
scp user@central-server:/opt/hybrid-ids/config/hids/hids_config.yaml /opt/hybrid-ids/config/

# 3. Configure ZMQ endpoint
nano /opt/hybrid-ids/config/hids_config.yaml
# Set alert_forwarding.endpoint to central server

# 4. Create systemd service
sudo cat > /etc/systemd/system/hybrid-ids-hids.service <<EOF
[Unit]
Description=Hybrid IDS - HIDS Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hybrid-ids/src/hids
ExecStart=/usr/bin/python3 hids_main.py -c /opt/hybrid-ids/config/hids_config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 5. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable hybrid-ids-hids
sudo systemctl start hybrid-ids-hids
```

---

## Docker Deployment

### Complete Dockerized Deployment

**1. Create Dockerfile for Integration Layer**:

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Expose ports
EXPOSE 5556 5557

# Run integration layer
CMD ["python", "src/integration/hybrid_ids.py", "-c", "config/hybrid_ids_config.yaml"]
```

**2. Create Docker Compose for Complete System**:

```yaml
# docker-compose-full.yml
version: '3.8'

services:
  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: hybrid-ids-elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    networks:
      - hybrid-ids

  # Logstash
  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: hybrid-ids-logstash
    volumes:
      - ./elk/logstash/pipeline:/usr/share/logstash/pipeline
      - ./elk/logstash/config:/usr/share/logstash/config
    ports:
      - "5044:5044"
    networks:
      - hybrid-ids
    depends_on:
      - elasticsearch

  # Kibana
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: hybrid-ids-kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    networks:
      - hybrid-ids
    depends_on:
      - elasticsearch

  # Integration Layer
  integration:
    build: .
    container_name: hybrid-ids-integration
    ports:
      - "5556:5556"
      - "5557:5557"
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    networks:
      - hybrid-ids
    depends_on:
      - elasticsearch
      - logstash

networks:
  hybrid-ids:
    driver: bridge

volumes:
  es_data:
```

**3. Deploy**:

```bash
# Build and start
docker-compose -f docker-compose-full.yml up -d

# View logs
docker-compose logs -f integration

# Stop
docker-compose down
```

---

## Cloud Deployment

### AWS Deployment

**Architecture**:
```
                      ┌─────────────────┐
                      │  Application    │
                      │  Load Balancer  │
                      └────────┬────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
       ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼──────┐
       │  EC2 (NIDS) │  │ EC2 (NIDS)│  │  EC2 (NIDS) │
       │   t3.large  │  │  t3.large │  │   t3.large  │
       └─────────────┘  └───────────┘  └─────────────┘
              │                │                │
              └────────────────┴────────────────┘
                               │
                      ┌────────▼────────┐
                      │  EC2 (Integration)│
                      │    t3.xlarge     │
                      └────────┬─────────┘
                               │
                      ┌────────▼────────┐
                      │  Amazon ES      │
                      │  (3-node cluster)│
                      └─────────────────┘
```

**Terraform Configuration**:

```hcl
# main.tf
provider "aws" {
  region = "us-east-1"
}

# VPC
resource "aws_vpc" "hybrid_ids" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "hybrid-ids-vpc"
  }
}

# NIDS instances
resource "aws_instance" "nids" {
  count         = 3
  ami           = "ami-0c55b159cbfafe1f0"  # Ubuntu 22.04
  instance_type = "t3.large"
  subnet_id     = aws_subnet.public.id

  user_data = file("scripts/install_nids.sh")

  tags = {
    Name = "hybrid-ids-nids-${count.index + 1}"
  }
}

# Integration instance
resource "aws_instance" "integration" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.xlarge"
  subnet_id     = aws_subnet.private.id

  user_data = file("scripts/install_integration.sh")

  tags = {
    Name = "hybrid-ids-integration"
  }
}

# Elasticsearch Service
resource "aws_elasticsearch_domain" "hybrid_ids" {
  domain_name           = "hybrid-ids-logs"
  elasticsearch_version = "7.10"

  cluster_config {
    instance_type  = "r5.large.elasticsearch"
    instance_count = 3
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 100
  }
}
```

**Deploy**:

```bash
terraform init
terraform plan
terraform apply
```

---

## Troubleshooting

### Common Issues

**1. NIDS Not Capturing Traffic**

```bash
# Check interface
ip link show

# Check permissions
sudo setcap cap_net_raw,cap_net_admin+eip /path/to/sids

# Test packet capture
sudo tcpdump -i eth0 -c 10
```

**2. Integration Layer Connection Issues**

```bash
# Check ZMQ ports
netstat -tuln | grep -E "(5556|5557)"

# Test ZMQ connection
python3 -c "import zmq; ctx = zmq.Context(); sock = ctx.socket(zmq.SUB); sock.connect('tcp://localhost:5556'); print('OK')"

# Check logs
tail -f logs/hybrid_ids.log
```

**3. Elasticsearch Not Accessible**

```bash
# Check service
curl http://localhost:9200

# Check Docker container
docker logs hybrid-ids-elasticsearch

# Restart Elasticsearch
docker-compose restart elasticsearch
```

**4. High CPU Usage**

```bash
# Check process usage
top -p $(pgrep -d',' -f 'sids|hids|hybrid_ids')

# Reduce worker threads
# Edit config/hybrid_ids_config.yaml:
performance:
  threads:
    alert_processor: 2
```

### Monitoring

**Check System Status**:

```bash
# NIDS status
sudo systemctl status hybrid-ids-nids

# Integration status
sudo systemctl status hybrid-ids-integration

# HIDS status
sudo systemctl status hybrid-ids-hids

# ELK stack
docker-compose ps

# View logs
journalctl -u hybrid-ids-* -f
```

---

## Performance Tuning

### NIDS Optimization

```bash
# Increase ring buffer
sudo ethtool -G eth0 rx 4096 tx 4096

# Disable offloading
sudo ethtool -K eth0 gro off lro off

# CPU affinity
taskset -c 0,1 ./sids -i eth0
```

### Elasticsearch Optimization

```yaml
# elasticsearch.yml
indices.memory.index_buffer_size: 30%
indices.fielddata.cache.size: 40%
thread_pool.write.queue_size: 1000
```

---

## Security Hardening

**1. Enable SSL/TLS for Elasticsearch**:

```yaml
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true
```

**2. Configure Firewall**:

```bash
sudo ufw default deny incoming
sudo ufw allow from 10.100.0.0/24 to any port 5556
sudo ufw allow from 10.100.0.0/24 to any port 5557
sudo ufw allow from 10.100.0.0/24 to any port 9200
sudo ufw enable
```

**3. Enable Audit Logging**:

```yaml
# config/hybrid_ids_config.yaml
logging:
  level: "INFO"
  file:
    enabled: true
    path: "/var/log/hybrid-ids/audit.log"
```

---

**Next Steps**: See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for usage instructions.
