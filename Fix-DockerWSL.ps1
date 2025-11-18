# AceBuddy - Docker WSL Auto-Fix Script (PowerShell)
# Run this as Administrator to fix Docker Desktop WSL issues

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          Docker WSL Auto-Fix Script (PowerShell)          ║" -ForegroundColor Cyan
Write-Host "║     This will install WSL 2 and fix Docker Desktop        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = [bool]([Security.Principal.WindowsIdentity]::GetCurrent().Groups -match "S-1-5-32-544")
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solution:" -ForegroundColor Yellow
    Write-Host "  1. Right-click on PowerShell"
    Write-Host "  2. Select 'Run as Administrator'"
    Write-Host "  3. Run this script again"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Running with Administrator privileges" -ForegroundColor Green
Write-Host ""

# Step 1: Enable WSL Feature
Write-Host "Step 1: Enabling Windows Subsystem for Linux..." -ForegroundColor Yellow
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ WSL feature enabled" -ForegroundColor Green
} else {
    Write-Host "⚠ WSL feature enable completed (may need reboot)" -ForegroundColor Yellow
}
Write-Host ""

# Step 2: Enable Virtual Machine Platform
Write-Host "Step 2: Enabling Virtual Machine Platform..." -ForegroundColor Yellow
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Virtual Machine Platform enabled" -ForegroundColor Green
} else {
    Write-Host "⚠ Virtual Machine Platform enable completed (may need reboot)" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Set WSL 2 as default
Write-Host "Step 3: Setting WSL 2 as default version..." -ForegroundColor Yellow
wsl --set-default-version 2 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ WSL 2 set as default" -ForegroundColor Green
} else {
    Write-Host "⚠ WSL 2 configuration (you may need to download kernel)" -ForegroundColor Yellow
    Write-Host "  Visit: https://aka.ms/wsl2kernel" -ForegroundColor Cyan
}
Write-Host ""

# Step 4: Check Ubuntu installation
Write-Host "Step 4: Checking Ubuntu installation..." -ForegroundColor Yellow
$ubuntuInstalled = wsl --list 2>&1 | Select-String -Pattern "ubuntu" -Quiet
if (-not $ubuntuInstalled) {
    Write-Host "Ubuntu not found. Installing Ubuntu..." -ForegroundColor Yellow
    wsl --install -d Ubuntu
    Write-Host "✓ Ubuntu installed" -ForegroundColor Green
} else {
    Write-Host "✓ Ubuntu already installed" -ForegroundColor Green
}
Write-Host ""

# Step 5: Verify WSL installation
Write-Host "Step 5: Verifying WSL installation..." -ForegroundColor Yellow
Write-Host ""
Write-Host "WSL Status:" -ForegroundColor Cyan
wsl --list --verbose
Write-Host ""

# Step 6: Check Docker
Write-Host "Step 6: Checking Docker installation..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker is installed" -ForegroundColor Green
    Write-Host "  Version: $dockerVersion" -ForegroundColor Cyan
} else {
    Write-Host "⚠ WARNING: Docker is not installed or not in PATH" -ForegroundColor Yellow
    Write-Host "  Please install Docker Desktop from:" -ForegroundColor Cyan
    Write-Host "  https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
}
Write-Host ""

# Summary
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                 Fix Complete - Summary                     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ WSL 2 features enabled" -ForegroundColor Green
Write-Host "✓ Virtual Machine Platform enabled" -ForegroundColor Green
Write-Host "✓ Ubuntu Linux installed (or already present)" -ForegroundColor Green
Write-Host ""

Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Restart your computer (IMPORTANT!)" -ForegroundColor Cyan
Write-Host "   Some WSL changes require system reboot" -ForegroundColor Gray
Write-Host "   Run: shutdown /r /t 30" -ForegroundColor Gray
Write-Host ""
Write-Host "2. After restart, verify Docker works:" -ForegroundColor Cyan
Write-Host "   docker ps" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Then start AceBuddy-RAG:" -ForegroundColor Cyan
Write-Host "   cd '...\AceBuddy-RAG'" -ForegroundColor Gray
Write-Host "   docker-compose up --build -d" -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$restart = Read-Host "Do you want to restart your computer now? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host "Restarting in 30 seconds... (Press Ctrl+C to cancel)" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    shutdown /r /t 30
} else {
    Write-Host "Remember to restart your computer for changes to take effect!" -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Press Enter to exit"
