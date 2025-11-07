# Complete ELK Stack Setup for Hybrid IDS

**Complete guide to get everything working with ELK Stack dashboard**

---

## Step 1: Install Docker Desktop

### Download and Install

1. **Download Docker Desktop for Windows**:
   - Go to: https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - Run the installer

2. **During Installation**:
   - ✅ Use WSL 2 instead of Hyper-V (recommended)
   - ✅ Add shortcut to desktop

3. **After Installation**:
   - Restart your computer
   - Start Docker Desktop
   - Wait for "Docker Desktop is running" message

### Enable WSL 2 (If not already enabled)

```powershell
# Run PowerShell as Administrator
wsl --install
wsl --set-default-version 2

# Restart computer
```

### Verify Docker Installation

```powershell
docker --version
docker-compose --version

# Should show:
# Docker version 24.0.0 or higher
# Docker Compose version v2.20.0 or higher
```

---

## Step 2: Configure Docker Resources

1. Open Docker Desktop
2. Click Settings (⚙️ icon)
3. Go to **Resources**
4. Set:
   - **CPUs**: 4 (minimum 2)
   - **Memory**: 8 GB (minimum 6 GB)
   - **Swap**: 2 GB
   - **Disk image size**: 60 GB
5. Click **Apply & Restart**

---

## Step 3: Fix Elasticsearch Memory Issue

### For WSL 2:

```powershell
# Run in PowerShell
wsl -d docker-desktop
sysctl -w vm.max_map_count=262144
exit
```

### Make it Permanent:

Create file: `C:\Users\<YourUsername>\.wslconfig`

```ini
[wsl2]
memory=8GB
processors=4
kernelCommandLine = sysctl.vm.max_map_count=262144
```

---

## Step 4: Update ELK Configuration for Windows

Let me update the docker-compose.yml to work better with Windows and include proper log mounting.
