#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete RAG Pipeline Runner
    
.DESCRIPTION
    Executes the full data-to-LLM pipeline:
    1. Data Preparation (cleaning, PII redaction)
    2. Vector DB Ingestion (Chroma)
    3. LLM Testing (Ollama responses)
    
.EXAMPLE
    .\run_complete_pipeline.ps1
    .\run_complete_pipeline.ps1 -SkipApiTest
#>

param(
    [switch]$SkipApiTest = $false,
    [string]$BaseDir = (Get-Location).Path
)

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "╔$("="*70)╗" -ForegroundColor Cyan
    Write-Host "║$(" "*((70-$Text.Length)/2))$Text$(" "*((70-$Text.Length+1)/2))║" -ForegroundColor Cyan
    Write-Host "╚$("="*70)╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "⚠️  $Text" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️  $Text" -ForegroundColor Cyan
}

# Main script
try {
    Write-Header "AceBuddy RAG: Complete Pipeline"
    
    # Step 1: Verify directories and files
    Write-Info "Step 1: Verifying setup..."
    
    $requiredDirs = @(
        "data",
        "data/kb",
        "scripts"
    )
    
    $requiredFiles = @(
        "scripts/data_preparation.py",
        "scripts/rag_ingestion.py",
        "scripts/full_pipeline.py"
    )
    
    $allExist = $true
    foreach ($dir in $requiredDirs) {
        $dirPath = Join-Path $BaseDir $dir
        if (-not (Test-Path $dirPath)) {
            Write-Error-Custom "Missing directory: $dirPath"
            $allExist = $false
        }
    }
    
    foreach ($file in $requiredFiles) {
        $filePath = Join-Path $BaseDir $file
        if (-not (Test-Path $filePath)) {
            Write-Error-Custom "Missing file: $filePath"
            $allExist = $false
        }
    }
    
    if (-not $allExist) {
        throw "Setup verification failed"
    }
    
    Write-Success "Setup verified"
    
    # Step 2: Check Python availability
    Write-Info "Step 2: Checking Python..."
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
        if ($null -eq $pythonCmd) {
            throw "Python not found in PATH"
        }
    }
    
    $pythonVersion = & python --version 2>&1
    Write-Success "Python found: $pythonVersion"
    
    # Step 3: Check required packages
    Write-Info "Step 3: Checking Python packages..."
    try {
        & python -c "import requests; import chromadb; import sentence_transformers" 2>&1 | Out-Null
        Write-Success "All required packages available"
    }
    catch {
        Write-Warning-Custom "Some packages might be missing. Installation may be needed."
        Write-Info "Run: pip install requests chromadb sentence-transformers"
    }
    
    # Step 4: Run the full pipeline
    Write-Header "Running Full RAG Pipeline"
    
    $pipelineScript = Join-Path $BaseDir "scripts/full_pipeline.py"
    
    $pipelineArgs = @($pipelineScript)
    if ($SkipApiTest) {
        $pipelineArgs += "--skip-api-test"
    }
    $pipelineArgs += "--base-dir"
    $pipelineArgs += $BaseDir
    
    Write-Info "Executing: python $(Join-Path 'scripts' 'full_pipeline.py')"
    Write-Info "Base directory: $BaseDir"
    Write-Info ""
    
    & python @pipelineArgs
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Header "✅ PIPELINE COMPLETE ✅"
        Write-Success "All steps completed successfully!"
        Write-Info ""
        Write-Host @"
Next Steps:
1. Verify cleaned data in: data/prepared/
   - documents_cleaned.json (cleaned documents)
   - chunks_for_rag.json (RAG-ready chunks)
   - preparation_report.json (quality metrics)

2. Check Chroma ingestion:
   - Vector DB should contain 100+ embeddings
   - Collection: 'acebuddy_kb'

3. Test RAG System:
   curl -X POST http://localhost:8000/chat `
     -H "Content-Type: application/json" `
     -d '{\"query\": \"How do I reset my password?\", \"user_id\": \"test\"}'

4. Monitor logs:
   - Check data/prepared/preparation_report.json for data quality metrics
   - Review API responses for LLM output quality

Your RAG system is now:
✅ Data cleaned (PII redacted, duplicates removed)
✅ Chunks validated and scored
✅ Indexed in vector database
✅ Connected to Ollama LLM
✅ Ready for production use!
"@ -ForegroundColor Green
    }
    else {
        Write-Error-Custom "Pipeline failed with exit code: $exitCode"
        Write-Host ""
        Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
        Write-Host "1. Ensure Docker containers are running: docker-compose ps" -ForegroundColor Yellow
        Write-Host "2. Check API health: curl http://localhost:8000/health" -ForegroundColor Yellow
        Write-Host "3. Check Chroma: curl http://localhost:8001/api/v1/heartbeat" -ForegroundColor Yellow
        Write-Host "4. Check Ollama: curl http://localhost:11434/api/tags" -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Error-Custom "Fatal error: $_"
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check that you're in the project root directory" -ForegroundColor Yellow
    Write-Host "2. Verify all required files exist" -ForegroundColor Yellow
    Write-Host "3. Ensure Docker services are running" -ForegroundColor Yellow
    Write-Host "4. Run: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}
