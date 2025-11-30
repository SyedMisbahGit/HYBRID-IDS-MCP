"""
SENTINEL | CORE - Configuration
Security Operations Center Dashboard

NOTE: Tuned for CIC-IDS2017 dataset characteristics
TODO: Add support for custom dataset profiles
"""

# ============================================================================
# BRANDING
# ============================================================================
COMPANY_NAME = "SENTINEL"
PRODUCT_NAME = "CORE"
TAGLINE = "Security Operations Center"

# ============================================================================
# UI SETTINGS
# ============================================================================
# Refresh interval in milliseconds (1000ms = 1 second)
REFRESH_INTERVAL = 1000

# Chart history retention (number of data points)
TRAFFIC_HISTORY_SIZE = 60
LOG_HISTORY_SIZE = 20

# Color scheme (Cyberpunk Cyan + Alert Red)
ACCENT_COLOR_PRIMARY = "#00f3ff"  # Neon cyan for active elements
ACCENT_COLOR_DANGER = "#ff2a2a"   # Alert red for threats
ACCENT_COLOR_SUCCESS = "#00ff41"  # Matrix green for normal
ACCENT_COLOR_WARNING = "#ffaa00"  # Amber for warnings

# Domain-specific colors
NIDS_COLOR_PRIMARY = "#00d4ff"    # Cyan for network domain
NIDS_COLOR_SECONDARY = "#0088ff"  # Blue for network charts
HIDS_COLOR_PRIMARY = "#ff8800"    # Orange for host domain
HIDS_COLOR_SECONDARY = "#ffaa00"  # Amber for host charts

# ============================================================================
# ML MODEL SETTINGS
# ============================================================================
# Anomaly detection threshold (0.0 - 1.0)
# NOTE: Set to 0.8 based on ROC curve analysis with CIC-IDS2017
ANOMALY_THRESHOLD = 0.8

# Model paths (relative to project root)
MODELS_DIR = "models"
NIDS_DIR = "models/nids"
HIDS_DIR = "models/hids"

# ============================================================================
# SIMULATION SETTINGS
# ============================================================================
# Network attack types
NETWORK_ATTACK_TYPES = ['DDoS', 'PortScan', 'BruteForce']

# Host attack types
HOST_ATTACK_TYPES = ['Rootkit', 'Ransomware']

# Attack intensity multipliers
INTENSITY_LOW = 0.5
INTENSITY_MEDIUM = 1.0
INTENSITY_HIGH = 2.0

# Easter egg probability (0.0 - 1.0)
# Chance of injecting system heartbeat/GC logs
EASTER_EGG_PROBABILITY = 0.05

# Malicious syscall patterns (for rootkit simulation)
ROOTKIT_SYSCALLS = [59, 105, 1, 2, 3]  # execve, setuid, write, open, close
RANSOMWARE_SYSCALLS = [1, 82, 2]  # write, rename, open (high frequency)

# ============================================================================
# SYSTEM MONITORING (Fake stats for demo)
# ============================================================================
FAKE_RAM_USAGE = 42  # Percentage
NODE_NAME = "LOCALHOST"
SECURE_CONNECTION = True
