# AceBuddy RAG Chatbot - Start with Ollama (PowerShell)

Write-Host "`n" -ForegroundColor Green
Write-Host "╔════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         AceBuddy RAG Chatbot - OLLAMA Integration Ready! ✅                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "`n"

# Set location
$scriptDir = "C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
Set-Location $scriptDir

# Check Ollama
Write-Host "🔍 Checking Ollama..." -ForegroundColor Yellow
$ollamaCheck = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -ErrorAction SilentlyContinue

if ($null -eq $ollamaCheck) {
    Write-Host "❌ ERROR: Ollama is not running!" -ForegroundColor Red
    Write-Host "`nPlease start Ollama in another terminal:" -ForegroundColor Yellow
    Write-Host "  ollama serve`n" -ForegroundColor White
    exit
}

Write-Host "✅ Ollama is running!`n" -ForegroundColor Green

# Parse models
$models = $ollamaCheck.Content | ConvertFrom-Json
Write-Host "📚 Available Models:" -ForegroundColor Cyan
$models.models | ForEach-Object {
    Write-Host "   • $($_.name) ($([math]::Round($_.size/1GB, 1))GB)" -ForegroundColor White
}
Write-Host "`n"

# Start server
Write-Host "🚀 Starting FastAPI Server..." -ForegroundColor Green
Write-Host "   Host: 127.0.0.1" -ForegroundColor Gray
Write-Host "   Port: 8000" -ForegroundColor Gray
Write-Host "   API Docs: http://127.0.0.1:8000/docs`n" -ForegroundColor Gray

# Open server in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    cd '$scriptDir'
    Write-Host '════════════════════════════════════════════════════════════' -ForegroundColor Cyan
    Write-Host ' AceBuddy RAG Server' -ForegroundColor Green
    Write-Host '════════════════════════════════════════════════════════════' -ForegroundColor Cyan
    Write-Host ''
    Write-Host 'Starting server...' -ForegroundColor Yellow
    Write-Host ''
    uvicorn app.main:app --host 127.0.0.1 --port 8000
"

Write-Host "⏳ Waiting 15 seconds for server to initialize..." -ForegroundColor Yellow
for ($i = 15; $i -gt 0; $i--) {
    Write-Host "`r   $i seconds remaining... " -NoNewline
    Start-Sleep -Seconds 1
}
Write-Host "`n"

# Verify server
Write-Host "🔗 Verifying server connection..." -ForegroundColor Yellow
$maxAttempts = 5
$attempt = 0

while ($attempt -lt $maxAttempts) {
    try {
        $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -ErrorAction Stop
        if ($health.StatusCode -eq 200) {
            Write-Host "✅ Server is running and healthy!`n" -ForegroundColor Green
            break
        }
    }
    catch {
        $attempt++
        if ($attempt -lt $maxAttempts) {
            Write-Host "   Attempt $attempt/$maxAttempts... " -NoNewline
            Start-Sleep -Seconds 2
        }
    }
}

if ($attempt -eq $maxAttempts) {
    Write-Host "⚠️  Server is slow to start. Proceeding anyway...`n" -ForegroundColor Yellow
}

# Run test
Write-Host "🧪 Running Test Query..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Gray

$testQuery = @{
    query = "How do I reset my password?"
    session_id = "powershell_test"
} | ConvertTo-Json

try {
    Write-Host "`n📝 Query: How do I reset my password?`n" -ForegroundColor White
    
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/chat" `
        -Method Post `
        -Body $testQuery `
        -ContentType "application/json" `
        -TimeoutSec 120
    
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "✅ SUCCESS!`n" -ForegroundColor Green
    Write-Host "💬 Response from Ollama:" -ForegroundColor Cyan
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host $data.answer -ForegroundColor White
    Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📊 Confidence: $($data.confidence)%" -ForegroundColor Yellow
    Write-Host "🎯 Intent Detected: $($data.intent)" -ForegroundColor Yellow
    Write-Host "🤖 Source: $($data.source)" -ForegroundColor Yellow
    
}
catch {
    Write-Host "❌ Error during test: $_`n" -ForegroundColor Red
    Write-Host "Possible issues:" -ForegroundColor Yellow
    Write-Host "  1. Server not fully started yet (wait 10+ more seconds)" -ForegroundColor Gray
    Write-Host "  2. Ollama is not responding (check 'ollama serve' window)" -ForegroundColor Gray
    Write-Host "  3. Check server logs in the other window" -ForegroundColor Gray
}

Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "`nYour chatbot is ready at: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "`nMore test queries to try:" -ForegroundColor Cyan
Write-Host "  • How do I troubleshoot RDP connection issues?" -ForegroundColor Gray
Write-Host "  • How do I add a new user?" -ForegroundColor Gray
Write-Host "  • What should I do if my server is slow?" -ForegroundColor Gray
Write-Host "  • How do I set up a printer?" -ForegroundColor Gray
Write-Host ""

Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
