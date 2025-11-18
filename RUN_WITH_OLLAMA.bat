@echo off
REM Start AceBuddy Server and Test with Ollama
setlocal enabledelayedexpansion

cd /d "C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"

echo.
echo ===============================================================================
echo  ACEBUDDY RAG CHATBOT - STARTING SERVER WITH OLLAMA
echo ===============================================================================
echo.
echo  Checking Ollama...
ollama list 2>nul || (
    echo  ERROR: Ollama not running!
    echo  Please start Ollama with: ollama serve
    pause
    exit /b 1
)

echo.
echo  Starting FastAPI server...
echo  URL: http://127.0.0.1:8000
echo.
echo  Waiting for server to start...

start "AceBuddy Server" cmd /k "title AceBuddy RAG Server && uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 15 /nobreak

echo.
echo  Running tests...
echo.

python simple_test.py

echo.
echo  Test complete!
echo.
pause
