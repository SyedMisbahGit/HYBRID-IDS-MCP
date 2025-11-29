"""
Hybrid IDS - Professional SIEM-Style Dashboard
Built with Plotly Dash and Dash Bootstrap Components

Mimics IBM QRadar interface with dark theme and real-time monitoring
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Initialize Dash app with dark theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True
)

app.title = "Hybrid IDS - SIEM Dashboard"

# ============================================================================
# HELPER FUNCTIONS FOR SIMULATED DATA
# ============================================================================

def generate_network_traffic_data(n_points=50):
    """Generate simulated network traffic data"""
    now = datetime.now()
    times = [now - timedelta(seconds=i*2) for i in range(n_points)]
    times.reverse()
    
    # Simulate traffic with some spikes (attacks)
    traffic = [random.randint(100, 500) for _ in range(n_points)]
    # Add attack spikes
    for i in [15, 32, 45]:
        if i < len(traffic):
            traffic[i] = random.randint(800, 1200)
    
    return times, traffic

def generate_attack_distribution():
    """Generate attack type distribution"""
    return {
        'DoS': random.randint(20, 50),
        'DDoS': random.randint(15, 40),
        'PortScan': random.randint(10, 30),
        'BruteForce': random.randint(5, 20),
        'WebAttack': random.randint(3, 15),
        'Infiltration': random.randint(1, 10)
    }

def generate_live_logs(n_logs=10):
    """Generate simulated packet logs"""
    protocols = ['TCP', 'UDP', 'ICMP', 'HTTP']
    ips = [f"192.168.1.{random.randint(1, 255)}" for _ in range(n_logs)]
    ports = [80, 443, 22, 21, 3389, 445, 8080]
    
    logs = []
    for i in range(n_logs):
        timestamp = (datetime.now() - timedelta(seconds=i*5)).strftime("%H:%M:%S")
        protocol = random.choice(protocols)
        src_ip = random.choice(ips)
        dst_port = random.choice(ports)
        severity = random.choice(['INFO', 'WARNING', 'CRITICAL'])
        
        log = f"[{timestamp}] {severity:8} | {protocol:4} | {src_ip:15} → :{dst_port:5}"
        logs.append(log)
    
    return logs

def generate_hids_heatmap():
    """Generate HIDS system call heatmap data"""
    syscalls = ['open', 'read', 'write', 'close', 'fork', 'exec', 'socket', 'connect']
    hours = list(range(24))
    
    data = np.random.randint(0, 100, size=(len(syscalls), len(hours)))
    # Add some anomalies
    data[2, 14] = 250  # Suspicious write activity
    data[6, 18] = 200  # Suspicious socket activity
    
    return syscalls, hours, data

# ============================================================================
# LAYOUT COMPONENTS
# ============================================================================

def create_stat_card(title, value, icon, color="primary"):
    """Create a statistic card"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"fas fa-{icon} fa-2x", style={"color": f"var(--bs-{color})"}),
                html.Div([
                    html.H4(value, className="mb-0", style={"fontWeight": "bold"}),
                    html.P(title, className="text-muted mb-0", style={"fontSize": "0.9rem"})
                ], style={"marginLeft": "15px"})
            ], style={"display": "flex", "alignItems": "center"})
        ])
    ], className="mb-3", style={"backgroundColor": "#1a1a1a", "border": f"1px solid var(--bs-{color})"})

def create_header():
    """Create dashboard header"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-shield-alt fa-2x", style={"color": "#00ff00", "marginRight": "15px"}),
                        html.Div([
                            html.H3("HYBRID IDS", className="mb-0", style={"color": "#00ff00", "fontWeight": "bold"}),
                            html.P("Security Information & Event Management", className="mb-0", style={"fontSize": "0.8rem", "color": "#888"})
                        ])
                    ], style={"display": "flex", "alignItems": "center"})
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.Span(id="live-time", style={"fontSize": "1.2rem", "fontWeight": "bold", "color": "#00ff00"}),
                        html.Span(" | ", style={"margin": "0 10px", "color": "#555"}),
                        html.Span("STATUS: ", style={"color": "#888"}),
                        html.Span("MONITORING", style={"color": "#00ff00", "fontWeight": "bold"})
                    ], style={"textAlign": "right"})
                ], width=6)
            ], className="w-100")
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-4"
    )

# ============================================================================
# MAIN LAYOUT
# ============================================================================

app.layout = dbc.Container([
    # Auto-refresh interval
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),
    
    # Header
    create_header(),
    
    # Top Row: Stat Cards
    dbc.Row([
        dbc.Col(html.Div(id="stat-total-packets"), width=3),
        dbc.Col(html.Div(id="stat-attacks-detected"), width=3),
        dbc.Col(html.Div(id="stat-anomaly-score"), width=3),
        dbc.Col(html.Div(id="stat-active-threats"), width=3),
    ], className="mb-4"),
    
    # Middle Row: Charts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Network Traffic Volume", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(id='live-traffic-chart', config={'displayModeBar': False})
                ])
            ], style={"backgroundColor": "#1a1a1a"})
        ], width=7),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Attack Distribution", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(id='attack-pie-chart', config={'displayModeBar': False})
                ])
            ], style={"backgroundColor": "#1a1a1a"})
        ], width=5),
    ], className="mb-4"),
    
    # Bottom Row: Logs & Heatmap
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Live Event Logs", className="mb-0")),
                dbc.CardBody([
                    html.Div(id='live-logs', style={
                        "fontFamily": "monospace",
                        "fontSize": "0.85rem",
                        "height": "300px",
                        "overflowY": "scroll",
                        "backgroundColor": "#0a0a0a",
                        "padding": "10px",
                        "borderRadius": "5px"
                    })
                ])
            ], style={"backgroundColor": "#1a1a1a"})
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("HIDS System Call Heatmap", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(id='hids-heatmap', config={'displayModeBar': False})
                ])
            ], style={"backgroundColor": "#1a1a1a"})
        ], width=6),
    ])
], fluid=True, style={"backgroundColor": "#0d0d0d", "minHeight": "100vh", "padding": "20px"})

# ============================================================================
# CALLBACKS
# ============================================================================

@app.callback(
    Output('live-time', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_time(n):
    """Update current time"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.callback(
    [Output('stat-total-packets', 'children'),
     Output('stat-attacks-detected', 'children'),
     Output('stat-anomaly-score', 'children'),
     Output('stat-active-threats', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_stats(n):
    """Update statistic cards"""
    total_packets = random.randint(10000, 15000) + n * 100
    attacks = random.randint(50, 150) + n * 2
    anomaly_score = round(random.uniform(0.1, 0.9), 2)
    active_threats = random.randint(3, 12)
    
    return (
        create_stat_card("Total Packets", f"{total_packets:,}", "network-wired", "info"),
        create_stat_card("Attacks Detected", f"{attacks}", "exclamation-triangle", "danger"),
        create_stat_card("Anomaly Score", f"{anomaly_score}", "chart-line", "warning"),
        create_stat_card("Active Threats", f"{active_threats}", "bug", "danger")
    )

@app.callback(
    Output('live-traffic-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_traffic_chart(n):
    """Update network traffic chart"""
    times, traffic = generate_network_traffic_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=traffic,
        mode='lines+markers',
        name='Packets/sec',
        line=dict(color='#00ff00', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.1)'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#0a0a0a',
        margin=dict(l=40, r=20, t=20, b=40),
        height=300,
        xaxis=dict(showgrid=True, gridcolor='#333'),
        yaxis=dict(showgrid=True, gridcolor='#333', title='Packets/sec'),
        hovermode='x unified'
    )
    
    return fig

@app.callback(
    Output('attack-pie-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_attack_pie(n):
    """Update attack distribution pie chart"""
    attack_data = generate_attack_distribution()
    
    fig = go.Figure(data=[go.Pie(
        labels=list(attack_data.keys()),
        values=list(attack_data.values()),
        hole=0.4,
        marker=dict(colors=['#ff4444', '#ff8844', '#ffaa44', '#ffcc44', '#ffee44', '#ff6644'])
    )])
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#1a1a1a',
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
        showlegend=True,
        legend=dict(orientation="v", x=1, y=0.5)
    )
    
    return fig

@app.callback(
    Output('live-logs', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_logs(n):
    """Update live logs"""
    logs = generate_live_logs(15)
    
    log_elements = []
    for log in logs:
        color = "#00ff00" if "INFO" in log else "#ffaa00" if "WARNING" in log else "#ff4444"
        log_elements.append(html.Div(log, style={"color": color, "marginBottom": "5px"}))
    
    return log_elements

@app.callback(
    Output('hids-heatmap', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_heatmap(n):
    """Update HIDS heatmap"""
    syscalls, hours, data = generate_hids_heatmap()
    
    fig = go.Figure(data=go.Heatmap(
        z=data,
        x=[f"{h:02d}:00" for h in hours],
        y=syscalls,
        colorscale='Reds',
        showscale=True
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#1a1a1a',
        plot_bgcolor='#0a0a0a',
        margin=dict(l=80, r=20, t=20, b=40),
        height=300,
        xaxis=dict(title='Hour of Day'),
        yaxis=dict(title='System Call')
    )
    
    return fig

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    print("="*60)
    print("🛡️  Hybrid IDS - SIEM Dashboard")
    print("="*60)
    print("Starting server...")
    print("Dashboard: http://127.0.0.1:8050")
    print("Press Ctrl+C to stop")
    print("="*60)
    app.run_server(debug=True, host='127.0.0.1', port=8050)
