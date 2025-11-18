#!/usr/bin/env python3
"""
Get public URL for webhook using pyngrok
"""

from pyngrok import ngrok, conf
import os
import time
import requests

def main():
    print("\n" + "="*70)
    print("ACEBUDDY RAG - PUBLIC WEBHOOK URL GENERATOR")
    print("="*70)
    
    # Skip SSL verification (for corporate networks)
    conf.get_ngrok_config().auth_token = os.getenv('NGROK_AUTH_TOKEN', '')
    
    print("\n1️⃣  Checking if API is running on localhost:8000...")
    time.sleep(2)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ API is running!")
        else:
            print(f"   ⚠️  API status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        print("   Make sure: python app/main_simple.py is running")
        return
    
    print("\n2️⃣  Creating public tunnel to localhost:8000...")
    try:
        # Suppress SSL warnings and use pyngrok
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Set up pyngrok with skip_browser option
        os.environ['PYNGROK_CONFIG'] = ''
        
        # Create the tunnel
        public_url = ngrok.connect(8000, "http", bind_tls=True)
        
        print(f"\n✅ PUBLIC URL CREATED:")
        print(f"\n   🌐 {public_url}")
        
        print(f"\n📝 SalesIQ WEBHOOK URL:")
        print(f"   {public_url}/salesiq/chat")
        
        print("\n" + "="*70)
        print("NEXT STEPS FOR SALESIQ INTEGRATION:")
        print("="*70)
        print("1. Copy this webhook URL:")
        webhook_url = f"{public_url}/salesiq/chat"
        print(f"   {webhook_url}")
        print("\n2. Go to Zoho SalesIQ Dashboard")
        print("3. Navigate to: Settings → Webhooks")
        print("4. Click 'Add Webhook'")
        print("5. Paste URL: " + webhook_url)
        print("6. Method: POST")
        print("7. Headers: Content-Type: application/json")
        print("8. Click 'Test Connection' - should see 200 OK response")
        print("="*70)
        
        print("\n🔒 Tunnel is ACTIVE. Press Ctrl+C to stop.\n")
        
        # Keep the tunnel running
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()
        
    except Exception as e:
        print(f"\n❌ Error creating tunnel: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Try: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")
        print("3. Or use manual ngrok: ngrok http 8000")

if __name__ == "__main__":
    main()
