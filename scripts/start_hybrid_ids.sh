#!/bin/bash
# Startup script for Hybrid IDS (NIDS + HIDS integrated system)
# This script orchestrates the complete integrated intrusion detection system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Hybrid IDS Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print colored messages
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Cleanup function
cleanup() {
    echo ""
    print_status "Cleaning up..."

    # Kill background processes
    if [ ! -z "$NIDS_PID" ]; then
        print_status "Stopping NIDS (PID: $NIDS_PID)..."
        kill -TERM $NIDS_PID 2>/dev/null || true
    fi

    if [ ! -z "$HIDS_PID" ]; then
        print_status "Stopping HIDS (PID: $HIDS_PID)..."
        kill -TERM $HIDS_PID 2>/dev/null || true
    fi

    if [ ! -z "$HYBRID_PID" ]; then
        print_status "Stopping Hybrid Controller (PID: $HYBRID_PID)..."
        kill -TERM $HYBRID_PID 2>/dev/null || true
    fi

    print_success "Cleanup complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Step 1: Check prerequisites
print_status "Step 1/8: Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"

# Check for required Python packages
print_status "Checking Python dependencies..."
python3 -c "import yaml, zmq, elasticsearch, psutil, watchdog" 2>/dev/null
if [ $? -ne 0 ]; then
    print_error "Missing Python dependencies"
    print_status "Installing dependencies..."
    pip3 install -r "$PROJECT_ROOT/requirements.txt"
fi
print_success "Python dependencies satisfied"

# Step 2: Load configuration
print_status "Step 2/8: Loading configuration..."

CONFIG_FILE="$PROJECT_ROOT/config/hybrid_ids_config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi
print_success "Configuration loaded"

# Step 3: Check/Start ELK Stack (optional)
print_status "Step 3/8: Checking ELK Stack..."

if command_exists docker && command_exists docker-compose; then
    print_status "Docker found. Would you like to start the ELK stack?"
    read -p "Start ELK stack? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Starting ELK stack..."
        cd "$PROJECT_ROOT/elk"
        docker-compose up -d
        print_success "ELK stack started"

        print_status "Waiting for Elasticsearch to be ready..."
        sleep 10

        # Load Elasticsearch template
        print_status "Loading Elasticsearch index template..."
        curl -X PUT "localhost:9200/_index_template/hybrid-ids-template" \
             -H 'Content-Type: application/json' \
             -d @"$PROJECT_ROOT/elk/elasticsearch/templates/hybrid-ids-template.json" \
             2>/dev/null

        print_success "Elasticsearch template loaded"
        cd "$PROJECT_ROOT"
    else
        print_warning "ELK stack not started (optional)"
    fi
else
    print_warning "Docker not found - ELK stack will not be started (optional)"
fi

# Step 4: Select components to run
print_status "Step 4/8: Component selection..."

echo ""
echo "Select which components to run:"
echo "  1) Complete Hybrid IDS (NIDS + HIDS + Integration)"
echo "  2) HIDS only"
echo "  3) NIDS only"
echo "  4) Integration layer only (requires NIDS/HIDS started separately)"
echo ""
read -p "Enter choice [1-4]: " COMPONENT_CHOICE

# Step 5: Network interface selection (for NIDS)
if [ "$COMPONENT_CHOICE" == "1" ] || [ "$COMPONENT_CHOICE" == "3" ]; then
    print_status "Step 5/8: Network interface selection..."

    echo ""
    echo "Available network interfaces:"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        ip -o link show | awk -F': ' '{print "  - " $2}'
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        ifconfig -l | tr ' ' '\n' | awk '{print "  - " $1}'
    fi
    echo ""

    read -p "Enter network interface name: " INTERFACE

    if [ -z "$INTERFACE" ]; then
        print_error "No interface specified"
        exit 1
    fi

    print_success "Interface selected: $INTERFACE"
else
    print_status "Step 5/8: Network interface selection (skipped)"
fi

# Step 6: Build NIDS (if needed)
if [ "$COMPONENT_CHOICE" == "1" ] || [ "$COMPONENT_CHOICE" == "3" ]; then
    print_status "Step 6/8: Checking NIDS build..."

    NIDS_BUILD_DIR="$PROJECT_ROOT/build"

    if [ ! -f "$NIDS_BUILD_DIR/sids" ] || [ ! -f "$NIDS_BUILD_DIR/nids" ]; then
        print_warning "NIDS not built. Building now..."

        mkdir -p "$NIDS_BUILD_DIR"
        cd "$NIDS_BUILD_DIR"
        cmake .. -DCMAKE_BUILD_TYPE=Release
        cmake --build . --config Release -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)

        if [ $? -eq 0 ]; then
            print_success "NIDS built successfully"
        else
            print_error "NIDS build failed"
            exit 1
        fi

        cd "$PROJECT_ROOT"
    else
        print_success "NIDS already built"
    fi
else
    print_status "Step 6/8: NIDS build check (skipped)"
fi

# Step 7: Create necessary directories
print_status "Step 7/8: Creating directories..."

mkdir -p "$PROJECT_ROOT/logs/alerts"
mkdir -p "$PROJECT_ROOT/logs/hids"
mkdir -p "$PROJECT_ROOT/logs/nids"
mkdir -p "$PROJECT_ROOT/data/hids"

print_success "Directories created"

# Step 8: Start components
print_status "Step 8/8: Starting components..."

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Starting Hybrid IDS Components${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

case $COMPONENT_CHOICE in
    1)
        # Complete Hybrid IDS
        print_status "Starting complete Hybrid IDS system..."

        # Start NIDS
        print_status "Starting NIDS..."
        cd "$PROJECT_ROOT/build"
        sudo ./sids -i "$INTERFACE" > "$PROJECT_ROOT/logs/nids/sids.log" 2>&1 &
        NIDS_PID=$!
        print_success "NIDS started (PID: $NIDS_PID)"

        sleep 2

        # Start Hybrid IDS controller (includes HIDS)
        print_status "Starting Hybrid IDS controller..."
        cd "$PROJECT_ROOT/src/integration"
        python3 hybrid_ids.py -c "$CONFIG_FILE" > "$PROJECT_ROOT/logs/hybrid_ids.log" 2>&1 &
        HYBRID_PID=$!
        print_success "Hybrid IDS controller started (PID: $HYBRID_PID)"

        ;;

    2)
        # HIDS only
        print_status "Starting HIDS only..."
        cd "$PROJECT_ROOT/src/hids"
        python3 hids_main.py -c "$PROJECT_ROOT/config/hids/hids_config.yaml" &
        HIDS_PID=$!
        print_success "HIDS started (PID: $HIDS_PID)"
        ;;

    3)
        # NIDS only
        print_status "Starting NIDS only..."
        cd "$PROJECT_ROOT/build"
        sudo ./sids -i "$INTERFACE" &
        NIDS_PID=$!
        print_success "NIDS started (PID: $NIDS_PID)"
        ;;

    4)
        # Integration layer only
        print_status "Starting integration layer..."
        cd "$PROJECT_ROOT/src/integration"
        python3 hybrid_ids.py -c "$CONFIG_FILE" &
        HYBRID_PID=$!
        print_success "Integration layer started (PID: $HYBRID_PID)"
        ;;

    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Hybrid IDS Running${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

print_success "Hybrid IDS started successfully!"
echo ""
print_status "Logs:"
echo "  - Hybrid IDS: $PROJECT_ROOT/logs/hybrid_ids.log"
echo "  - NIDS: $PROJECT_ROOT/logs/nids/sids.log"
echo "  - Alerts: $PROJECT_ROOT/logs/alerts/unified_alerts.jsonl"
echo ""

if command_exists docker; then
    print_status "Dashboards:"
    echo "  - Kibana: http://localhost:5601"
    echo "  - Elasticsearch: http://localhost:9200"
    echo ""
fi

print_status "Press Ctrl+C to stop all components"
echo ""

# Wait for processes
wait
