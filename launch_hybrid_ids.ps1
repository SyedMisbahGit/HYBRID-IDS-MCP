# Launch Hybrid IDS - All-in-One Launcher
# This script starts NIDS, HIDS, and a simple web dashboard

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to check if a process is running
function Test-ProcessRunning($name) {
    return (Get-Process | Where-Object { $_.ProcessName -like "*$name*" }).Count -gt 0
}

# Function to start a process in a new window
function Start-ProcessInWindow {
    param (
        [string]$Title,
        [string]$Command,
        [string]$WorkingDir = $PSScriptRoot
    )
    
    $ps = New-Object System.Diagnostics.Process
    $ps.StartInfo.FileName = "powershell.exe"
    $ps.StartInfo.Arguments = "-NoExit -Command `"cd '$WorkingDir'; $Command`""
    $ps.StartInfo.WorkingDirectory = $WorkingDir
    $ps.StartInfo.WindowTitle = $Title
    $ps.Start() | Out-Null
    return $ps
}

# Clear screen and show banner
Clear-Host
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Hybrid IDS - All-in-One Launcher" -ForegroundColor Cyan
Write-Host "  Starting NIDS, HIDS, and Web Dashboard" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start NIDS
Write-Host "[1/3] Starting NIDS (Network IDS)..." -ForegroundColor Yellow
$nids = Start-ProcessInWindow -Title "Hybrid IDS - NIDS" -Command "python src/nids_python/nids_main.py -r test.pcap"
Start-Sleep -Seconds 2

# Start HIDS
Write-Host "[2/3] Starting HIDS (Host IDS)..." -ForegroundColor Yellow
$hids = Start-ProcessInWindow -Title "Hybrid IDS - HIDS" -Command "python src/hids/hids_main.py"
Start-Sleep -Seconds 2

# Start Web Dashboard
Write-Host "[3/3] Starting Web Dashboard..." -ForegroundColor Yellow
$dashboard = Start-ProcessInWindow -Title "Hybrid IDS - Dashboard" -Command "python web_dashboard.py"

# Open dashboard in default browser
Start-Sleep -Seconds 3
Start-Process "http://localhost:5000"

# Show status
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Hybrid IDS System Started Successfully!" -ForegroundColor Green
Write-Host "  - NIDS: Running in a new terminal" -ForegroundColor Green
Write-Host "  - HIDS: Running in a new terminal" -ForegroundColor Green
Write-Host "  - Dashboard: Opening in your default browser" -ForegroundColor Green
Write-Host ""
Write-Host "  Access the dashboard at: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press Ctrl+C in this window to stop all components" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Green

# Wait for user to press Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    # Cleanup on exit
    Write-Host ""
    Write-Host "Stopping Hybrid IDS components..." -ForegroundColor Yellow
    
    if ($nids -and !$nids.HasExited) { $nids.Kill() }
    if ($hids -and !$hids.HasExited) { $hids.Kill() }
    if ($dashboard -and !$dashboard.HasExited) { $dashboard.Kill() }
    
    Write-Host "All components stopped." -ForegroundColor Green
}
