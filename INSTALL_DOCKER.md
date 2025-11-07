# Quick Docker Installation Guide

**Get Docker Desktop running in 15 minutes**

---

## Step 1: Download Docker Desktop

1. Go to: **https://www.docker.com/products/docker-desktop/**
2. Click **"Download for Windows"**
3. Save the installer: `Docker Desktop Installer.exe`

---

## Step 2: Install Docker Desktop

1. **Run** `Docker Desktop Installer.exe` as Administrator
2. **During installation**:
   - ✅ Check "Use WSL 2 instead of Hyper-V"
   - ✅ Check "Add shortcut to desktop"
3. **Click** "Ok" to proceed
4. **Wait** for installation (5-10 minutes)
5. **Restart** your computer when prompted

---

## Step 3: Enable WSL 2 (If Needed)

If Docker asks to enable WSL 2:

```powershell
# Open PowerShell as Administrator (Right-click → Run as Administrator)
wsl --install
wsl --set-default-version 2

# Restart computer
```

---

## Step 4: Start Docker Desktop

1. **Launch** Docker Desktop from Start Menu
2. **Accept** the service agreement
3. **Wait** for "Docker Desktop is running" message
4. **Look for** green whale icon in system tray (bottom right)

---

## Step 5: Verify Installation

```powershell
# Open PowerShell (normal, not admin)
docker --version
docker-compose --version

# Should show:
# Docker version 24.x.x
# Docker Compose version v2.x.x
```

**Test Docker**:
```powershell
docker run hello-world

# Should download and run a test container
```

---

## Step 6: Configure Docker Resources

1. **Open** Docker Desktop
2. **Click** Settings (⚙️ gear icon)
3. **Go to** Resources
4. **Set**:
   - CPUs: 4
   - Memory: 8 GB
   - Swap: 2 GB
5. **Click** "Apply & Restart"

---

## Step 7: Fix Elasticsearch Memory (Important!)

```powershell
# Run PowerShell as Administrator
wsl -d docker-desktop
sysctl -w vm.max_map_count=262144
exit
```

**Make it permanent**:

Create file: `C:\Users\<YourUsername>\.wslconfig`

```ini
[wsl2]
memory=8GB
processors=4
kernelCommandLine = sysctl.vm.max_map_count=262144
```

---

## ✅ You're Ready!

Docker is now installed and configured. 

**Next step**: Run the Hybrid IDS with ELK Stack

```powershell
cd C:\Users\zsyed\Hybrid-IDS-MCP
START_COMPLETE_SYSTEM_ELK.bat
```

---

## Troubleshooting

### "WSL 2 installation is incomplete"

```powershell
# Run as Administrator
wsl --install
wsl --update

# Restart computer
```

### "Hardware assisted virtualization is not enabled"

1. Restart computer
2. Enter BIOS (press F2, F10, or Del during boot)
3. Enable "Intel VT-x" or "AMD-V"
4. Save and exit

### "Docker Desktop requires Windows 10/11"

- You need Windows 10 version 2004+ or Windows 11
- Update Windows via Settings → Update & Security

### Docker Desktop won't start

1. Restart computer
2. Disable antivirus temporarily
3. Run Docker Desktop as Administrator
4. Check Windows Event Viewer for errors

---

## System Requirements

- **OS**: Windows 10 64-bit (version 2004+) or Windows 11
- **RAM**: 8GB minimum (16GB recommended)
- **CPU**: 64-bit processor with virtualization support
- **Disk**: 20GB free space
- **Virtualization**: Enabled in BIOS

---

**Estimated Time**: 15-20 minutes (including download)
