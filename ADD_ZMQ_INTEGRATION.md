# Adding ZeroMQ Integration to Complete the System

This guide shows how to add ZeroMQ publishers to HIDS and NIDS to enable the complete integrated system as per the original plan.

---

## What Needs to Be Done

1. Add ZeroMQ publisher to HIDS
2. Add ZeroMQ publisher to NIDS Python
3. Test the integrated system
4. Verify alert flow through the pipeline

---

## Step 1: Add ZeroMQ to HIDS

### Modify `src/hids/hids_main.py`

Add at the top with other imports:
```python
import zmq
```

In the `HybridHIDS.__init__` method, add:
```python
# ZeroMQ publisher for integration
self.zmq_context = None
self.zmq_publisher = None
if self.config.get('zmq_enabled', True):
    try:
        self.zmq_context = zmq.Context()
        self.zmq_publisher = self.zmq_context.socket(zmq.PUB)
        zmq_port = self.config.get('zmq_port', 5557)
        self.zmq_publisher.bind(f"tcp://*:{zmq_port}")
        logger.info(f"ZeroMQ publisher bound to port {zmq_port}")
    except Exception as e:
        logger.error(f"Failed to setup ZeroMQ: {e}")
        self.zmq_publisher = None
```

In the `_export_alerts` method, add after writing to file:
```python
# Publish to ZeroMQ
if self.zmq_publisher:
    try:
        self.zmq_publisher.send_string(json.dumps(alert), zmq.NOBLOCK)
    except Exception as e:
        logger.error(f"Failed to publish to ZeroMQ: {e}")
```

In the `shutdown` method, add:
```python
# Close ZeroMQ
if self.zmq_publisher:
    self.zmq_publisher.close()
if self.zmq_context:
    self.zmq_context.term()
```

---

## Step 2: Add ZeroMQ to NIDS Python

### Modify `src/nids_python/nids_main.py`

Add at the top with other imports:
```python
import zmq
```

In the `HybridNIDS.__init__` method, add:
```python
# ZeroMQ publisher for integration
self.zmq_context = None
self.zmq_publisher = None
if self.config.get('zmq_enabled', True):
    try:
        self.zmq_context = zmq.Context()
        self.zmq_publisher = self.zmq_context.socket(zmq.PUB)
        zmq_port = self.config.get('zmq_port', 5556)
        self.zmq_publisher.bind(f"tcp://*:{zmq_port}")
        logger.info(f"ZeroMQ publisher bound to port {zmq_port}")
    except Exception as e:
        logger.error(f"Failed to setup ZeroMQ: {e}")
        self.zmq_publisher = None
```

In the `_export_alert` method, add after writing to file:
```python
# Publish to ZeroMQ
if self.zmq_publisher:
    try:
        self.zmq_publisher.send_string(json.dumps(alert), zmq.NOBLOCK)
    except Exception as e:
        logger.error(f"Failed to publish to ZeroMQ: {e}")
```

In the `shutdown` method, add:
```python
# Close ZeroMQ
if self.zmq_publisher:
    self.zmq_publisher.close()
if self.zmq_context:
    self.zmq_context.term()
```

---

## Step 3: Test the Integrated System

### Terminal 1: Start Alert Manager
```powershell
python src/integration/alert_manager.py
```

### Terminal 2: Start HIDS
```powershell
python src/hids/hids_main.py --config config/hids/hids_config.yaml --no-logs
```

### Terminal 3: Start NIDS
```powershell
python src/nids_python/nids_main.py -r test.pcap
```

### Terminal 4: Start Integration Controller (Optional)
```powershell
python src/integration/integration_controller.py
```

---

## Step 4: Verify Alert Flow

Check that alerts are flowing:

1. **HIDS alerts** → ZMQ port 5557 → Alert Manager
2. **NIDS alerts** → ZMQ port 5556 → Alert Manager
3. **Alert Manager** → Unified alerts log → `logs/unified_alerts.log`

### Check logs:
```powershell
# HIDS alerts
Get-Content logs\hids_alerts.log -Tail 10

# NIDS alerts
Get-Content logs\nids_alerts.log -Tail 10

# Unified alerts
Get-Content logs\unified_alerts.log -Tail 10
```

---

## Configuration Updates

### Update `config/hids/hids_config.yaml`

Add:
```yaml
# ZeroMQ Integration
zmq_enabled: true
zmq_port: 5557
```

### Create `config/nids/nids_config.yaml`

```yaml
# NIDS Configuration
interface: null
pcap_file: test.pcap
packet_count: 0
timeout: null

# Detection
rules_dir: config/nids/rules
alert_log: logs/nids_alerts.log

# ZeroMQ Integration
zmq_enabled: true
zmq_port: 5556
```

---

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Integration Controller (MCP)               │
│  Orchestrates all components, health monitoring         │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────────┐    ┌─────────▼────────┐
│  HIDS            │    │  NIDS            │
│  (Python)        │    │  (Python)        │
│                  │    │                  │
│  ZMQ PUB:5557 ───┼────┼──▶ ZMQ PUB:5556 │
└──────────────────┘    └──────────────────┘
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │  Alert Manager          │
        │  ZMQ SUB: 5556, 5557    │
        │  ZMQ PUB: 5559          │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │  Event Correlator       │
        │  ZMQ SUB: 5559          │
        └─────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │  Unified Alerts Log     │
        │  logs/unified_alerts.log│
        └─────────────────────────┘
```

---

## Testing Checklist

- [ ] ZeroMQ installed (`pip install pyzmq`)
- [ ] HIDS modified with ZMQ publisher
- [ ] NIDS modified with ZMQ publisher
- [ ] Alert Manager running
- [ ] HIDS publishing alerts
- [ ] NIDS publishing alerts
- [ ] Alert Manager receiving alerts
- [ ] Unified alerts log created
- [ ] No errors in logs

---

## Troubleshooting

### "Address already in use"
```powershell
# Check what's using the port
netstat -ano | findstr :5557

# Kill the process if needed
taskkill /PID <pid> /F
```

### "No module named 'zmq'"
```powershell
pip install pyzmq
```

### "No alerts received"
```powershell
# Check if publishers are bound
# Check if subscriber is connected
# Verify ports match in configuration
```

### "Connection refused"
```powershell
# Start Alert Manager first
# Then start HIDS and NIDS
# Check firewall settings
```

---

## Next Steps After Integration

1. **Train ML Models**
   ```powershell
   python src/ai/training/train_models.py --dataset data/CICIDS2017.csv
   ```

2. **Deploy ELK Stack**
   ```powershell
   cd elk
   docker-compose up -d
   ```

3. **Build C++ NIDS**
   ```powershell
   mkdir build && cd build
   cmake .. && cmake --build . --config Release
   ```

---

## Summary

By following these steps, you will have:

✅ Complete ZeroMQ integration
✅ All components communicating
✅ Unified alert pipeline
✅ Event correlation capability
✅ Full system as per original plan

**Estimated Time**: 1-2 hours

**Difficulty**: Medium

**Result**: Fully integrated Hybrid IDS system
