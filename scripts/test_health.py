import asyncio, os, sys

# Ensure project root is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import health_check, initialize_services

async def main():
    try:
        # Manually initialize services (normally done by FastAPI startup event)
        initialize_services()
        res = await health_check()
        print(res)
    except Exception as e:
        print('ERROR:', type(e).__name__, e)

if __name__ == '__main__':
    asyncio.run(main())
