# Deploying ELK Stack for Hybrid IDS

Complete guide to deploy Elasticsearch, Logstash, and Kibana for visualization and analytics.

---

## Prerequisites

### 1. Install Docker Desktop for Windows

**Download and Install**:
```powershell
# Download from: https://www.docker.com/products/docker-desktop/
# Or using Chocolatey:
choco install docker-desktop
```

**System Requirements**:
- Windows 10/11 64-bit: Pro, Enterprise, or Education
- WSL 2 feature enabled
- Hyper-V and Containers Windows features enabled
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

**Enable WSL 2**:
```powershell
# Run PowerShell as Administrator
wsl --install
wsl --set-default-version 2

# Restart computer
```

**Verify Docker**:
```powershell
docker --version
docker-compose --version
```

### 2. Configure Docker Resources

1. Open Docker Desktop
2. Go to Settings → Resources
3. Set:
   - **CPUs**: 4 (minimum 2)
   - **Memory**: 8GB (minimum 6GB)
   - **Swap**: 2GB
   - **Disk**: 20GB

---

## Quick Start

### Option 1: One-Command Deploy

```powershell
cd C:\Users\zsyed\Hybrid-IDS-MCP\elk
docker-compose up -d
```

### Option 2: Step-by-Step Deploy

```powershell
# Navigate to ELK directory
cd C:\Users\zsyed\Hybrid-IDS-MCP\elk

# Pull images (optional, takes time)
docker-compose pull

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## Verify Deployment

### Check Services

```powershell
# All services should be "Up"
docker-compose ps

# Expected output:
# NAME                    STATUS
# elk-elasticsearch-1     Up (healthy)
# elk-logstash-1          Up
# elk-kibana-1            Up (healthy)
```

### Test Endpoints

**Elasticsearch**:
```powershell
# Test connection
curl http://localhost:9200

# Should return JSON with cluster info
```

**Kibana**:
```powershell
# Open in browser
start http://localhost:5601

# Should show Kibana welcome page
```

**Logstash**:
```powershell
# Check if listening
netstat -ano | findstr :5044

# Should show LISTENING on port 5044
```

---

## Configuration

### Elasticsearch

**Location**: `elk/elasticsearch/elasticsearch.yml`

```yaml
cluster.name: "hybrid-ids-cluster"
network.host: 0.0.0.0
discovery.type: single-node
xpack.security.enabled: false
```

**Index Templates**:
- Located in: `elk/elasticsearch/index-templates/`
- Automatically loaded on startup

### Logstash

**Location**: `elk/logstash/pipeline/`

**Main Pipeline** (`logstash.conf`):
```ruby
input {
  file {
    path => "/usr/share/logstash/logs/*.log"
    start_position => "beginning"
    sincedb_path => "/dev/null"
    codec => json
  }
}

filter {
  # Parse JSON alerts
  json {
    source => "message"
  }
  
  # Add geolocation (if available)
  geoip {
    source => "src_ip"
    target => "geoip"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "hybrid-ids-%{+YYYY.MM.dd}"
  }
  
  stdout {
    codec => rubydebug
  }
}
```

### Kibana

**Location**: `elk/kibana/kibana.yml`

```yaml
server.name: kibana
server.host: "0.0.0.0"
elasticsearch.hosts: ["http://elasticsearch:9200"]
```

**Dashboards**:
- Located in: `elk/kibana/dashboards/`
- Import manually via Kibana UI

---

## Import Dashboards

### Step 1: Access Kibana

```powershell
start http://localhost:5601
```

### Step 2: Import Dashboard

1. Click **☰ Menu** → **Stack Management**
2. Click **Saved Objects**
3. Click **Import**
4. Select file: `elk/kibana/dashboards/unified-security-dashboard.ndjson`
5. Click **Import**

### Step 3: View Dashboard

1. Click **☰ Menu** → **Dashboard**
2. Select **Hybrid IDS - Unified Security Dashboard**

---

## Connect Hybrid IDS to ELK

### Option 1: File-based (Logstash)

**Already configured!** Logstash monitors:
- `logs/hids_alerts.log`
- `logs/nids_alerts.log`
- `logs/unified_alerts.log`

Just run your IDS components and alerts will flow automatically.

### Option 2: Direct Elasticsearch Export

**Enable in HIDS**:
```powershell
python src\hids\hids_main.py --elasticsearch --es-host http://localhost:9200
```

**Enable in Configuration**:
```yaml
# config/hids/hids_config.yaml
elasticsearch_enabled: true
elasticsearch_hosts:
  - "http://localhost:9200"
```

---

## Viewing Alerts

### Discover (Raw Data)

1. Go to **☰ Menu** → **Discover**
2. Select index pattern: `hybrid-ids-*`
3. View real-time alerts

### Dashboard (Visualizations)

1. Go to **☰ Menu** → **Dashboard**
2. Select **Hybrid IDS - Unified Security Dashboard**
3. See:
   - Alert timeline
   - Severity distribution
   - Top attacked IPs
   - Attack types
   - Geographic map

### Create Custom Visualizations

1. Go to **☰ Menu** → **Visualize Library**
2. Click **Create visualization**
3. Choose visualization type
4. Select index: `hybrid-ids-*`
5. Configure metrics and buckets

---

## Troubleshooting

### Elasticsearch Won't Start

**Error**: "max virtual memory areas vm.max_map_count [65530] is too low"

**Solution** (WSL 2):
```powershell
# In PowerShell
wsl -d docker-desktop
sysctl -w vm.max_map_count=262144
exit
```

**Permanent Fix**:
```powershell
# Create/edit: C:\Users\<username>\.wslconfig
[wsl2]
kernelCommandLine = sysctl.vm.max_map_count=262144
```

### Out of Memory

**Reduce Memory Usage**:

Edit `elk/docker-compose.yml`:
```yaml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms2g -Xmx2g"  # Reduce from 4g
```

### Port Already in Use

**Check what's using ports**:
```powershell
netstat -ano | findstr :9200
netstat -ano | findstr :5601
netstat -ano | findstr :5044
```

**Kill process or change ports** in `docker-compose.yml`

### Logstash Not Ingesting

**Check logs**:
```powershell
docker-compose logs logstash
```

**Verify file paths**:
```powershell
# Ensure logs directory is mounted
docker-compose exec logstash ls -la /usr/share/logstash/logs/
```

### Kibana Shows "Kibana server is not ready yet"

**Wait 2-3 minutes** for Elasticsearch to be ready, then:
```powershell
docker-compose restart kibana
```

---

## Performance Tuning

### For Development (Low Resources)

```yaml
# docker-compose.yml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
  mem_limit: 2g
  
logstash:
  environment:
    - "LS_JAVA_OPTS=-Xms512m -Xmx512m"
  mem_limit: 1g
  
kibana:
  mem_limit: 1g
```

### For Production (High Performance)

```yaml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms8g -Xmx8g"
  mem_limit: 16g
  deploy:
    resources:
      limits:
        cpus: '4'
```

---

## Data Management

### View Indices

```powershell
curl http://localhost:9200/_cat/indices?v
```

### Delete Old Data

```powershell
# Delete indices older than 7 days
curl -X DELETE "http://localhost:9200/hybrid-ids-2025.10.*"
```

### Set Index Lifecycle Policy

```powershell
# Create ILM policy
curl -X PUT "http://localhost:9200/_ilm/policy/hybrid-ids-policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {}
      },
      "delete": {
        "min_age": "7d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}'
```

---

## Backup and Restore

### Backup Dashboards

```powershell
# Export from Kibana UI
# Stack Management → Saved Objects → Export
```

### Backup Data

```powershell
# Create snapshot repository
curl -X PUT "http://localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backup"
  }
}'

# Create snapshot
curl -X PUT "http://localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"
```

---

## Monitoring

### Check Cluster Health

```powershell
curl http://localhost:9200/_cluster/health?pretty
```

### View Node Stats

```powershell
curl http://localhost:9200/_nodes/stats?pretty
```

### Monitor in Kibana

1. Go to **☰ Menu** → **Stack Monitoring**
2. View Elasticsearch, Logstash, and Kibana metrics

---

## Stopping and Starting

### Stop All Services

```powershell
cd C:\Users\zsyed\Hybrid-IDS-MCP\elk
docker-compose down
```

### Stop and Remove Data

```powershell
docker-compose down -v
```

### Start Services

```powershell
docker-compose up -d
```

### Restart Single Service

```powershell
docker-compose restart elasticsearch
docker-compose restart logstash
docker-compose restart kibana
```

---

## Security (Production)

### Enable X-Pack Security

**elasticsearch.yml**:
```yaml
xpack.security.enabled: true
```

**Set Passwords**:
```powershell
docker-compose exec elasticsearch bin/elasticsearch-setup-passwords auto
```

**Update Logstash**:
```ruby
output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    user => "elastic"
    password => "your-password"
  }
}
```

---

## Complete System Integration

### Terminal 1: Start ELK Stack

```powershell
cd C:\Users\zsyed\Hybrid-IDS-MCP\elk
docker-compose up -d
```

### Terminal 2: Start Hybrid IDS

```powershell
cd C:\Users\zsyed\Hybrid-IDS-MCP
python src\integration\integration_controller.py
```

### Terminal 3: View Dashboard

```powershell
start http://localhost:5601
```

---

## Quick Reference

### Essential Commands

```powershell
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Status
docker-compose ps

# Restart
docker-compose restart

# Remove everything
docker-compose down -v
```

### Essential URLs

- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601
- **Logstash**: http://localhost:9600 (API)

---

## Success Indicators

✅ All containers running (docker-compose ps)
✅ Elasticsearch responds on port 9200
✅ Kibana accessible on port 5601
✅ Logstash ingesting logs
✅ Dashboards imported successfully
✅ Alerts visible in Kibana Discover
✅ Visualizations showing data

---

## Next Steps

1. **Import dashboards** from `elk/kibana/dashboards/`
2. **Start Hybrid IDS** components
3. **Generate alerts** (run tests or live monitoring)
4. **View in Kibana** dashboard
5. **Create custom visualizations**
6. **Set up alerting** (Kibana Alerting)

---

**Estimated Setup Time**: 15-30 minutes
**Difficulty**: Medium
**Result**: Professional security analytics dashboard

---

**Last Updated**: November 1, 2025
**Tested On**: Windows 11, Docker Desktop 4.25+
