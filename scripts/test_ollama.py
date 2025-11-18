import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app.main import query_ollama

if __name__ == '__main__':
    try:
        out = query_ollama("Briefly say 'Ollama test OK' and nothing else.")
        print('RESPONSE:', out)
    except Exception as e:
        print('ERROR:', type(e).__name__, e)
