#!/usr/bin/env python3
"""
Simple script to run the FastAPI server with local tunnel information.
This shows you the local API URL for testing.
"""

import subprocess
import time
import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("\n" + "="*70)
    print("ACEBUDDY RAG - LOCAL API SERVER")
    print("="*70)
    print("\n✓ Starting API server on http://localhost:8000")
    print("\n📌 LOCAL TESTING URL:")
    print("   http://localhost:8000")
    print("\n📝 Available endpoints for testing:")
    print("   GET  http://localhost:8000/docs (API Documentation)")
    print("   POST http://localhost:8000/chat (Main Chat Endpoint)")
    print("   POST http://localhost:8000/salesiq/chat (SalesIQ Webhook)")
    print("   GET  http://localhost:8000/salesiq/status (Health Check)")
    print("\n⚠️  FOR PUBLIC WEBHOOK TESTING:")
    print("   You need ngrok or Cloudflare tunnel (see TROUBLESHOOTING below)")
    print("\n" + "="*70 + "\n")
    
    # Run the main app
    os.system("python app/main.py")

if __name__ == "__main__":
    main()
