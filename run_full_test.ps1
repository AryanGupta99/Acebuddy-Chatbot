#!/usr/bin/env powershell
# AceBuddy Smoke Test - Complete Startup Script

param(
    [int]$OllamaWaitSeconds = 10,
    [int]$DockerWaitSeconds = 120
)

Write-Host "`n========== AceBuddy RAG - Complete System Test ==========" -ForegroundColor Green
Write-Host ""

# Step 1: Verify Ollama is running
Write-Host "Step 1: Checking Ollama service..." -ForegroundColor Cyan
$ollama = Get-Process ollama -ErrorAction SilentlyContinue
if ($ollama) {
    Write-Host "✅ Ollama is running (PID: $($ollama.Id))" -ForegroundColor Green
} else {
    Write-Host "⏳ Starting Ollama service..." -ForegroundColor Yellow
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Write-Host "✅ Ollama started. Waiting ${OllamaWaitSeconds} seconds to be ready..." -ForegroundColor Green
    Start-Sleep -Seconds $OllamaWaitSeconds
}

# Step 2: Check if phi model exists
Write-Host "`nStep 2: Checking for phi model..." -ForegroundColor Cyan
$models = ollama list 2>$null
if ($models -match "phi") {
    Write-Host "✅ phi model is available" -ForegroundColor Green
} else {
    Write-Host "❌ phi model not found. Pulling it now..." -ForegroundColor Yellow
    ollama pull phi
}

# Step 3: Stop old services and start fresh
Write-Host "`nStep 3: Resetting Docker services..." -ForegroundColor Cyan
docker-compose down 2>&1 | Where-Object { $_ -match "Container|Network|removed" }
Write-Host "✅ Old services removed" -ForegroundColor Green

# Step 4: Start new services
Write-Host "`nStep 4: Starting Docker services..." -ForegroundColor Cyan
docker-compose up -d --build 2>&1 | Where-Object { $_ -match "Running|Container|Network|Created|Started" }
Write-Host "✅ Services started" -ForegroundColor Green

# Step 5: Run smoke test
Write-Host "`nStep 5: Running smoke test (timeout: ${DockerWaitSeconds}s)..." -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File .\test_chatbot_smoke.ps1 -MaxWaitSeconds $DockerWaitSeconds

Write-Host "`nTest execution complete!`n" -ForegroundColor Green
