

# Building C++ NIDS on Windows

Complete guide to compile the high-performance C++ NIDS component on Windows.

---

## Prerequisites

### 1. Install Visual Studio Build Tools

**Option A: Visual Studio 2022 Community (Recommended)**
```powershell
# Download from: https://visualstudio.microsoft.com/downloads/
# During installation, select:
# - Desktop development with C++
# - Windows 10/11 SDK
# - CMake tools for Windows
```

**Option B: Build Tools Only**
```powershell
# Download from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
# Select: C++ build tools
```

**Option C: Using Chocolatey**
```powershell
# Run PowerShell as Administrator
choco install visualstudio2022buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools"
```

### 2. Install CMake

**Option A: Direct Download**
```powershell
# Download from: https://cmake.org/download/
# Choose: Windows x64 Installer
# During installation: Add CMake to system PATH
```

**Option B: Using Chocolatey**
```powershell
choco install cmake
```

**Verify Installation**:
```powershell
cmake --version
# Should show: cmake version 3.20 or higher
```

### 3. Install Npcap (Windows Packet Capture)

```powershell
# Download from: https://npcap.com/
# During installation:
# ✓ Check "Install Npcap in WinPcap API-compatible Mode"
# ✓ Check "Support raw 802.11 traffic"
```

### 4. Install vcpkg (Package Manager)

```powershell
# Clone vcpkg
cd C:\
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg

# Bootstrap vcpkg
.\bootstrap-vcpkg.bat

# Add to PATH (optional)
$env:PATH += ";C:\vcpkg"
```

---

## Install Dependencies

### Using vcpkg

```powershell
cd C:\vcpkg

# Install required libraries
.\vcpkg install nlohmann-json:x64-windows
.\vcpkg install zeromq:x64-windows
.\vcpkg install cppzmq:x64-windows
.\vcpkg install spdlog:x64-windows
.\vcpkg install boost-asio:x64-windows

# Integrate with Visual Studio
.\vcpkg integrate install
```

---

## Build Process

### Step 1: Navigate to Project

```powershell
cd C:\Users\zsyed\Hybrid-IDS-MCP
```

### Step 2: Create Build Directory

```powershell
mkdir build
cd build
```

### Step 3: Configure with CMake

**Using Visual Studio 2022**:
```powershell
cmake .. -G "Visual Studio 17 2022" -A x64 `
  -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake `
  -DCMAKE_BUILD_TYPE=Release
```

**Using Visual Studio 2019**:
```powershell
cmake .. -G "Visual Studio 16 2019" -A x64 `
  -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake `
  -DCMAKE_BUILD_TYPE=Release
```

**Using Ninja (Faster)**:
```powershell
cmake .. -G "Ninja" `
  -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake `
  -DCMAKE_BUILD_TYPE=Release `
  -DCMAKE_C_COMPILER=cl `
  -DCMAKE_CXX_COMPILER=cl
```

### Step 4: Build

```powershell
# Using Visual Studio
cmake --build . --config Release -j 8

# Or using MSBuild directly
msbuild HybridIDS.sln /p:Configuration=Release /m
```

### Step 5: Verify Build

```powershell
# Check if executables were created
dir Release\*.exe

# Should see:
# - sids.exe (Signature IDS)
# - nids.exe (Complete NIDS)
```

---

## Running C++ NIDS

### Test with PCAP File

```powershell
# Navigate to project root
cd C:\Users\zsyed\Hybrid-IDS-MCP

# Run S-IDS
.\build\Release\sids.exe -r test.pcap

# Run complete NIDS
.\build\Release\nids.exe -r test.pcap --extract-features
```

### Live Capture (Requires Administrator)

```powershell
# Run PowerShell as Administrator

# List available interfaces
.\build\Release\nids.exe --list-interfaces

# Capture on specific interface
.\build\Release\nids.exe -i "Ethernet" --extract-features
```

---

## Troubleshooting

### CMake Cannot Find vcpkg

```powershell
# Set environment variable
$env:VCPKG_ROOT = "C:\vcpkg"

# Or specify in cmake command
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
```

### "pcap.h not found"

```powershell
# Install Npcap SDK
# Download from: https://npcap.com/#download
# Extract to: C:\npcap-sdk

# Add to CMake command
cmake .. -DPCAP_INCLUDE_DIR="C:/npcap-sdk/Include" `
         -DPCAP_LIBRARY="C:/npcap-sdk/Lib/x64/wpcap.lib"
```

### "Cannot open include file: 'zmq.h'"

```powershell
# Reinstall ZeroMQ via vcpkg
cd C:\vcpkg
.\vcpkg remove zeromq:x64-windows
.\vcpkg install zeromq:x64-windows cppzmq:x64-windows
```

### Build Fails with "MSB8020: The build tools for v143 cannot be found"

```powershell
# Install correct Visual Studio version
# Or specify toolset
cmake .. -G "Visual Studio 17 2022" -T v142
```

### "LINK : fatal error LNK1104: cannot open file 'wpcap.lib'"

```powershell
# Copy Npcap libraries
copy "C:\Windows\System32\Npcap\wpcap.lib" "C:\Program Files (x86)\Windows Kits\10\Lib\*\um\x64\"
copy "C:\Windows\System32\Npcap\Packet.lib" "C:\Program Files (x86)\Windows Kits\10\Lib\*\um\x64\"
```

---

## Alternative: MinGW Build

### Install MinGW-w64

```powershell
# Using Chocolatey
choco install mingw

# Or download from: https://www.mingw-w64.org/
```

### Build with MinGW

```powershell
cd C:\Users\zsyed\Hybrid-IDS-MCP
mkdir build-mingw
cd build-mingw

# Configure
cmake .. -G "MinGW Makefiles" `
  -DCMAKE_BUILD_TYPE=Release `
  -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake

# Build
mingw32-make -j8
```

---

## Performance Optimization

### Release Build with Optimizations

```powershell
cmake .. -DCMAKE_BUILD_TYPE=Release `
  -DCMAKE_CXX_FLAGS="/O2 /GL /arch:AVX2" `
  -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake

cmake --build . --config Release
```

### Profile-Guided Optimization (PGO)

```powershell
# Step 1: Build with instrumentation
cmake .. -DCMAKE_CXX_FLAGS="/GL /LTCG:PGInstrument"
cmake --build . --config Release

# Step 2: Run with representative workload
.\Release\nids.exe -r test.pcap

# Step 3: Rebuild with optimization
cmake .. -DCMAKE_CXX_FLAGS="/GL /LTCG:PGOptimize"
cmake --build . --config Release
```

---

## Integration with Python Components

### Enable ZeroMQ Communication

The C++ NIDS will automatically publish to ZeroMQ port 5556 when built with ZeroMQ support.

```powershell
# Start Alert Manager (Python)
python src\integration\alert_manager.py

# Start C++ NIDS (separate terminal)
.\build\Release\nids.exe -i "Ethernet" --zmq-publish
```

---

## Benchmarking

### Test Packet Processing Speed

```powershell
# Create large PCAP file or use existing
.\build\Release\nids.exe -r large_capture.pcap --benchmark

# Expected performance:
# - Signature matching: 50,000+ pps
# - Feature extraction: 20,000+ pps
# - Full pipeline: 10,000+ pps
```

---

## Deployment

### Copy Required DLLs

```powershell
# Copy to build directory
copy C:\vcpkg\installed\x64-windows\bin\*.dll .\build\Release\
copy C:\Windows\System32\Npcap\wpcap.dll .\build\Release\
copy C:\Windows\System32\Npcap\Packet.dll .\build\Release\
```

### Create Standalone Package

```powershell
# Create distribution folder
mkdir dist
copy .\build\Release\*.exe dist\
copy .\build\Release\*.dll dist\
copy config\nids\* dist\config\

# Zip for distribution
Compress-Archive -Path dist\* -DestinationPath hybrid-ids-nids-windows.zip
```

---

## Comparison: C++ vs Python NIDS

| Feature | C++ NIDS | Python NIDS |
|---------|----------|-------------|
| **Performance** | 50K+ pps | 5-10K pps |
| **Memory** | 20-50 MB | 50-200 MB |
| **Build Required** | Yes | No |
| **Dependencies** | Complex | Simple |
| **Maintenance** | Harder | Easier |
| **Use Case** | Production | Development |

---

## Quick Reference

### Full Build Command (Copy-Paste)

```powershell
# One-liner for quick build
cd C:\Users\zsyed\Hybrid-IDS-MCP && `
mkdir -Force build && cd build && `
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake && `
cmake --build . --config Release -j 8
```

### Test Command

```powershell
.\build\Release\sids.exe -r test.pcap
```

---

## Success Indicators

✅ CMake configuration completes without errors
✅ Build completes with 0 errors
✅ `sids.exe` and `nids.exe` created in `build/Release/`
✅ Test PCAP file processes successfully
✅ Alerts generated in console output
✅ No missing DLL errors when running

---

## Next Steps After Build

1. **Test with PCAP files**
   ```powershell
   .\build\Release\nids.exe -r test.pcap
   ```

2. **Integrate with Python components**
   ```powershell
   python src\integration\integration_controller.py --use-cpp-nids
   ```

3. **Benchmark performance**
   ```powershell
   .\build\Release\nids.exe -r large.pcap --benchmark
   ```

4. **Deploy to production**
   - Copy executables and DLLs
   - Configure as Windows Service
   - Set up monitoring

---

**Estimated Build Time**: 10-30 minutes (depending on download speeds)
**Difficulty**: Medium
**Result**: High-performance C++ NIDS (10x faster than Python)

---

**Last Updated**: November 1, 2025
**Tested On**: Windows 11, Visual Studio 2022
