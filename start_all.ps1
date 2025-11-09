# Start-All.ps1 - Single command to start the Hybrid IDS Dashboard

# Set the working directory to the project root
$projectRoot = $PSScriptRoot
Set-Location $projectRoot

# Function to check if a port is in use
function Test-PortInUse {
    param([int]$Port)
    $tcpConnections = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $tcpConnections
}

# Check if required ports are available
$portsInUse = @()
@(3000, 8000) | ForEach-Object {
    if (Test-PortInUse -Port $_) {
        $portsInUse += $_
    }
}

if ($portsInUse.Count -gt 0) {
    Write-Host "Error: The following ports are already in use: $($portsInUse -join ', ')" -ForegroundColor Red
    Write-Host "Please close any applications using these ports and try again." -ForegroundColor Yellow
    exit 1
}

# Start backend server in a new window
Write-Host "Starting backend server..." -ForegroundColor Cyan
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\dashboard\backend'; .\venv\Scripts\Activate; uvicorn main:app --reload --host 0.0.0.0 --port 8000" -PassThru

# Wait for backend to start
Write-Host "Waiting for backend to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Start frontend in a new window
Write-Host "Starting frontend development server..." -ForegroundColor Cyan
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\dashboard\frontend'; npm start" -PassThru

# Open browser after a short delay
Write-Host "Opening dashboard in default browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"

Write-Host "`nHybrid IDS Dashboard is now running!" -ForegroundColor Green
Write-Host "- Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "- Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "- API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan

# Keep the script running in the background
Write-Host "`nPress Ctrl+C to stop all services..." -ForegroundColor Yellow
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    # Cleanup on Ctrl+C
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "All services stopped." -ForegroundColor Green
}
