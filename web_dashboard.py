#!/usr/bin/env python3
"""
Simple Web Dashboard for Hybrid IDS
Accessible on http://localhost:8080
"""

from flask import Flask, render_template_string, jsonify
import json
import os
from pathlib import Path
from datetime import datetime
import psutil

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Hybrid IDS Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .stat-card h3 {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
        }
        .alerts-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .alerts-section h2 {
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        .alert-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 10px;
            border-left: 4px solid;
        }
        .alert-critical { border-left-color: #ff4757; }
        .alert-high { border-left-color: #ff6348; }
        .alert-medium { border-left-color: #ffa502; }
        .alert-low { border-left-color: #2ed573; }
        .alert-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .alert-details {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status-running { background: #2ed573; }
        .status-stopped { background: #ff4757; }
        .footer {
            text-align: center;
            margin-top: 30px;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Hybrid IDS Dashboard</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>System Status</h3>
                <div class="value">
                    <span class="status-indicator status-running"></span>
                    RUNNING
                </div>
            </div>
            <div class="stat-card">
                <h3>Total Alerts</h3>
                <div class="value">{{ stats.total_alerts }}</div>
            </div>
            <div class="stat-card">
                <h3>HIDS Alerts</h3>
                <div class="value">{{ stats.hids_alerts }}</div>
            </div>
            <div class="stat-card">
                <h3>NIDS Alerts</h3>
                <div class="value">{{ stats.nids_alerts }}</div>
            </div>
            <div class="stat-card">
                <h3>CPU Usage</h3>
                <div class="value">{{ stats.cpu }}%</div>
            </div>
            <div class="stat-card">
                <h3>Memory Usage</h3>
                <div class="value">{{ stats.memory }}%</div>
            </div>
            <div class="stat-card">
                <h3>Active Processes</h3>
                <div class="value">{{ stats.processes }}</div>
            </div>
            <div class="stat-card">
                <h3>Uptime</h3>
                <div class="value">{{ stats.uptime }}</div>
            </div>
        </div>
        
        <div class="alerts-section">
            <h2>📊 Recent Alerts (Last 10)</h2>
            {% if alerts %}
                {% for alert in alerts %}
                <div class="alert-item alert-{{ alert.severity|lower }}">
                    <div class="alert-header">
                        <span>{{ alert.name }}</span>
                        <span>{{ alert.severity }}</span>
                    </div>
                    <div class="alert-details">
                        {{ alert.timestamp }} | {{ alert.source|upper }}
                        {% if alert.src_ip %}
                        | {{ alert.src_ip }} → {{ alert.dst_ip }}
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; opacity: 0.6;">No alerts yet. System is monitoring...</p>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>Hybrid IDS v1.0.0 | Auto-refresh every 5 seconds</p>
            <p>{{ current_time }}</p>
        </div>
    </div>
</body>
</html>
"""

def get_alerts():
    """Read recent alerts from log files"""
    alerts = []
    
    # Read HIDS alerts
    hids_log = Path('logs/hids_alerts.log')
    if hids_log.exists():
        try:
            with open(hids_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-5:]:  # Last 5 HIDS alerts
                    try:
                        alert = json.loads(line.strip())
                        alert['source'] = 'hids'
                        alerts.append(alert)
                    except:
                        pass
        except:
            pass
    
    # Read NIDS alerts
    nids_log = Path('logs/nids_alerts.log')
    if nids_log.exists():
        try:
            with open(nids_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-5:]:  # Last 5 NIDS alerts
                    try:
                        alert = json.loads(line.strip())
                        alert['source'] = 'nids'
                        alerts.append(alert)
                    except:
                        pass
        except:
            pass
    
    # Sort by timestamp and get last 10
    alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return alerts[:10]

def get_stats():
    """Get system statistics"""
    # Count alerts
    hids_count = 0
    nids_count = 0
    
    hids_log = Path('logs/hids_alerts.log')
    if hids_log.exists():
        try:
            with open(hids_log, 'r') as f:
                hids_count = len(f.readlines())
        except:
            pass
    
    nids_log = Path('logs/nids_alerts.log')
    if nids_log.exists():
        try:
            with open(nids_log, 'r') as f:
                nids_count = len(f.readlines())
        except:
            pass
    
    # System stats
    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory().percent
    processes = len(psutil.pids())
    
    # Uptime (simplified)
    uptime = "Running"
    
    return {
        'total_alerts': hids_count + nids_count,
        'hids_alerts': hids_count,
        'nids_alerts': nids_count,
        'cpu': f"{cpu:.1f}",
        'memory': f"{memory:.1f}",
        'processes': processes,
        'uptime': uptime
    }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    alerts = get_alerts()
    stats = get_stats()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template_string(
        HTML_TEMPLATE,
        alerts=alerts,
        stats=stats,
        current_time=current_time
    )

@app.route('/api/stats')
def api_stats():
    """API endpoint for stats"""
    return jsonify(get_stats())

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for alerts"""
    return jsonify(get_alerts())

if __name__ == '__main__':
    print("="*70)
    print("  Hybrid IDS Web Dashboard")
    print("="*70)
    print()
    print("  Dashboard URL: http://localhost:8080")
    print("  Auto-refresh: Every 5 seconds")
    print()
    print("  Press Ctrl+C to stop")
    print("="*70)
    print()
    
    app.run(host='0.0.0.0', port=8080, debug=False)
