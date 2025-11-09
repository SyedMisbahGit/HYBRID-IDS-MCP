# Start Hybrid IDS with Synthetic Data

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-Status {
    param (
        [string]$Message,
        [string]$Status = "INFO"
    )
    
    $time = Get-Date -Format "HH:mm:ss"
    $color = switch ($Status) {
        "INFO"    { "Cyan" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR"   { "Red" }
        default    { "White" }
    }
    
    Write-Host "[$time] [$Status] $Message" -ForegroundColor $color
}

# Function to check if a port is in use
function Test-PortInUse {
    param (
        [int]$Port
    )
    
    try {
        $tcpListener = [System.Net.Sockets.TcpListener]$Port
        $tcpListener.Start()
        $tcpListener.Stop()
        return $false
    } catch {
        return $true
    }
}

# Main script
Write-Status "Starting Hybrid IDS with Synthetic Data..."

# 1. Check if required ports are available
$portsToCheck = @(8000, 8001, 8002)  # Add more ports if needed
foreach ($port in $portsToCheck) {
    if (Test-PortInUse -Port $port) {
        Write-Status "Port $port is already in use. Please free the port and try again." -Status "ERROR"
        exit 1
    }
}

# 2. Generate synthetic network traffic
Write-Status "Generating synthetic network traffic..."
$pcapFile = "synthetic_traffic.pcap"
if (-not (Test-Path $pcapFile)) {
    python scripts/generate_test_traffic.py $pcapFile
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Failed to generate synthetic traffic" -Status "ERROR"
        exit 1
    }
    Write-Status "Synthetic traffic generated: $pcapFile" -Status "SUCCESS"
} else {
    Write-Status "Using existing synthetic traffic file: $pcapFile" -Status "INFO"
}

# 3. Create a synthetic config file
$configContent = @'
{
    "nids": {
        "interface": "any",
        "pcap_file": "synthetic_traffic.pcap",
        "zmq_pub_address": "tcp://127.0.0.1:5555",
        "zmq_sub_address": "tcp://127.0.0.1:5556",
        "use_synthetic": true
    },
    "hids": {
        "monitor_directories": ["synthetic_data/hids"],
        "log_paths": ["synthetic_data/logs"],
        "zmq_pub_address": "tcp://127.0.0.1:5557",
        "use_synthetic": true
    },
    "dashboard": {
        "host": "127.0.0.1",
        "port": 8000,
        "websocket_port": 8001
    }
}
'@

# Create necessary directories
New-Item -ItemType Directory -Force -Path "synthetic_data/hids", "synthetic_data/logs" | Out-Null

# Save config
$configFile = "synthetic_config.json"
$configContent | Out-File -FilePath $configFile -Encoding utf8
Write-Status "Created synthetic configuration: $configFile" -Status "SUCCESS"

# 4. Start N-IDS with synthetic data
Write-Status "Starting N-IDS with synthetic data..."
$nidsProcess = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "src/nids_python/nids_main.py --config $configFile"

# 5. Start H-IDS with synthetic monitoring
Write-Status "Starting H-IDS with synthetic monitoring..."
$hidsProcess = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "src/hids/hids_main.py --config $configFile"

# 6. Start the dashboard
Write-Status "Starting the dashboard..."
$dashboardProcess = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "dashboard/backend/main.py --config $configFile"

# 6. Open the dashboard in default browser
Start-Process "http://localhost:3000"

Write-Status "Hybrid IDS is now running with synthetic data!" -Status "SUCCESS"
Write-Status "N-IDS Process ID: $($nidsProcess.Id)" -Status "INFO"
Write-Status "H-IDS Process ID: $($hidsProcess.Id)" -Status "INFO"
Write-Status "Dashboard Process ID: $($dashboardProcess.Id)" -Status "INFO"
Write-Status "Access the dashboard at: http://localhost:3000" -Status "INFO"

# Wait for user input to stop the services
Write-Host "`nPress any key to stop all services..." -NoNewline
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop all processes
Write-Status "Stopping all services..."
Stop-Process -Id $nidsProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $hidsProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $dashboardProcess.Id -Force -ErrorAction SilentlyContinue

Write-Status "All services have been stopped." -Status "SUCCESS"
