#!/usr/bin/env python3
"""
Simple wrapper to run ngrok and display the public URL
"""

import subprocess
import time
import requests
import json

def main():
    print("\n" + "="*70)
    print("ACEBUDDY RAG - PUBLIC WEBHOOK URL GENERATOR")
    print("="*70)
    
    print("\n1️⃣  Checking if API is running...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        if response.status_code == 200:
            print("   ✅ API is running on http://localhost:8000")
        else:
            print("   ⚠️  API responded with status", response.status_code)
    except:
        print("   ❌ API is not running. Start it with: python app/main_simple.py")
        return
    
    print("\n2️⃣  Starting ngrok tunnel...")
    print("   (ngrok is already installed)")
    
    # Start ngrok in background via powershell
    try:
        # Try to start ngrok
        proc = subprocess.Popen(
            ["ngrok", "http", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("   ⏳ Waiting for tunnel to initialize...")
        time.sleep(3)
        
        # Try to get the ngrok URL from the API
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('tunnels') and len(data['tunnels']) > 0:
                    public_url = data['tunnels'][0]['public_url']
                    print(f"\n✅ SUCCESS! Public URL generated:")
                    print(f"\n   🌐 {public_url}")
                    print(f"\n   📝 SalesIQ Webhook URL:")
                    print(f"      {public_url}/salesiq/chat")
                    print("\n" + "="*70)
                    print("NEXT STEPS:")
                    print("1. Copy the webhook URL above")
                    print("2. Go to Zoho SalesIQ dashboard")
                    print("3. Settings → Webhooks → Add Webhook")
                    print("4. Paste the URL: " + public_url + "/salesiq/chat")
                    print("5. Method: POST")
                    print("6. Click 'Test Connection'")
                    print("="*70 + "\n")
                    
                    # Keep running
                    print("🔒 Tunnel is active. Press Ctrl+C to close.\n")
                    proc.wait()
                    
        except Exception as e:
            print(f"\n⚠️  Could not fetch ngrok status: {e}")
            print("   The tunnel may still be running. Check:")
            print("   - ngrok dashboard: http://127.0.0.1:4040")
            print("   - Or look for 'Forwarding' line in ngrok output")
            proc.wait()
            
    except FileNotFoundError:
        print("\n❌ ngrok not found in PATH")
        print("   Please run: ngrok http 8000")
        print("   (in a separate terminal)")

if __name__ == "__main__":
    main()
