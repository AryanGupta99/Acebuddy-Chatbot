#!/usr/bin/env python3
"""
Get ngrok public URL by querying the ngrok API dashboard
"""

import requests
import time
import subprocess
import threading

def start_ngrok_subprocess():
    """Start ngrok in a separate process"""
    try:
        print("Starting ngrok subprocess...")
        proc = subprocess.Popen(
            ["ngrok", "http", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return proc
    except Exception as e:
        print(f"Error starting ngrok: {e}")
        return None

def get_ngrok_url():
    """Get the public URL from ngrok API"""
    for attempt in range(10):
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('tunnels') and len(data['tunnels']) > 0:
                    return data['tunnels'][0]['public_url']
        except:
            pass
        
        print(f"   Waiting for ngrok to start... ({attempt + 1}/10)")
        time.sleep(1)
    
    return None

def main():
    print("\n" + "="*70)
    print("ACEBUDDY RAG - PUBLIC WEBHOOK URL GENERATOR")
    print("="*70)
    
    # Verify API is running
    print("\n1️⃣  Checking if API is running...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        print("   ✅ API is running on localhost:8000")
    except:
        print("   ❌ API not running. Start it first:")
        print("   python app/main_simple.py")
        return
    
    # Start ngrok
    print("\n2️⃣  Starting ngrok tunnel...")
    proc = start_ngrok_subprocess()
    
    if proc is None:
        print("   ❌ Failed to start ngrok")
        return
    
    # Get the public URL
    print("\n3️⃣  Retrieving public URL...")
    public_url = get_ngrok_url()
    
    if public_url:
        webhook_url = f"{public_url}/salesiq/chat"
        
        print(f"\n✅ SUCCESS!")
        print(f"\n   PUBLIC URL: {public_url}")
        print(f"\n   🎯 SalesIQ WEBHOOK URL:")
        print(f"      {webhook_url}")
        
        print("\n" + "="*70)
        print("USE THIS URL IN ZOHO SALESIQ:")
        print("="*70)
        print(f"Webhook URL: {webhook_url}")
        print("Method:      POST")
        print("Headers:     Content-Type: application/json")
        print("="*70 + "\n")
        
        print("🔒 Tunnel running. Press Ctrl+C to stop.\n")
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\n\nStopping ngrok...")
            proc.terminate()
            proc.wait()
    else:
        print("   ❌ Could not get ngrok URL")
        print("   Check: http://127.0.0.1:4040 in your browser")
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    main()
