# Hybrid IDS Dashboard Launcher
Write-Host "Starting Hybrid IDS Dashboard..." -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Node.js is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Create and activate virtual environment
$venvPath = ".\dashboard\backend\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv $venvPath
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Host "Error: Could not activate Python virtual environment" -ForegroundColor Red
    exit 1
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
pip install --upgrade pip
pip install fastapi uvicorn python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv websockets pydantic python-socketio fastapi-socketio aiofiles psutil pandas numpy scikit-learn python-dateutil pyzmq

# Install and build frontend
$frontendPath = ".\dashboard\frontend"
if (Test-Path $frontendPath) {
    Set-Location $frontendPath
    
    # Install Node.js dependencies
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    npm install
    
    # Build the React app
    Write-Host "Building frontend..." -ForegroundColor Cyan
    npm run build
    
    Set-Location ../..
}

# Start the backend server
Write-Host "Starting backend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\dashboard\backend\venv\Scripts\Activate.ps1; uvicorn dashboard.backend.main:app --reload --host 0.0.0.0 --port 8000"

# Open the dashboard in the default browser
Start-Sleep -Seconds 5
Start-Process "http://localhost:8000"

Write-Host "`nDashboard is running!" -ForegroundColor Green
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Dashboard: http://localhost:8000" -ForegroundColor Cyan
