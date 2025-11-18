<#
.SYNOPSIS
Comprehensive smoke test for AceBuddy RAG chatbot with real KB and sample queries.

.DESCRIPTION
This script:
1. Starts Docker Compose services
2. Waits for services to be healthy
3. Tests /health endpoint
4. Calls /ingest to index KB files
5. Runs sample queries through /chat
6. Reports results and coverage

.USAGE
.\test_chatbot_smoke_fixed.ps1

.NOTES
- Requires Docker Compose to be installed
- Requires curl or PowerShell (uses Invoke-RestMethod)
- Takes 2-5 minutes total
#>

param(
    [string]$BaseUrl = "http://localhost:8000",
    [int]$MaxWaitSeconds = 60,
    [bool]$Verbose = $true
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $color = switch($Status) {
        "SUCCESS" { "Green" }
        "FAIL" { "Red" }
        "WARN" { "Yellow" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Status] $Message" -ForegroundColor $color
}

function Wait-ServiceHealthy {
    param(
        [string]$Url,
        [int]$MaxWait
    )
    
    Write-Status "Waiting for service to be healthy..."
    $startTime = Get-Date
    $healthy = $false
    
    while ($true) {
        try {
            $response = Invoke-RestMethod -Uri "$Url/health" -Method Get -TimeoutSec 5
            if ($response.status -eq "healthy") {
                $healthy = $true
                Write-Status "Service is healthy!" "SUCCESS"
                return $true
            }
        }
        catch {
            $elapsed = [int]((Get-Date) - $startTime).TotalSeconds
            if ($elapsed -gt $MaxWait) {
                Write-Status "Service did not become healthy within $MaxWait seconds" "FAIL"
                return $false
            }
            Write-Status "Waiting... ($elapsed`s/$MaxWait`s)" "WARN"
            Start-Sleep -Seconds 2
        }
    }
}

# Step 1: Start services
Write-Status "Step 1: Starting Docker Compose services..." "INFO"
try {
    $output = docker-compose up --build -d 2>&1
    Write-Status "Docker Compose started" "SUCCESS"
}
catch {
    Write-Status "Failed to start Docker Compose: $_" "FAIL"
    exit 1
}

# Step 2: Wait for service health
Write-Status "Step 2: Waiting for services to be ready..." "INFO"
$healthOk = Wait-ServiceHealthy $BaseUrl $MaxWaitSeconds
if (-not $healthOk) {
    Write-Status "Services failed to start" "FAIL"
    docker-compose logs --tail 20
    exit 1
}

# Step 3: Test /health endpoint
Write-Status "Step 3: Testing /health endpoint..." "INFO"
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    Write-Status "Health Status: $($health.status)" "SUCCESS"
    Write-Status "  - embedding_model: $($health.embedding_model)" "INFO"
    Write-Status "  - chroma_client: $($health.chroma_client)" "INFO"
    Write-Status "  - collection: $($health.collection)" "INFO"
}
catch {
    Write-Status "Health check failed: $_" "FAIL"
    exit 1
}

# Step 4: Ingest KB files
Write-Status "Step 4: Ingesting KB files..." "INFO"
try {
    $ingestResponse = Invoke-RestMethod -Uri "$BaseUrl/ingest" -Method Post
    Write-Status "Ingest Response: $($ingestResponse.message)" "SUCCESS"
}
catch {
    Write-Status "Ingestion failed: $_" "FAIL"
}

# Step 5: Load and run sample queries
Write-Status "Step 5: Running sample queries..." "INFO"
$sampleQueriesPath = "$PSScriptRoot/tests/sample_queries.json"

if (-not (Test-Path $sampleQueriesPath)) {
    Write-Status "Sample queries file not found at $sampleQueriesPath" "WARN"
}
else {
    try {
        $queriesJson = Get-Content $sampleQueriesPath -Raw | ConvertFrom-Json
        $queries = $queriesJson.sample_queries
        
        Write-Status "Found $($queries.Count) sample queries" "SUCCESS"
        
        $successCount = 0
        $failureCount = 0
        $contextCount = 0
        
        # Test first 10 queries for speed
        $queriesToTest = @($queries | Select-Object -First 10)
        
        Write-Status "Testing first $($queriesToTest.Count) queries..." "INFO"
        
        $index = 0
        foreach ($q in $queriesToTest) {
            $index++
            $query = $q.query
            $expectedIntent = $q.expected_intent
            
            try {
                $body = @{
                    query = $query
                    user_id = "smoke_test_user"
                } | ConvertTo-Json
                
                $response = Invoke-RestMethod -Uri "$BaseUrl/chat" `
                    -Method Post `
                    -Body $body `
                    -ContentType "application/json" `
                    -TimeoutSec 10
                
                $hasContext = $response.context -and $response.context.Count -gt 0
                if ($hasContext) {
                    $contextCount++
                    $status = "SUCCESS"
                }
                else {
                    $status = "WARN"
                }
                
                $successCount++
                Write-Status "[$index/10] Query: '$query' - Intent: $expectedIntent - Context: $hasContext" $status
                
            }
            catch {
                $failureCount++
                Write-Status "[$index/10] Query failed: '$query' - Error: $_" "FAIL"
            }
            
            Start-Sleep -Milliseconds 500
        }
        
        # Step 6: Summary report
        Write-Status "" "INFO"
        Write-Status "=== SMOKE TEST SUMMARY ===" "INFO"
        Write-Status "Queries Tested: $($queriesToTest.Count)" "INFO"
        Write-Status "Successful: $successCount" "SUCCESS"
        Write-Status "Failed: $failureCount" $(if ($failureCount -eq 0) { "SUCCESS" } else { "FAIL" })
        Write-Status "With Context: $contextCount" "SUCCESS"
        
        if ($successCount -gt 0) {
            $coverage = [math]::Round(($contextCount / $successCount) * 100)
            Write-Status "Context Coverage: $coverage%" $(if ($coverage -ge 80) { "SUCCESS" } else { "WARN" })
        }
        
        # Final status
        Write-Status "" "INFO"
        if ($successCount -ge 8 -and $contextCount -ge 6) {
            Write-Status "PASS - System ready for testing!" "SUCCESS"
            Write-Status "Next steps:" "INFO"
            Write-Status "1. Run full test suite with all 47 sample queries" "INFO"
            Write-Status "2. Prepare production KB with domain expertise" "INFO"
            Write-Status "3. Run comprehensive evaluation with real users" "INFO"
        }
        else {
            Write-Status "WARNING - Some issues detected" "WARN"
            Write-Status "Please check:" "INFO"
            Write-Status "1. Are all KB files ingested properly?" "INFO"
            Write-Status "2. Check Chroma container logs: docker logs acebuddy-chroma" "INFO"
            Write-Status "3. Check API logs: docker logs acebuddy-api" "INFO"
        }
        
    }
    catch {
        Write-Status "Error processing sample queries: $_" "FAIL"
    }
}

Write-Status "" "INFO"
Write-Status "Smoke test complete! Services still running." "SUCCESS"
Write-Status "Stop services with: docker-compose down" "INFO"
