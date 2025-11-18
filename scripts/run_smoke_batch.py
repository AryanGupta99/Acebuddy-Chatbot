import requests
import json
import time
import os
from datetime import datetime

URL = 'http://127.0.0.1:8000/chat'

queries = [
    "How do I reset my password?",
    "How can I increase disk storage on my server?",
    "My RDP connection keeps disconnecting, what should I check?",
    "Printer is not responding on Windows 10 — troubleshooting steps?",
    "How do I configure email (SMTP) for our application?",
    "How do I add or remove a user from the system?",
    "Server CPU is high — how to diagnose performance issues?",
    "QuickBooks shows data error on startup, what should I try?",
    "How do I set up a monitor for server alerts?",
    "Where can I find the AceBuddy support guide?"
]

results = []

def do_request_with_retries(payload, max_retries=3, backoff_factor=1.0, timeout=60):
    attempt = 0
    while attempt < max_retries:
        try:
            r = requests.post(URL, json=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            attempt += 1
            wait = backoff_factor * (2 ** (attempt - 1))
            print(f"Request failed (attempt {attempt}/{max_retries}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    return {"error": f"Failed after {max_retries} attempts: {str(e)}"}


for i, q in enumerate(queries, start=1):
    payload = {"query": q, "session_id": f"smoke_batch_{i}", "use_history": False}
    resp = do_request_with_retries(payload, max_retries=3, backoff_factor=1.0, timeout=60)

    entry = {
        "query": q,
        "timestamp": datetime.now().isoformat(),
        "response": resp
    }
    results.append(entry)

    # small delay between requests to avoid bursting the server
    time.sleep(1)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)
out_path = os.path.join('data', 'smoke_test_results.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(results)} results to {out_path}")
