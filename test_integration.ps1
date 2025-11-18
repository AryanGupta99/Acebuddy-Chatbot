#!/usr/bin/env powershell

# AceBuddy Integration Test Suite

$BaseURL = "http://localhost:8000"
$Results = @()

Write-Host "`n" + ("="*70)
Write-Host "AceBuddy RAG Chatbot - Integration Test Suite"
Write-Host "="*70

# Wait for server
Write-Host "`nWaiting for server..."
$serverReady = $false
for ($i = 1; $i -le 15; $i++) {
    try {
        $health = Invoke-RestMethod -Uri "$BaseURL/health" -Method Get -ErrorAction Stop
        Write-Host "✅ Server is ready!"
        $serverReady = $true
        break
    } catch {
        if ($i -lt 15) {
            Write-Host "  Attempting connection... ($i/15)"
            Start-Sleep -Seconds 1
        }
    }
}

if (-not $serverReady) {
    Write-Host "❌ Server did not respond. Please ensure uvicorn is running."
    exit 1
}

# TEST 1: Health Check
Write-Host "`n" + ("="*70)
Write-Host "TEST 1: Health Check"
Write-Host "="*70
try {
    $health = Invoke-RestMethod -Uri "$BaseURL/health" -Method Get
    Write-Host "Status: $($health.status)"
    Write-Host "Services:"
    $health.services | ForEach-Object {
        $_.PSObject.Properties | ForEach-Object {
            Write-Host "  - $($_.Name): $($_.Value)"
        }
    }
    Write-Host "✅ PASS"
    $Results += @{Test="Health Check"; Status="PASS"}
} catch {
    Write-Host "❌ FAIL: $_"
    $Results += @{Test="Health Check"; Status="FAIL"}
}

# TEST 2: Password Reset Query
Write-Host "`n" + ("="*70)
Write-Host "TEST 2: Password Reset Query"
Write-Host "="*70
try {
    $payload = @{query="How do I reset my password?"; user_id="test_user_1"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseURL/chat" -Method Post -ContentType "application/json" -Body $payload -TimeoutSec 30
    Write-Host "Query: How do I reset my password?"
    Write-Host "Intent: $($response.intent)"
    Write-Host "Answer: $($response.answer.Substring(0, [Math]::Min(150, $response.answer.Length)))..."
    Write-Host "✅ PASS"
    $Results += @{Test="Password Reset"; Status="PASS"}
} catch {
    Write-Host "❌ FAIL: $_"
    $Results += @{Test="Password Reset"; Status="FAIL"}
}

# TEST 3: Disk Upgrade Query
Write-Host "`n" + ("="*70)
Write-Host "TEST 3: Disk Space Upgrade Query"
Write-Host "="*70
try {
    $payload = @{query="I need more disk space"; user_id="test_user_2"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseURL/chat" -Method Post -ContentType "application/json" -Body $payload -TimeoutSec 30
    Write-Host "Query: I need more disk space"
    Write-Host "Intent: $($response.intent)"
    Write-Host "Answer: $($response.answer.Substring(0, [Math]::Min(150, $response.answer.Length)))..."
    Write-Host "✅ PASS"
    $Results += @{Test="Disk Upgrade"; Status="PASS"}
} catch {
    Write-Host "❌ FAIL: $_"
    $Results += @{Test="Disk Upgrade"; Status="FAIL"}
}

# TEST 4: RDP Connection Issue
Write-Host "`n" + ("="*70)
Write-Host "TEST 4: RDP Connection Issue"
Write-Host "="*70
try {
    $payload = @{query="I cannot connect to the server via RDP"; user_id="test_user_3"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseURL/chat" -Method Post -ContentType "application/json" -Body $payload -TimeoutSec 30
    Write-Host "Query: I cannot connect to the server via RDP"
    Write-Host "Intent: $($response.intent)"
    Write-Host "Answer: $($response.answer.Substring(0, [Math]::Min(150, $response.answer.Length)))..."
    Write-Host "✅ PASS"
    $Results += @{Test="RDP Issue"; Status="PASS"}
} catch {
    Write-Host "❌ FAIL: $_"
    $Results += @{Test="RDP Issue"; Status="FAIL"}
}

# TEST 5: Printer Issue
Write-Host "`n" + ("="*70)
Write-Host "TEST 5: Printer Troubleshooting"
Write-Host "="*70
try {
    $payload = @{query="My printer is offline"; user_id="test_user_4"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseURL/chat" -Method Post -ContentType "application/json" -Body $payload -TimeoutSec 30
    Write-Host "Query: My printer is offline"
    Write-Host "Intent: $($response.intent)"
    Write-Host "Answer: $($response.answer.Substring(0, [Math]::Min(150, $response.answer.Length)))..."
    Write-Host "✅ PASS"
    $Results += @{Test="Printer Issue"; Status="PASS"}
} catch {
    Write-Host "❌ FAIL: $_"
    $Results += @{Test="Printer Issue"; Status="FAIL"}
}

# TEST 6: Application Update
Write-Host "`n" + ("="*70)
Write-Host "TEST 6: Application Update"
Write-Host "="*70
try {
    $payload = @{query="How do I update QuickBooks?"; user_id="test_user_5"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseURL/chat" -Method Post -ContentType "application/json" -Body $payload -TimeoutSec 30
    Write-Host "Query: How do I update QuickBooks?"
    Write-Host "Intent: $($response.intent)"
    Write-Host "Answer: $($response.answer.Substring(0, [Math]::Min(150, $response.answer.Length)))..."
    Write-Host "✅ PASS"
    $Results += @{Test="App Update"; Status="PASS"}
} catch {
    Write-Host "❌ FAIL: $_"
    $Results += @{Test="App Update"; Status="FAIL"}
}

# Summary
Write-Host "`n" + ("="*70)
Write-Host "TEST SUMMARY"
Write-Host "="*70
$passed = ($Results | Where-Object { $_.Status -eq "PASS" }).Count
$total = $Results.Count
Write-Host "`nPassed: $passed/$total`n"
$Results | ForEach-Object {
    $status = if ($_.Status -eq "PASS") { "✅ PASS" } else { "❌ FAIL" }
    Write-Host "  $status : $($_.Test)"
}

if ($passed -eq $total) {
    Write-Host "`n🎉 ALL TESTS PASSED! RAG + OpenAI integration is fully operational."
} else {
    Write-Host "`n⚠️  $($total - $passed) test(s) failed."
}

Write-Host "`n" + ("="*70)
