import os
import requests

OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
models_to_try = [
    'llama3.2:1b',
    'phi:latest',
    'mistral:latest',
]

prompt = "Reply exactly: Ollama test OK."

for model in models_to_try:
    print('\n--- Trying model:', model)
    url = f"{OLLAMA_HOST}/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.9,
            "top_k": 10,
            "num_predict": 64,
            "num_gpu": int(os.getenv('OLLAMA_NUM_GPU', '0'))
        }
    }
    try:
        resp = requests.post(url, json=data, timeout=30)
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        print('Status:', resp.status_code)
        print('Body:', body)
        if resp.status_code == 200:
            # Try to extract response field
            if isinstance(body, dict):
                r = body.get('response') or body.get('output') or body
                print('Generated:', r)
            else:
                print('Raw output:', body)
            break
    except Exception as e:
        print('Error:', type(e).__name__, e)

print('\nDone')
