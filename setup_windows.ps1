# Beaky Windows Setup Script
# Run this in PowerShell as Administrator: .\setup_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Beaky Windows Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator. Some steps may fail." -ForegroundColor Yellow
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
}

# 1. Check Python
Write-Host "[1/6] Checking Python..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.(\d+)") {
        $minorVersion = [int]$Matches[1]
        if ($minorVersion -ge 9) {
            Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Python 3.9+ required, found $pythonVersion" -ForegroundColor Red
            Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
            exit 1
        }
    }
} catch {
    Write-Host "  ✗ Python not found" -ForegroundColor Red
    Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# 2. Check/Install Ollama
Write-Host "[2/6] Checking Ollama..." -ForegroundColor Green
$ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaPath) {
    Write-Host "  ✓ Ollama found at: $($ollamaPath.Source)" -ForegroundColor Green
} else {
    Write-Host "  ✗ Ollama not found" -ForegroundColor Red
    Write-Host "  Downloading Ollama..." -ForegroundColor Yellow

    $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
    Invoke-WebRequest -Uri "https://ollama.ai/download/OllamaSetup.exe" -OutFile $ollamaInstaller

    Write-Host "  Installing Ollama..." -ForegroundColor Yellow
    Start-Process -FilePath $ollamaInstaller -Wait

    Write-Host "  ✓ Ollama installed" -ForegroundColor Green
}

# 3. Pull Ollama models
Write-Host "[3/6] Pulling Ollama models..." -ForegroundColor Green
Write-Host "  This may take a while (downloading ~7GB)..." -ForegroundColor Yellow

$models = @("llama3.1:8b", "moondream")
foreach ($model in $models) {
    Write-Host "  Pulling $model..." -ForegroundColor Cyan
    ollama pull $model
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $model ready" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed to pull $model" -ForegroundColor Red
        exit 1
    }
}

# 4. Check/Install Piper TTS
Write-Host "[4/6] Checking Piper TTS..." -ForegroundColor Green
$piperPath = Get-Command piper -ErrorAction SilentlyContinue
if ($piperPath) {
    Write-Host "  ✓ Piper found at: $($piperPath.Source)" -ForegroundColor Green
} else {
    Write-Host "  Installing Piper TTS..." -ForegroundColor Yellow

    $piperDir = "C:\Program Files\piper"
    New-Item -ItemType Directory -Force -Path $piperDir | Out-Null

    # Download Piper
    $piperZip = "$env:TEMP\piper_windows_amd64.zip"
    Write-Host "  Downloading Piper..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://github.com/rhasspy/piper/releases/latest/download/piper_windows_amd64.zip" -OutFile $piperZip

    Write-Host "  Extracting..." -ForegroundColor Cyan
    Expand-Archive -Path $piperZip -DestinationPath $piperDir -Force

    # Download voice model
    Write-Host "  Downloading voice model..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -OutFile "$piperDir\en_US-lessac-medium.onnx"
    Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -OutFile "$piperDir\en_US-lessac-medium.onnx.json"

    # Add to PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$piperDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$currentPath;$piperDir", "User")
        $env:Path += ";$piperDir"
    }

    Write-Host "  ✓ Piper installed to $piperDir" -ForegroundColor Green
    Write-Host "  Note: You may need to restart PowerShell for PATH changes to take effect" -ForegroundColor Yellow
}

# 5. Install Python dependencies
Write-Host "[5/6] Installing Python dependencies..." -ForegroundColor Green
Write-Host "  This may take a few minutes..." -ForegroundColor Yellow

pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Python packages installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to install some packages" -ForegroundColor Red
    Write-Host "  Try running: pip install -r requirements.txt" -ForegroundColor Yellow
}

# 6. Verify setup
Write-Host "[6/6] Verifying setup..." -ForegroundColor Green
python verify_setup.py

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run Beaky:" -ForegroundColor Green
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""
Write-Host "Press ESC to exit Beaky when running." -ForegroundColor Yellow
Write-Host ""
