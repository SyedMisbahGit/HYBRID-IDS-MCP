#!/bin/bash

# ============================================
# Hybrid IDS - Development Environment Setup
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for system packages
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. This is not recommended for development."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        print_info "Detected OS: $OS $VERSION"
    else
        print_error "Cannot detect OS. /etc/os-release not found."
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    print_info "Installing system dependencies..."

    if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
        sudo apt-get update
        sudo apt-get install -y \
            build-essential \
            cmake \
            git \
            libpcap-dev \
            libboost-all-dev \
            nlohmann-json3-dev \
            libzmq3-dev \
            libspdlog-dev \
            libgtest-dev \
            python3.10 \
            python3-pip \
            python3-venv \
            valgrind \
            gdb \
            curl \
            wget

        print_success "System dependencies installed"

    elif [[ "$OS" == "kali" ]]; then
        sudo apt-get update
        sudo apt-get install -y \
            build-essential \
            cmake \
            git \
            libpcap-dev \
            libboost-all-dev \
            nlohmann-json3-dev \
            libzmq3-dev \
            libspdlog-dev \
            libgtest-dev \
            python3 \
            python3-pip \
            python3-venv \
            valgrind \
            gdb \
            curl \
            wget

        print_success "System dependencies installed"

    else
        print_error "Unsupported OS: $OS"
        print_info "Please install dependencies manually:"
        print_info "  - build-essential, cmake, git"
        print_info "  - libpcap-dev, libboost-all-dev"
        print_info "  - nlohmann-json3-dev, libzmq3-dev, libspdlog-dev"
        print_info "  - python3.10, python3-pip, python3-venv"
        exit 1
    fi
}

# Build C++ NIDS engine
build_nids() {
    print_info "Building NIDS engine..."

    if [ ! -d "build" ]; then
        mkdir build
    fi

    cd build
    cmake .. -DCMAKE_BUILD_TYPE=Debug
    make -j$(nproc)
    cd ..

    print_success "NIDS engine built successfully"
}

# Setup Python environment
setup_python() {
    print_info "Setting up Python environment..."

    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi

    deactivate
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."

    mkdir -p logs
    mkdir -p data/raw
    mkdir -p data/processed
    mkdir -p data/models
    mkdir -p config

    print_success "Directories created"
}

# Copy example configurations
setup_config() {
    print_info "Setting up configuration files..."

    if [ ! -f "config/nids.yaml" ]; then
        cp config/nids.yaml.example config/nids.yaml
        print_success "Created config/nids.yaml"
    else
        print_warning "config/nids.yaml already exists"
    fi

    if [ ! -f "config/ai_engine.yaml" ]; then
        cp config/ai_engine.yaml.example config/ai_engine.yaml
        print_success "Created config/ai_engine.yaml"
    else
        print_warning "config/ai_engine.yaml already exists"
    fi

    if [ ! -f "config/mcp.yaml" ]; then
        cp config/mcp.yaml.example config/mcp.yaml
        print_success "Created config/mcp.yaml"
    else
        print_warning "config/mcp.yaml already exists"
    fi

    print_info "Please review and customize the configuration files in config/"
}

# Download sample datasets (optional)
download_datasets() {
    print_info "Do you want to download sample datasets? (NSL-KDD, CICIDS2017)"
    print_warning "This will download ~500MB of data"
    read -p "Download datasets? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Downloading datasets..."

        cd data/raw

        # NSL-KDD
        if [ ! -f "KDDTrain+.txt" ]; then
            print_info "Downloading NSL-KDD dataset..."
            wget -q https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain%2B.txt
            wget -q https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest%2B.txt
            print_success "NSL-KDD downloaded"
        else
            print_warning "NSL-KDD already exists"
        fi

        cd ../..
        print_success "Datasets downloaded"
    else
        print_info "Skipping dataset download"
    fi
}

# Run tests
run_tests() {
    print_info "Running tests..."

    # C++ tests
    if [ -d "build" ]; then
        cd build
        if command -v ctest &> /dev/null; then
            ctest --output-on-failure
            print_success "C++ tests passed"
        else
            print_warning "ctest not found, skipping C++ tests"
        fi
        cd ..
    fi

    # Python tests
    source venv/bin/activate
    if [ -d "tests" ]; then
        if command -v pytest &> /dev/null; then
            pytest tests/unit/ -v
            print_success "Python tests passed"
        else
            print_warning "pytest not found, skipping Python tests"
        fi
    fi
    deactivate
}

# Print summary
print_summary() {
    echo ""
    echo "=========================================="
    echo "  Hybrid IDS Setup Complete!"
    echo "=========================================="
    echo ""
    print_success "Environment is ready for development"
    echo ""
    print_info "Next steps:"
    echo "  1. Review and customize configuration files in config/"
    echo "  2. Activate Python environment: source venv/bin/activate"
    echo "  3. Start development: see docs/ROADMAP.md"
    echo ""
    print_info "Quick start:"
    echo "  - Build NIDS: cd build && make"
    echo "  - Run NIDS: ./build/nids --config config/nids.yaml"
    echo "  - Start AI engine: python src/ai/inference/main.py"
    echo "  - Start MCP: python src/mcp/api/main.py"
    echo ""
    print_info "Documentation:"
    echo "  - Master Plan: MCP_MASTER_PLAN.md"
    echo "  - Architecture: docs/architecture/SYSTEM_ARCHITECTURE.md"
    echo "  - Roadmap: docs/ROADMAP.md"
    echo ""
}

# Main execution
main() {
    echo "=========================================="
    echo "  Hybrid IDS - Development Setup"
    echo "=========================================="
    echo ""

    check_root
    detect_os

    print_info "Starting setup process..."
    echo ""

    # Step 1: System dependencies
    read -p "Install system dependencies? (requires sudo) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_system_deps
    else
        print_warning "Skipping system dependencies"
    fi

    # Step 2: Create directories
    create_directories

    # Step 3: Setup configuration
    setup_config

    # Step 4: Build NIDS
    read -p "Build NIDS engine? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_nids
    else
        print_warning "Skipping NIDS build"
    fi

    # Step 5: Setup Python
    read -p "Setup Python environment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_python
    else
        print_warning "Skipping Python setup"
    fi

    # Step 6: Download datasets
    download_datasets

    # Step 7: Run tests
    read -p "Run tests? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    else
        print_warning "Skipping tests"
    fi

    # Print summary
    print_summary
}

# Run main function
main
