#!/bin/bash
# ============================================
# Hybrid IDS - HIDS Startup Script (Linux/macOS)
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="$PROJECT_ROOT/venv"
HIDS_DIR="$PROJECT_ROOT/src/hids"
CONFIG_FILE="$PROJECT_ROOT/config/hids/hids_config.yaml"
LOG_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Hybrid IDS - HIDS Startup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check for root/sudo (required for some monitoring features)
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}[WARNING] Not running as root.${NC}"
    echo -e "${YELLOW}Some features may be limited (e.g., network monitoring, system logs)${NC}"
    echo -e "${YELLOW}Consider running with: sudo $0${NC}"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create required directories
echo -e "${BLUE}[1/6] Creating required directories...${NC}"
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR"

# Activate virtual environment
echo -e "${BLUE}[2/6] Activating virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}[ERROR] Virtual environment not found at $VENV_DIR${NC}"
    echo -e "${YELLOW}Please run: python3 -m venv venv${NC}"
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Check dependencies
echo -e "${BLUE}[3/6] Checking dependencies...${NC}"
python3 -c "import psutil, yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[WARNING] Missing dependencies. Installing...${NC}"
    pip install psutil pyyaml watchdog elasticsearch
fi

# Check configuration
echo -e "${BLUE}[4/6] Checking configuration...${NC}"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}[WARNING] Config file not found. Using default configuration.${NC}"
    CONFIG_FILE=""
fi

# Check if Elasticsearch is needed
if [ -n "$CONFIG_FILE" ]; then
    ES_ENABLED=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['elasticsearch_enabled'])" 2>/dev/null || echo "false")
    if [ "$ES_ENABLED" = "True" ]; then
        echo -e "${BLUE}[5/6] Checking Elasticsearch connection...${NC}"
        ES_HOST=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['elasticsearch_hosts'][0])" 2>/dev/null || echo "http://localhost:9200")
        curl -s "$ES_HOST" > /dev/null
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}[WARNING] Cannot connect to Elasticsearch at $ES_HOST${NC}"
            echo -e "${YELLOW}HIDS will run without Elasticsearch integration${NC}"
        else
            echo -e "${GREEN}✓ Elasticsearch connected${NC}"
        fi
    fi
fi

# Start HIDS
echo -e "${BLUE}[6/6] Starting HIDS...${NC}"
echo ""

cd "$HIDS_DIR"

# Build command
CMD="python3 hids_main.py"

if [ -n "$CONFIG_FILE" ]; then
    CMD="$CMD --config $CONFIG_FILE"
fi

# Check for command line arguments
if [ "$1" = "--no-files" ]; then
    CMD="$CMD --no-files"
fi

if [ "$1" = "--no-processes" ]; then
    CMD="$CMD --no-processes"
fi

if [ "$1" = "--no-logs" ]; then
    CMD="$CMD --no-logs"
fi

if [ "$1" = "--elasticsearch" ]; then
    CMD="$CMD --elasticsearch"
fi

echo -e "${GREEN}Starting HIDS with command:${NC}"
echo -e "${YELLOW}$CMD${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop${NC}"
echo ""

# Execute
exec $CMD
