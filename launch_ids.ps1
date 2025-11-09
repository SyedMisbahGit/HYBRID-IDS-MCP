# Hybrid IDS Modern Launcher
# Single command to launch all components with visual feedback

# Add required .NET assembly
Add-Type -AssemblyName System.Windows.Forms

# Configuration
$config = @{
    NidsPort = 8000
    HidsPort = 8001
    WebPort = 3000
    DashboardTitle = "Hybrid IDS Dashboard"
}

# Function to show notification
function Show-Notification {
    param($Title, $Message)
    [System.Windows.Forms.MessageBox]::Show($Message, $Title, [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
}

# Check and kill existing processes
Write-Host "[INFO] Stopping any running instances..."
Get-Process | Where-Object { $_.ProcessName -match "python|node" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Create config directory if it doesn't exist
$configDir = "config"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir | Out-Null
}

# Create N-IDS config
$nidsConfig = @{
    interface = "any"
    pcap_file = "test.pcap"
    zmq_enabled = $true
    zmq_port = 5556
    rules_dir = "rules"
    alert_log = "logs/nids_alerts.log"
}
$nidsConfigPath = "$configDir/nids_config.json"
$nidsConfig | ConvertTo-Json | Out-File -FilePath $nidsConfigPath -Encoding utf8

# Start N-IDS
Write-Host "[N-IDS] Starting Network IDS..."
try {
    $nids = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "src/nids_python/nids_main.py -r test.pcap --rules-dir rules"
    Start-Sleep -Seconds 2
    Write-Host "[N-IDS] Started with test traffic" -ForegroundColor Green
    Show-Notification -Title "Hybrid IDS" -Message "N-IDS started with test traffic"
} catch {
    Write-Host "[ERROR] Failed to start N-IDS: $_" -ForegroundColor Red
    exit 1
}

# Create H-IDS config
$hidsConfig = @"
monitor_directories:
  - "C:\\Windows\\System32\\drivers\\etc"
log_paths:
  - "C:\\Windows\\System32\\Logs"
baseline_file: "$configDir/hids_baseline.json"
zmq_enabled: true
zmq_port: 5557
"@

$hidsConfigPath = "$configDir/hids_config.yaml"
$hidsConfig | Out-File -FilePath $hidsConfigPath -Encoding utf8

# Start H-IDS
Write-Host "[H-IDS] Starting Host IDS..."
try {
    $hids = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "src/hids/hids_main.py --config $hidsConfigPath"
    Start-Sleep -Seconds 2
    Write-Host "[H-IDS] Started with basic monitoring" -ForegroundColor Green
    Show-Notification -Title "Hybrid IDS" -Message "H-IDS started with basic monitoring"
} catch {
    Write-Host "[ERROR] Failed to start H-IDS: $_" -ForegroundColor Red
    exit 1
}

# Start Dashboard
Write-Host "[DASH] Starting Dashboard..."
try {
    $dashboard = Start-Process -NoNewWindow -PassThru -WorkingDirectory "dashboard/frontend" -FilePath "npm" -ArgumentList "start"
    Start-Sleep -Seconds 5  # Give npm some time to start
    Write-Host "[DASH] Dashboard starting on port 3000" -ForegroundColor Green
    Start-Process "http://localhost:3000"
} catch {
    Write-Host "[ERROR] Failed to start Dashboard: $_" -ForegroundColor Red
    Write-Host "[INFO] Trying alternative method to start dashboard..."
    try {
        Set-Location "dashboard/frontend"
        $dashboard = Start-Process -NoNewWindow -PassThru -FilePath "cmd.exe" -ArgumentList "/c npm start"
        Start-Sleep -Seconds 5
        Write-Host "[DASH] Dashboard started using alternative method" -ForegroundColor Green
        Start-Process "http://localhost:3000"
    } catch {
        Write-Host "[CRITICAL] Failed to start dashboard with all methods" -ForegroundColor Red
        exit 1
    }
}
Write-Host "[INFO] Dashboard URL: http://localhost:$($config.WebPort)" -ForegroundColor Cyan

# Cleanup on exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-Host "[INFO] Stopping all services..."
    Get-Process | Where-Object { $_.Id -in ($nids.Id, $hids.Id, $dashboard.Id) } | Stop-Process -Force -ErrorAction SilentlyContinue
}
