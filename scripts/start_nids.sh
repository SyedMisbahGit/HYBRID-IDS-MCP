#!/bin/bash
# ============================================
# Hybrid IDS - NIDS Startup Script (Linux/macOS)
# Starts both S-IDS (Signature) and A-IDS (Anomaly/ML)
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
BUILD_DIR="$PROJECT_ROOT/build"
CONFIG_FILE="$PROJECT_ROOT/config/nids/nids_config.yaml"
LOG_DIR="$PROJECT_ROOT/logs"
VENV_DIR="$PROJECT_ROOT/venv"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Hybrid IDS - NIDS Startup${NC}"
echo -e "${BLUE}  Two-Tier Detection System${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check for root/sudo (required for packet capture)
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Root privileges required for packet capture${NC}"
    echo -e "${YELLOW}Please run with: sudo $0${NC}"
    exit 1
fi

# Create required directories
echo -e "${BLUE}[1/8] Creating required directories...${NC}"
mkdir -p "$LOG_DIR"
mkdir -p "$PROJECT_ROOT/data"

# Check if build directory exists
if [ ! -d "$BUILD_DIR" ]; then
    echo -e "${YELLOW}[WARNING] Build directory not found. Building now...${NC}"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    cmake .. -DCMAKE_BUILD_TYPE=Release
    cmake --build . --config Release -j$(nproc)
    cd "$PROJECT_ROOT"
fi

# Check if executables exist
echo -e "${BLUE}[2/8] Checking NIDS executables...${NC}"
if [ ! -f "$BUILD_DIR/sids" ] || [ ! -f "$BUILD_DIR/nids" ]; then
    echo -e "${RED}[ERROR] NIDS executables not found${NC}"
    echo -e "${YELLOW}Please build the project first:${NC}"
    echo -e "${YELLOW}  cd build${NC}"
    echo -e "${YELLOW}  cmake .. && make${NC}"
    exit 1
fi

echo -e "${GREEN}✓ S-IDS executable found${NC}"
echo -e "${GREEN}✓ NIDS (feature extractor) executable found${NC}"

# Check configuration
echo -e "${BLUE}[3/8] Checking configuration...${NC}"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}[WARNING] Config file not found at $CONFIG_FILE${NC}"
    echo -e "${YELLOW}Using default configuration${NC}"
else
    echo -e "${GREEN}✓ Configuration loaded from $CONFIG_FILE${NC}"
fi

# Detect network interface
echo -e "${BLUE}[4/8] Detecting network interface...${NC}"
DEFAULT_IFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
if [ -z "$DEFAULT_IFACE" ]; then
    DEFAULT_IFACE="eth0"
fi

echo -e "${YELLOW}Default interface: $DEFAULT_IFACE${NC}"
read -p "Enter network interface to monitor [$DEFAULT_IFACE]: " USER_IFACE
INTERFACE="${USER_IFACE:-$DEFAULT_IFACE}"

echo -e "${GREEN}✓ Using interface: $INTERFACE${NC}"

# Check if interface exists
if ! ip link show "$INTERFACE" > /dev/null 2>&1; then
    echo -e "${RED}[ERROR] Interface $INTERFACE not found${NC}"
    echo -e "${YELLOW}Available interfaces:${NC}"
    ip link show | grep -E "^[0-9]+" | awk '{print "  " $2}' | sed 's/:$//'
    exit 1
fi

# Check Python environment for AI engine
echo -e "${BLUE}[5/8] Checking Python environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}[WARNING] Virtual environment not found${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Install AI dependencies
python3 -c "import numpy, sklearn, zmq" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[WARNING] AI engine dependencies missing. Installing...${NC}"
    pip install numpy scikit-learn pyzmq msgpack -q
fi

echo -e "${GREEN}✓ Python environment ready${NC}"

# Ask user which components to start
echo ""
echo -e "${BLUE}[6/8] Select components to start:${NC}"
echo "  1) S-IDS only (Signature-based detection)"
echo "  2) S-IDS + A-IDS (Complete two-tier system)"
echo "  3) Feature extractor only (for testing)"
read -p "Enter choice [1-3] (default: 2): " COMPONENT_CHOICE
COMPONENT_CHOICE="${COMPONENT_CHOICE:-2}"

# Start components
echo ""
echo -e "${BLUE}[7/8] Starting NIDS components...${NC}"

case $COMPONENT_CHOICE in
    1)
        # Start S-IDS only
        echo -e "${GREEN}Starting S-IDS (Tier 1: Signature Detection)...${NC}"
        echo -e "${YELLOW}Command: $BUILD_DIR/sids -i $INTERFACE${NC}"
        echo ""
        "$BUILD_DIR/sids" -i "$INTERFACE"
        ;;

    2)
        # Start complete system
        echo -e "${GREEN}Starting Complete Two-Tier System...${NC}"
        echo ""

        # Start AI engine in background
        echo -e "${BLUE}[Tier 2] Starting AI Engine (A-IDS)...${NC}"
        cd "$PROJECT_ROOT/src/ai/inference"
        python zmq_subscriber.py --model-dir ../../../models --port 5555 > "$LOG_DIR/ai_engine.log" 2>&1 &
        AI_PID=$!
        echo "$AI_PID" > "$PROJECT_ROOT/data/ai_engine.pid"
        echo -e "${GREEN}✓ AI Engine started (PID: $AI_PID)${NC}"

        sleep 2

        # Start NIDS feature extractor in background
        echo -e "${BLUE}[Tier 1/2] Starting Feature Extractor (NIDS)...${NC}"
        cd "$BUILD_DIR"
        ./nids -i "$INTERFACE" --extract-features > "$LOG_DIR/nids_features.log" 2>&1 &
        NIDS_PID=$!
        echo "$NIDS_PID" > "$PROJECT_ROOT/data/nids.pid"
        echo -e "${GREEN}✓ Feature Extractor started (PID: $NIDS_PID)${NC}"

        sleep 2

        # Start S-IDS in foreground
        echo -e "${BLUE}[Tier 1] Starting S-IDS (Signature Detection)...${NC}"
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  Hybrid IDS Running${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo -e "  S-IDS PID:     Foreground"
        echo -e "  NIDS PID:      $NIDS_PID"
        echo -e "  AI Engine PID: $AI_PID"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "${YELLOW}Press Ctrl+C to stop all components${NC}"
        echo ""

        # Cleanup function
        cleanup() {
            echo ""
            echo -e "${YELLOW}Shutting down...${NC}"

            if [ -n "$NIDS_PID" ]; then
                echo "Stopping NIDS (PID: $NIDS_PID)..."
                kill $NIDS_PID 2>/dev/null || true
            fi

            if [ -n "$AI_PID" ]; then
                echo "Stopping AI Engine (PID: $AI_PID)..."
                kill $AI_PID 2>/dev/null || true
            fi

            rm -f "$PROJECT_ROOT/data/nids.pid" "$PROJECT_ROOT/data/ai_engine.pid"
            echo -e "${GREEN}All components stopped${NC}"
            exit 0
        }

        trap cleanup SIGINT SIGTERM

        # Run S-IDS in foreground
        ./sids -i "$INTERFACE"
        ;;

    3)
        # Feature extractor only
        echo -e "${GREEN}Starting Feature Extractor only...${NC}"
        echo -e "${YELLOW}Command: $BUILD_DIR/nids -i $INTERFACE --extract-features${NC}"
        echo ""
        "$BUILD_DIR/nids" -i "$INTERFACE" --extract-features
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}[8/8] Complete${NC}"
