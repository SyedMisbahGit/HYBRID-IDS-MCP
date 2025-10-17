#!/bin/bash

# ============================================
# Build script for S-IDS
# ============================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Building S-IDS${NC}"
echo -e "${GREEN}========================================${NC}"

# Create build directory
if [ ! -d "build" ]; then
    echo -e "${YELLOW}[INFO] Creating build directory...${NC}"
    mkdir build
fi

cd build

# Configure with CMake
echo -e "${YELLOW}[INFO] Configuring with CMake...${NC}"
cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF

# Build
echo -e "${YELLOW}[INFO] Building S-IDS...${NC}"
make -j$(nproc) sids

# Check if build succeeded
if [ -f "sids" ]; then
    echo -e "${GREEN}[SUCCESS] S-IDS built successfully!${NC}"
    echo -e "${GREEN}Executable: $(pwd)/sids${NC}"

    # Show usage
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./build/sids -r <pcap_file>    # Analyze PCAP file"
    echo "  sudo ./build/sids -i <interface>  # Live capture (requires sudo)"
    echo ""
else
    echo -e "${RED}[ERROR] Build failed${NC}"
    exit 1
fi
