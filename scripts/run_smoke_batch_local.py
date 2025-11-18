import json
import os
import time
from datetime import datetime
import asyncio
import importlib.util
import sys

# Load the FastAPI app by filepath so this script runs from any cwd
proj_root = os.path.dirname(os.path.dirname(__file__))
app_path = os.path.join(proj_root, 'app', 'main.py')
spec = importlib.util.spec_from_file_location('app_main', app_path)
app_mod = importlib.util.module_from_spec(spec)
sys.modules['app_main'] = app_mod
spec.loader.exec_module(app_mod)
app = getattr(app_mod, 'app')
chat = getattr(app_mod, 'chat')
ChatRequest = getattr(app_mod, 'ChatRequest')
initialize_services = getattr(app_mod, 'initialize_services')

# Initialize services
print('Initializing services...')
initialize_services()
print('Services initialized')

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

for i, q in enumerate(queries, start=1):
    print(f'Running query {i}: {q}')
    req = ChatRequest(query=q, session_id=f'local_smoke_{i}', use_history=False, enhance_query=True)
    try:
        # chat is an async function, run it
        resp = asyncio.run(chat(req))
        try:
            data = resp.model_dump()
        except Exception:
            data = str(resp)
    except Exception as e:
        data = {'error': str(e)}
        import traceback
        traceback.print_exc()

    results.append({
        'query': q,
        'timestamp': datetime.now().isoformat(),
        'response': data
    })

    time.sleep(0.5)

os.makedirs('data', exist_ok=True)
out_path = os.path.join('data', 'smoke_test_results.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Local run complete — wrote {len(results)} results to {out_path}")
