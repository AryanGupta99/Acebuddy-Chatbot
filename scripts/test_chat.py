import os, sys, asyncio
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('OLLAMA_MODEL', 'llama3.2:1b')
os.environ.setdefault('OLLAMA_NUM_GPU', '0')
os.environ.setdefault('EMBEDDING_OFFLINE', 'true')

from app.main import initialize_services, chat, ChatRequest

async def main():
    initialize_services()
    queries = [
        "How do I reset my password?",
        "Steps to add a new user in Windows domain?",
        "Printer not working – how to troubleshoot?",
        "RDP connection is slow, what can I check?"
    ]
    for q in queries:
        req = ChatRequest(query=q, user_id='tester', use_history=False)
        try:
            resp = await chat(req)
            print("Q:", q)
            print("A:", (resp.answer or '')[:400], "\n")
        except Exception as e:
            print("Q:", q)
            print("ERROR:", type(e).__name__, e, "\n")

if __name__ == '__main__':
    asyncio.run(main())
