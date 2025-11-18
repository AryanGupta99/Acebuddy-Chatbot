#!/usr/bin/env python3
"""Quick single test"""
import requests
import sys
import os

os.chdir(r"C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG")

try:
    print("Sending query to chatbot...")
    r = requests.post("http://127.0.0.1:8000/chat", json={"query": "How do I reset my password?"}, timeout=90)
    
    if r.status_code == 200:
        d = r.json()
        print(f"\n✅ SUCCESS!\n\nResponse:\n{d['answer']}\n\nConfidence: {d['confidence']}%")
    else:
        print(f"HTTP {r.status_code}: {r.text[:200]}")
except requests.exceptions.ConnectionError:
    print("Server not running. Start it with:\nuvicorn app.main:app --host 127.0.0.1 --port 8000")
except Exception as e:
    print(f"Error: {e}")
