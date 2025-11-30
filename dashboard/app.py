"""
SENTINEL | CORE - Security Operations Center
Professional SIEM Dashboard with Domain Separation

Built by: Security Engineering Team
Last Modified: 2024-11-30
NOTE: Separated NIDS and HIDS into distinct operational domains
TODO: Add cross-domain correlation engine for advanced threat detection
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sys
import os
import logging
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ml.prediction_engine import PredictionEngine
from utils.mock_generator import MockDataGenerator
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Prediction Engine
engine = PredictionEngine()
try:
    engine.load_all()
    logger.info("✓ All ML models loaded successfully")
except Exception as e:
    logger.error(f"[!] CRITICAL: Model loading failed - {e}")
    logger.warning("[!] Defaulting to Safe Mode (simulation only)")

APP_START_TIME = time.time()

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    assets_folder='assets'
)

app.title = f"{config.COMPANY_NAME} | {config.PRODUCT_NAME}"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_stat_card(title, value, icon, id_suffix="", color_class="stat-card-value"):
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"fas fa-{icon} fa-2x", style={"color": config.ACCENT_COLOR_PRIMARY}),
                html.Div([
                    html.H4(value, id=f"stat-value-{id_suffix}", className=f"{color_class} mb-0"),
                    html.P(title, className="text-muted mb-0", style={"fontSize": "0.85rem"})
                ], style={"marginLeft": "15px"})
            ], style={"display": "flex", "alignItems": "center"})
        ])
    ], className="mb-3 active-card", style={"backgroundColor": "#1a1a1a"})

def create_pipeline_stage(stage_num, icon, title, subtitle, tooltip, id_suffix):
    """
    Create a pipeline stage card for decision flowchart
    
    Args:
        stage_num: Stage number (1-4)
        icon: FontAwesome icon name
        title: Stage title (e.g., "TRAFFIC INPUT")
        subtitle: Plain language explanation
        tooltip: Detailed tooltip text
        id_suffix: Unique ID suffix for this stage
    """
    return html.Div([
        html.Div([
            html.I(className=f"fas fa-{icon} pipeline-stage-icon", id=f"stage-icon-{id_suffix}"),
            html.Div([
                html.Span(f"STAGE {stage_num}", style={"fontSize": "0.65rem", "color": "#666"}),
            ]),
            html.Div(title, className="pipeline-stage-title pipeline-tooltip", **{"data-tooltip": tooltip}),
            html.Div(subtitle, className="pipeline-stage-subtitle"),
            html.Div(id=f"stage-status-{id_suffix}", className="pipeline-stage-status")
        ], id=f"pipeline-stage-{id_suffix}", className="pipeline-stage")
    ], style={"flex": "1"})


def create_header():
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-shield-alt fa-2x", style={"color": config.ACCENT_COLOR_PRIMARY, "marginRight": "15px"}),
                        html.Div([
                            html.Div([
                                html.Span(config.COMPANY_NAME, className="company"),
                                html.Span("|", className="separator"),
                                html.Span(config.PRODUCT_NAME, className="product")
                            ], className="navbar-brand mb-0"),
                            html.P(config.TAGLINE, className="mb-0", style={"fontSize": "0.7rem", "color": "#666", "letterSpacing": "0.15em"})
                        ])
                    ], style={"display": "flex", "alignItems": "center"})
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.Span("UPTIME: ", style={"color": "#666", "fontSize": "0.8rem"}),
                            html.Span(id="uptime-counter", className="uptime-counter")
                        ], className="mb-1"),
                        html.Div([
                            html.Span("STATUS: ", style={"color": "#666", "fontSize": "0.8rem"}),
                            html.Span(id="system-status", children="MONITORING", style={"color": config.ACCENT_COLOR_SUCCESS, "fontWeight": "bold", "fontSize": "0.8rem"})
                        ])
                    ], style={"textAlign": "right"})
                ], width=6)
            ], className="w-100")
        ], fluid=True),
        color="dark",
        dark=True,
        className="mb-4"
    )

def create_sidebar():
    return dbc.Card([
        dbc.CardHeader("SIMULATION CONTROL", style={"fontWeight": "bold", "color": config.ACCENT_COLOR_DANGER}),
        dbc.CardBody([
            # Network Operations
            html.Div([
                html.H6("NETWORK OPERATIONS", className="mb-2", style={"color": config.NIDS_COLOR_PRIMARY, "fontSize": "0.85rem", "fontWeight": "bold"}),
                dbc.Button("Inject DDoS", id="btn-ddos", color="danger", outline=True, size="sm", className="w-100 mb-2"),
                dbc.Button("Inject Port Scan", id="btn-portscan", color="warning", outline=True, size="sm", className="w-100 mb-2"),
                dbc.Button("Inject Brute Force", id="btn-bruteforce", color="warning", outline=True, size="sm", className="w-100 mb-3"),
            ]),
            
            html.Hr(),
            
            # Host Operations
            html.Div([
                html.H6("HOST OPERATIONS", className="mb-2", style={"color": config.HIDS_COLOR_PRIMARY, "fontSize": "0.85rem", "fontWeight": "bold"}),
                dbc.Button("Inject Rootkit", id="btn-rootkit", color="danger", outline=True, size="sm", className="w-100 mb-2"),
                dbc.Button("Inject Ransomware", id="btn-ransomware", color="warning", outline=True, size="sm", className="w-100 mb-3"),
            ]),
            
            html.Hr(),
            
            dbc.Button("Return to Normal", id="btn-normal", color="success", size="sm", className="w-100 mb-3"),
            
            html.Label("Traffic Intensity", className="text-muted small"),
            dcc.Slider(
                id='intensity-slider',
                min=1, max=3, step=1,
                marks={1: 'Low', 2: 'Med', 3: 'High'},
                value=2,
                className="mb-3"
            ),
            
            html.Div(id="simulation-status", className="mt-3 small text-center text-muted")
        ])
    ], className="active-card", style={"backgroundColor": "#1a1a1a"})

def create_status_footer():
    return html.Div([
        html.Div([
            html.Span([
                html.Span("RAM: ", className="status-label"),
                html.Span(f"{config.FAKE_RAM_USAGE}%", className="status-value")
            ], className="status-item"),
            html.Span([
                html.Span("NODE: ", className="status-label"),
                html.Span(config.NODE_NAME, className="status-value")
            ], className="status-item"),
            html.Span([
                html.Span("SECURE: ", className="status-label"),
                html.Span("TRUE" if config.SECURE_CONNECTION else "FALSE", className="status-value success")
            ], className="status-item"),
        ]),
        html.Div([
            html.Span(id="live-time", style={"fontSize": "0.75rem", "color": "#666"})
        ])
    ], className="status-footer")

# ============================================================================
# MAIN LAYOUT
# ============================================================================

app.layout = dbc.Container([
    # Stores
    dcc.Store(id='network-attack-state', data={'type': 'BENIGN', 'intensity': 'Medium'}),
    dcc.Store(id='host-attack-state', data={'type': 'BENIGN', 'intensity': 'Medium'}),
    dcc.Store(id='traffic-history', data={'times': [], 'values': []}),
    dcc.Store(id='syscall-history', data=[]),
    dcc.Store(id='log-history', data=[]),
    
    dcc.Interval(id='interval-component', interval=config.REFRESH_INTERVAL, n_intervals=0),
    
    create_header(),
    
    html.Div(id="alert-area"),
    
    dbc.Row([
        # Sidebar
        dbc.Col([
            create_sidebar(),
            html.Br(),
            dbc.Card([
                dbc.CardHeader("MODEL STATUS"),
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-brain me-2"),
                        "NIDS SIDS: ", 
                        html.Span("ACTIVE" if engine.nids_sids_loaded else "OFFLINE", 
                                 className="text-success" if engine.nids_sids_loaded else "text-danger")
                    ], className="mb-2 small"),
                    html.Div([
                        html.I(className="fas fa-search me-2"),
                        "NIDS A-IDS: ",
                        html.Span("ACTIVE" if engine.nids_aids_loaded else "OFFLINE",
                                 className="text-success" if engine.nids_aids_loaded else "text-danger")
                    ], className="mb-2 small"),
                    html.Div([
                        html.I(className="fas fa-microchip me-2"),
                        "HIDS LSTM: ",
                        html.Span("ACTIVE" if engine.hids_loaded else "OFFLINE",
                                 className="text-success" if engine.hids_loaded else "text-danger")
                    ], className="small")
                ])
            ], className="active-card", style={"backgroundColor": "#1a1a1a"})
        ], width=2),
        
        # Main Content with Tabs
        dbc.Col([
            dcc.Tabs(id="domain-tabs", value='tab-nids', className="custom-tabs", children=[
                # NIDS Tab
                dcc.Tab(label='NETWORK DEFENSE (NIDS)', value='tab-nids', className="tab-nids", children=[
                    html.Div([
                        # NIDS Decision Pipeline
                        html.Div([
                            html.H5("Network Defense Decision Pipeline", className="mb-3", style={"color": config.NIDS_COLOR_PRIMARY}),
                            html.Div([
                                create_pipeline_stage(
                                    1, "globe", "TRAFFIC INPUT", 
                                    "Network packets arriving",
                                    "Raw network traffic from monitored interfaces",
                                    "nids-input"
                                ),
                                html.Div("→", className="pipeline-arrow", id="arrow-nids-1"),
                                create_pipeline_stage(
                                    2, "shield-alt", "KNOWN THREATS", 
                                    "Checking 'Wanted' list (S-IDS)",
                                    "S-IDS: Matches known hacker patterns like a fingerprint database",
                                    "nids-sids"
                                ),
                                html.Div("→", className="pipeline-arrow", id="arrow-nids-2"),
                                create_pipeline_stage(
                                    3, "radar", "BEHAVIOR SCAN", 
                                    "Checking anomalies (A-IDS)",
                                    "A-IDS: Detects weird behavior never seen before using ML",
                                    "nids-aids"
                                ),
                                html.Div("→", className="pipeline-arrow", id="arrow-nids-3"),
                                create_pipeline_stage(
                                    4, "check-circle", "FINAL DECISION", 
                                    "Allow or Block",
                                    "Final verdict based on all checks",
                                    "nids-decision"
                                ),
                            ], className="pipeline-container")
                        ], className="mb-4 mt-3"),
                        
                        # SIDS vs A-IDS Row
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader(html.H6("SIDS: Known Signatures", className="mb-0")),
                                    dbc.CardBody([
                                        dcc.Graph(id='sids-bar-chart', config={'displayModeBar': False}, style={'height': '250px'})
                                    ])
                                ], className="active-card", style={"backgroundColor": "#1a1a1a"})
                            ], width=6),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader(html.H6("A-IDS: Anomaly Radar", className="mb-0")),
                                    dbc.CardBody([
                                        dcc.Graph(id='aids-gauge-chart', config={'displayModeBar': False}, style={'height': '250px'})
                                    ])
                                ], className="active-card", style={"backgroundColor": "#1a1a1a"})
                            ], width=6),
                        ], className="mb-4"),
                        
                        # Network Traffic Chart
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader(html.H6("Live Network Traffic Volume", className="mb-0")),
                                    dbc.CardBody([
                                        dcc.Graph(id='network-traffic-chart', config={'displayModeBar': False}, style={'height': '250px'})
                                    ])
                                ], className="active-card", style={"backgroundColor": "#1a1a1a"})
                            ], width=12),
                        ])
                    ], style={"padding": "1rem"})
                ]),
                
                # HIDS Tab
                dcc.Tab(label='HOST INTEGRITY (HIDS)', value='tab-hids', className="tab-hids", children=[
                    html.Div([
                        # HIDS Decision Pipeline
                        html.Div([
                            html.H5("Host Integrity Decision Pipeline", className="mb-3", style={"color": config.HIDS_COLOR_PRIMARY}),
                            html.Div([
                                create_pipeline_stage(
                                    1, "microchip", "SYSTEM CALLS", 
                                    "Process operations monitored",
                                    "Raw system calls from running processes (read, write, exec, etc.)",
                                    "hids-input"
                                ),
                                html.Div("→", className="pipeline-arrow", id="arrow-hids-1"),
                                create_pipeline_stage(
                                    2, "fingerprint", "SIGNATURE CHECK", 
                                    "Known malicious patterns",
                                    "Checks for known rootkit/malware syscall sequences",
                                    "hids-signature"
                                ),
                                html.Div("→", className="pipeline-arrow", id="arrow-hids-2"),
                                create_pipeline_stage(
                                    3, "brain", "ANOMALY CHECK", 
                                    "LSTM deviation analysis",
                                    "Detects unusual sequences never seen during training",
                                    "hids-lstm"
                                ),
                                html.Div("→", className="pipeline-arrow", id="arrow-hids-3"),
                                create_pipeline_stage(
                                    4, "heartbeat", "SYSTEM STATUS", 
                                    "Healthy or Compromised",
                                    "Final verdict on host integrity",
                                    "hids-decision"
                                ),
                            ], className="pipeline-container")
                        ], className="mb-4 mt-3"),
                        
                        # Sequence Heatmap
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader(html.H6("System Call Sequence Heatmap", className="mb-0")),
                                    dbc.CardBody([
                                        dcc.Graph(id='syscall-heatmap', config={'displayModeBar': False}, style={'height': '250px'})
                                    ])
                                ], className="active-card", style={"backgroundColor": "#1a1a1a"})
                            ], width=12),
                        ], className="mb-4"),
                        
                        # Syscall Distribution
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader(html.H6("Syscall Distribution (Recent Activity)", className="mb-0")),
                                    dbc.CardBody([
                                        dcc.Graph(id='syscall-histogram', config={'displayModeBar': False}, style={'height': '250px'})
                                    ])
                                ], className="active-card", style={"backgroundColor": "#1a1a1a"})
                            ], width=12),
                        ])
                    ], style={"padding": "1rem"})
                ]),
            ]),
            
            # Global Logs Panel (Outside Tabs)
            html.Div([
                dbc.Card([
                    dbc.CardHeader(html.H6("Live Event Logs (Global)", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id='live-logs', className="scan-line", style={
                            "fontFamily": "monospace",
                            "fontSize": "0.75rem",
                            "height": "200px",
                            "overflowY": "scroll",
                            "backgroundColor": "#0a0a0a",
                            "padding": "10px",
                            "borderRadius": "5px",
                            "position": "relative"
                        })
                    ])
                ], className="active-card", style={"backgroundColor": "#1a1a1a"})
            ], className="mt-4")
        ], width=10)
    ]),
    
    create_status_footer()
    
], fluid=True, style={"backgroundColor": "#0d0d0d", "minHeight": "100vh", "padding": "20px"})

# ============================================================================
# CALLBACKS
# ============================================================================

@app.callback(
    [Output('network-attack-state', 'data'),
     Output('host-attack-state', 'data'),
     Output('simulation-status', 'children'),
     Output('alert-area', 'children')],
    [Input('btn-ddos', 'n_clicks'),
     Input('btn-portscan', 'n_clicks'),
     Input('btn-bruteforce', 'n_clicks'),
     Input('btn-rootkit', 'n_clicks'),
     Input('btn-ransomware', 'n_clicks'),
     Input('btn-normal', 'n_clicks'),
     Input('intensity-slider', 'value')],
    [State('network-attack-state', 'data'),
     State('host-attack-state', 'data')]
)
def update_simulation_state(btn_ddos, btn_ps, btn_bf, btn_rk, btn_rw, btn_norm, intensity_val, net_state, host_state):
    ctx = callback_context
    if not ctx.triggered:
        return net_state, host_state, "Status: Normal", None
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    intensity_map = {1: 'Low', 2: 'Medium', 3: 'High'}
    intensity = intensity_map[intensity_val]
    
    new_net_state = net_state.copy()
    new_host_state = host_state.copy()
    new_net_state['intensity'] = intensity
    new_host_state['intensity'] = intensity
    
    alert = None
    status_msg = f"Network: {net_state['type']} | Host: {host_state['type']}"
    
    # Network attacks
    if button_id == 'btn-ddos':
        new_net_state['type'] = 'DDoS'
        status_msg = f"[ALERT] Network: DDoS Attack ({intensity})"
        alert = dbc.Alert("[ALERT] DDoS Attack Pattern Injected (NIDS)", color="danger", duration=3000)
    elif button_id == 'btn-portscan':
        new_net_state['type'] = 'PortScan'
        status_msg = f"[ALERT] Network: Port Scan ({intensity})"
        alert = dbc.Alert("[ALERT] Port Scan Pattern Injected (NIDS)", color="warning", duration=3000)
    elif button_id == 'btn-bruteforce':
        new_net_state['type'] = 'BruteForce'
        status_msg = f"[ALERT] Network: Brute Force ({intensity})"
        alert = dbc.Alert("[ALERT] Brute Force Pattern Injected (NIDS)", color="warning", duration=3000)
    
    # Host attacks
    elif button_id == 'btn-rootkit':
        new_host_state['type'] = 'Rootkit'
        status_msg = f"[ALERT] Host: Rootkit Activity ({intensity})"
        alert = dbc.Alert("[ALERT] Rootkit Pattern Injected (HIDS)", color="danger", duration=3000)
    elif button_id == 'btn-ransomware':
        new_host_state['type'] = 'Ransomware'
        status_msg = f"[ALERT] Host: Ransomware Activity ({intensity})"
        alert = dbc.Alert("[ALERT] Ransomware Pattern Injected (HIDS)", color="warning", duration=3000)
    
    # Reset
    elif button_id == 'btn-normal':
        new_net_state['type'] = 'BENIGN'
        new_host_state['type'] = 'BENIGN'
        status_msg = "✓ All Systems Normal"
        alert = dbc.Alert("[INFO] Returned to Normal Traffic", color="success", duration=3000)
    
    elif button_id == 'intensity-slider':
        status_msg = f"Network: {net_state['type']} | Host: {host_state['type']} ({intensity})"
    
    return new_net_state, new_host_state, status_msg, alert

@app.callback(
    [Output('uptime-counter', 'children'),
     Output('live-time', 'children'),
     Output('system-status', 'children'),
     Output('system-status', 'style'),
     
     # NIDS Pipeline Stages (className and status text)
     Output('pipeline-stage-nids-input', 'className'),
     Output('stage-status-nids-input', 'children'),
     Output('arrow-nids-1', 'className'),
     
     Output('pipeline-stage-nids-sids', 'className'),
     Output('stage-status-nids-sids', 'children'),
     Output('arrow-nids-2', 'className'),
     
     Output('pipeline-stage-nids-aids', 'className'),
     Output('stage-status-nids-aids', 'children'),
     Output('arrow-nids-3', 'className'),
     
     Output('pipeline-stage-nids-decision', 'className'),
     Output('stage-status-nids-decision', 'children'),
     
     # HIDS Pipeline Stages
     Output('pipeline-stage-hids-input', 'className'),
     Output('stage-status-hids-input', 'children'),
     Output('arrow-hids-1', 'className'),
     
     Output('pipeline-stage-hids-signature', 'className'),
     Output('stage-status-hids-signature', 'children'),
     Output('arrow-hids-2', 'className'),
     
     Output('pipeline-stage-hids-lstm', 'className'),
     Output('stage-status-hids-lstm', 'children'),
     Output('arrow-hids-3', 'className'),
     
     Output('pipeline-stage-hids-decision', 'className'),
     Output('stage-status-hids-decision', 'children'),
     
     # Charts
     Output('traffic-history', 'data'),
     Output('network-traffic-chart', 'figure'),
     Output('sids-bar-chart', 'figure'),
     Output('aids-gauge-chart', 'figure'),
     Output('syscall-history', 'data'),
     Output('syscall-heatmap', 'figure'),
     Output('syscall-histogram', 'figure'),
     
     # Global logs
     Output('log-history', 'data'),
     Output('live-logs', 'children')],
    [Input('interval-component', 'n_intervals')],
    [State('network-attack-state', 'data'),
     State('host-attack-state', 'data'),
     State('traffic-history', 'data'),
     State('syscall-history', 'data'),
     State('log-history', 'data')]
)
def update_all_metrics(n, net_state, host_state, traffic_hist, syscall_hist, log_hist):
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Uptime
    uptime_seconds = int(time.time() - APP_START_TIME)
    uptime_str = f"{uptime_seconds // 3600:02d}:{(uptime_seconds % 3600) // 60:02d}:{uptime_seconds % 60:02d}"
    
    # Generate network sample
    net_attack = net_state['type']
    net_intensity = net_state['intensity']
    net_sample = MockDataGenerator.generate_single_sample(net_attack, net_intensity)
    
    # Generate host syscall sequence
    host_attack = host_state['type']
    host_intensity = host_state['intensity']
    syscalls = MockDataGenerator.generate_syscall_sequence(host_attack, host_intensity, length=50)
    
    # ========================================================================
    # NIDS WATERFALL LOGIC
    # ========================================================================
    
    # Default: All stages success
    nids_input_class = "pipeline-stage active"
    nids_input_status = "Active"
    nids_arrow1_class = "pipeline-arrow active"
    
    nids_sids_class = "pipeline-stage success"
    nids_sids_status = "Clean"
    nids_arrow2_class = "pipeline-arrow"
    
    nids_aids_class = "pipeline-stage success"
    nids_aids_status = "Normal"
    nids_arrow3_class = "pipeline-arrow"
    
    nids_decision_class = "pipeline-stage success"
    nids_decision_status = "ALLOW"
    
    net_is_attack = False
    net_prediction = "BENIGN"
    anomaly_score = 0.0
    sids_probs = {'BENIGN': 0.9, 'DoS': 0.05, 'Bot': 0.03, 'PortScan': 0.02}
    
    # Run ML predictions
    try:
        if engine.nids_sids_loaded or engine.nids_aids_loaded:
            features = net_sample.values
            results = engine.predict_nids(features)
            
            if 'sids' in results:
                pred = results['sids']['predictions'][0]
                if pred != 'BENIGN':
                    net_is_attack = True
                    net_prediction = pred
                if 'probabilities' in results['sids']:
                    probs = results['sids']['probabilities'][0]
                    classes = engine.nids_label_encoder.classes_
                    sids_probs = dict(zip(classes, probs))
            
            if 'aids' in results:
                anomaly_score = float(results['aids']['anomaly_scores'][0])
                if results['aids']['is_anomaly'][0]:
                    if not net_is_attack:  # Only if SIDS didn't catch it
                        net_is_attack = True
                        net_prediction = "Anomaly"
            
            # Demo override
            if net_attack != 'BENIGN' and not net_is_attack:
                net_is_attack = True
                net_prediction = net_attack
                anomaly_score = 0.8
                
    except Exception as e:
        logger.error(f"[!] Network prediction failure: {e}")
    
    # Apply Waterfall Logic
    if net_attack in ['DDoS', 'PortScan', 'BruteForce']:
        # Known threat - SIDS blocks it
        nids_sids_class = "pipeline-stage danger"
        nids_sids_status = f"[THREAT] {net_attack} Detected"
        nids_arrow2_class = "pipeline-arrow"  # Not active
        
        # A-IDS is skipped (short-circuit)
        nids_aids_class = "pipeline-stage inactive"
        nids_aids_status = "Scan Skipped"
        nids_arrow3_class = "pipeline-arrow"
        
        # Final decision: BLOCK
        nids_decision_class = "pipeline-stage danger"
        nids_decision_status = "[BLOCKED]"
        
    elif anomaly_score > 0.7:
        # Zero-day / Unknown threat - A-IDS catches it
        nids_sids_class = "pipeline-stage success"
        nids_sids_status = "✓ No Signatures"
        nids_arrow2_class = "pipeline-arrow active"
        
        nids_aids_class = "pipeline-stage warning"
        nids_aids_status = f"[ANOMALY] Deviation: {anomaly_score:.2f}"
        nids_arrow3_class = "pipeline-arrow active"
        
        nids_decision_class = "pipeline-stage warning"
        nids_decision_status = "[FLAGGED]"
    
    # ========================================================================
    # HIDS WATERFALL LOGIC
    # ========================================================================
    
    hids_input_class = "pipeline-stage active"
    hids_input_status = "Monitoring"
    hids_arrow1_class = "pipeline-arrow active"
    
    hids_sig_class = "pipeline-stage success"
    hids_sig_status = "Clean"
    hids_arrow2_class = "pipeline-arrow"
    
    hids_lstm_class = "pipeline-stage success"
    hids_lstm_status = "Normal"
    hids_arrow3_class = "pipeline-arrow"
    
    hids_decision_class = "pipeline-stage success"
    hids_decision_status = "✓ HEALTHY"
    
    host_is_attack = False
    recon_error = random.uniform(0.1, 0.3)
    
    if host_attack == 'Rootkit':
        # Signature match - Stage 2 blocks
        host_is_attack = True
        recon_error = random.uniform(0.7, 0.9)
        
        hids_sig_class = "pipeline-stage danger"
        hids_sig_status = "[THREAT] Rootkit Pattern"
        hids_arrow2_class = "pipeline-arrow"
        
        # LSTM skipped
        hids_lstm_class = "pipeline-stage inactive"
        hids_lstm_status = "Scan Skipped"
        hids_arrow3_class = "pipeline-arrow"
        
        hids_decision_class = "pipeline-stage danger"
        hids_decision_status = "[COMPROMISED]"
        
    elif host_attack == 'Ransomware':
        # Behavioral anomaly - LSTM catches it
        host_is_attack = True
        recon_error = random.uniform(0.6, 0.9)
        
        hids_sig_class = "pipeline-stage success"
        hids_sig_status = "✓ No Signatures"
        hids_arrow2_class = "pipeline-arrow active"
        
        hids_lstm_class = "pipeline-stage warning"
        hids_lstm_status = f"[ANOMALY] Error: {recon_error:.2f}"
        hids_arrow3_class = "pipeline-arrow active"
        
        hids_decision_class = "pipeline-stage warning"
        hids_decision_status = "[SUSPICIOUS]"
    
    # System status
    status_text = "MONITORING"
    status_style = {"color": config.ACCENT_COLOR_SUCCESS, "fontWeight": "bold", "fontSize": "0.8rem"}
    
    if net_is_attack or host_is_attack:
        threats = []
        if net_is_attack: threats.append(f"NET:{net_prediction}")
        if host_is_attack: threats.append(f"HOST:{host_attack}")
        status_text = f"[ALERT] {' | '.join(threats)}"
        status_style = {"color": config.ACCENT_COLOR_DANGER, "fontWeight": "bold", "fontSize": "0.8rem"}
    
    # Update traffic history
    times = traffic_hist.get('times', [])
    values = traffic_hist.get('values', [])
    
    current_volume = float(net_sample[' Total Fwd Packets'].iloc[0])
    current_volume += random.randint(-50, 50)
    if current_volume < 0: current_volume = 0
    
    times.append(now.strftime("%H:%M:%S"))
    values.append(current_volume)
    
    if len(times) > config.TRAFFIC_HISTORY_SIZE:
        times = times[-config.TRAFFIC_HISTORY_SIZE:]
        values = values[-config.TRAFFIC_HISTORY_SIZE:]
        
    traffic_data = {'times': times, 'values': values}
    
    # Update syscall history
    syscall_hist.extend(syscalls)
    if len(syscall_hist) > 500:
        syscall_hist = syscall_hist[-500:]
    
    # Create NIDS charts
    fig_traffic = go.Figure()
    fig_traffic.add_trace(go.Scatter(
        x=times, y=values, mode='lines', name='Packets',
        line=dict(color=config.NIDS_COLOR_PRIMARY if not net_is_attack else config.ACCENT_COLOR_DANGER, width=2),
        fill='tozeroy',
        fillcolor=f'rgba(0, 212, 255, 0.1)' if not net_is_attack else 'rgba(255, 42, 42, 0.2)'
    ))
    fig_traffic.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=20, b=40), height=250,
        xaxis=dict(showgrid=True, gridcolor='#222'), yaxis=dict(showgrid=True, gridcolor='#222', title='Packets')
    )
    
    fig_sids = go.Figure(data=[
        go.Bar(x=list(sids_probs.keys()), y=list(sids_probs.values()),
               marker_color=config.NIDS_COLOR_PRIMARY)
    ])
    fig_sids.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=20, b=40), height=250,
        yaxis=dict(title='Probability', range=[0, 1])
    )
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=anomaly_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Anomaly Score"},
        gauge={'axis': {'range': [None, 1]},
               'bar': {'color': config.NIDS_COLOR_SECONDARY},
               'threshold': {'line': {'color': config.ACCENT_COLOR_DANGER, 'width': 4}, 'thickness': 0.75, 'value': 0.7}}
    ))
    fig_gauge.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    # Create HIDS charts
    recent_syscalls = syscall_hist[-100:] if len(syscall_hist) >= 100 else syscall_hist
    heatmap_data = np.array(recent_syscalls).reshape(-1, 10) if len(recent_syscalls) >= 10 else np.array([[0]*10])
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        colorscale=[[0, '#0a0a0a'], [0.5, config.HIDS_COLOR_SECONDARY], [1, config.HIDS_COLOR_PRIMARY]],
        showscale=False
    ))
    fig_heatmap.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20), height=250,
        xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False)
    )
    
    syscall_counts = {}
    syscall_names = {0: 'read', 1: 'write', 2: 'open', 3: 'close', 59: 'execve', 82: 'rename', 105: 'setuid'}
    for sc in recent_syscalls:
        name = syscall_names.get(sc, f'sys_{sc}')
        syscall_counts[name] = syscall_counts.get(name, 0) + 1
    
    top_syscalls = sorted(syscall_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    
    fig_histogram = go.Figure(data=[
        go.Bar(x=[s[0] for s in top_syscalls], y=[s[1] for s in top_syscalls],
               marker_color=config.HIDS_COLOR_PRIMARY)
    ])
    fig_histogram.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=20, b=40), height=250,
        yaxis=dict(title='Count')
    )
    
    # Update logs
    new_log = f"[{time_str}] "
    
    if random.random() < config.EASTER_EGG_PROBABILITY:
        easter_eggs = [
            "[SYSTEM] Heartbeat check: All sensors responding",
            "[SYSTEM] Garbage collection cycle completed",
            "[SYSTEM] Cache refresh: 2847 entries updated",
            "[SYSTEM] Threat intelligence feed synchronized"
        ]
        new_log += random.choice(easter_eggs)
        log_class = "system"
    elif net_is_attack:
        src_ip = f"192.168.1.{random.randint(100, 200)}"
        new_log += f"CRITICAL [NIDS] {net_prediction} detected from {src_ip}"
        log_class = "critical"
    elif host_is_attack:
        new_log += f"CRITICAL [HIDS] {host_attack} activity detected (Recon Error: {recon_error:.2f})"
        log_class = "critical"
    else:
        new_log += f"INFO | Normal traffic flow processed"
        log_class = "info"
        
    log_hist.append({'text': new_log, 'class': log_class})
    if len(log_hist) > config.LOG_HISTORY_SIZE:
        log_hist = log_hist[-config.LOG_HISTORY_SIZE:]
        
    log_elements = []
    for log in reversed(log_hist):
        log_elements.append(html.Div(log['text'], className=f"log-entry {log['class']}"))
    
    return (
        uptime_str, time_str, status_text, status_style,
        
        # NIDS Pipeline
        nids_input_class, nids_input_status, nids_arrow1_class,
        nids_sids_class, nids_sids_status, nids_arrow2_class,
        nids_aids_class, nids_aids_status, nids_arrow3_class,
        nids_decision_class, nids_decision_status,
        
        # HIDS Pipeline
        hids_input_class, hids_input_status, hids_arrow1_class,
        hids_sig_class, hids_sig_status, hids_arrow2_class,
        hids_lstm_class, hids_lstm_status, hids_arrow3_class,
        hids_decision_class, hids_decision_status,
        
        # Charts
        traffic_data, fig_traffic, fig_sids, fig_gauge,
        syscall_hist, fig_heatmap, fig_histogram,
        
        # Logs
        log_hist, log_elements
    )


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    print("="*60)
    print(f"{config.COMPANY_NAME} | {config.PRODUCT_NAME}")
    print(f"    {config.TAGLINE}")
    print("="*60)
    print("Domain-Separated Architecture:")
    print("  • NETWORK DEFENSE (NIDS) - Tab 1")
    print("  • HOST INTEGRITY (HIDS) - Tab 2")
    print("="*60)
    print("Starting server...")
    print("Dashboard: http://127.0.0.1:8050")
    print("Press Ctrl+C to stop")
    print("="*60)
    app.run_server(debug=True, host='127.0.0.1', port=8050)
