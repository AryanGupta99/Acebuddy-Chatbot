"""
MANUAL NGROK SETUP GUIDE
Since ngrok has certificate issues, follow these manual steps.
"""

print("""

================================================================================
⚠️  NGROK TLS CERTIFICATE ERROR - MANUAL WORKAROUND
================================================================================

Your ngrok is having TLS verification issues (common with corporate networks).

SOLUTION: Use manual ngrok command in a separate terminal:

STEP 1: Open a NEW PowerShell window (separate from the API)

STEP 2: Run this exact command:
        ngrok http 8000

STEP 3: Wait for ngrok to start. You should see output like:

        Session Status                online
        Account                       <your-account>
        Version                       3.24.0
        Region                        us (United States)
        Latency                       45ms
        Web Interface                 http://127.0.0.1:4040
        Forwarding                    https://xxxxx-xx-xx-xx.ngrok.io -> http://localhost:8000

STEP 4: Copy the "Forwarding" URL (the https://xxxxx... part)
        This is your public webhook URL!

STEP 5: For SalesIQ, use:
        https://xxxxx-xx-xx-xx.ngrok.io/salesiq/chat

STEP 6: Share the URL with me, and I'll help configure SalesIQ

================================================================================
WHAT IF STEP 2 FAILS WITH CERTIFICATE ERROR?
================================================================================

If ngrok still fails, try these alternatives:

OPTION A: Use localtunnel (simpler, no TLS issues)
         npm install -g localtunnel
         lt --port 8000

OPTION B: Use Cloudflare tunnel  
         pip install cloudflared
         cloudflared tunnel --url http://localhost:8000

OPTION C: Use IP-based tunneling
         You can manually configure SalesIQ to use:
         http://<YOUR_IP>:8000/salesiq/chat
         (requires opening firewall, less secure)

================================================================================

Once you get the public URL, reply with it in this format:
"My webhook URL is: https://xxxxx-xx-xx-xx.ngrok.io/salesiq/chat"

================================================================================
""")
