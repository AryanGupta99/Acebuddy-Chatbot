import os
from pathlib import Path
import math
import logging
from dotenv import load_dotenv
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_openai_embeddings(texts, api_key, model='text-embedding-3-small', disable_ssl=False):
    # Create OpenAI client; optionally disable SSL verification for local testing
    if disable_ssl:
        import ssl
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
        except Exception:
            pass
        client = openai.OpenAI(api_key=api_key)
    else:
        client = openai.OpenAI(api_key=api_key)

    embeddings = []
    batch_size = 256
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        resp = client.embeddings.create(model=model, input=batch)
        for item in resp.data:
            embeddings.append(item.embedding)
    return embeddings


def main():
    project_root = Path(__file__).parent.parent
    load_dotenv(project_root / '.env')

    source_col = os.getenv('SOURCE_VECTOR_DB_COLLECTION', 'acebuddy_kb')
    target_col = os.getenv('VECTOR_DB_COLLECTION', 'acebuddy_kb_v2')
    api_key = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    disable_ssl = os.getenv('DISABLE_SSL_VERIFY', 'false').lower() in ('1','true','yes')

    if not api_key:
        raise Exception('OPENAI_API_KEY not set in .env')

    # Disable Chroma telemetry to avoid external PostHog calls (and SSL issues in local env)
    os.environ.setdefault('CHROMA_DISABLE_TELEMETRY', '1')
    os.environ.setdefault('CHROMA_TELEMETRY', '0')
    os.environ.setdefault('CHROMA_TELEMETRY_ENABLED', 'false')

    # Import chromadb after disabling telemetry env vars
    # Temporarily suppress stdout/stderr around chromadb import to avoid telemetry/network noise
    import sys, io
    _stdout, _stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
    try:
        import chromadb
        from chromadb.config import Settings
    finally:
        # restore streams
        sys.stdout, sys.stderr = _stdout, _stderr

    chroma_dir = project_root / 'data' / 'chroma'
    client = None
    try:
        # Prefer PersistentClient if available
        client = chromadb.PersistentClient(path=str(chroma_dir))
    except Exception:
        try:
            client = chromadb.Client(Settings(persist_directory=str(chroma_dir), anonymized_telemetry=False))
        except Exception:
            client = chromadb.Client()

    # Get source collection
    try:
        src = client.get_collection(source_col)
    except Exception as e:
        raise Exception(f"Source collection '{source_col}' not found: {e}")

    # Fetch all documents from source
    logger.info(f"Fetching documents from source collection: {source_col}")
    # Note: chromadb.Collection.get does not accept 'ids' in include; call without include to get ids
    res = src.get()
    ids = res.get('ids', [])
    docs = res.get('documents', [])
    metadatas = res.get('metadatas', [])

    total = len(ids)
    if total == 0:
        logger.info('No documents found in source collection; nothing to do.')
        return

    # Estimate API calls
    batch_size = 256
    calls = math.ceil(total / batch_size)
    logger.info(f"Found {total} documents to re-embed. Estimated OpenAI embedding calls: {calls} (batch_size={batch_size})")

    # Confirm before proceeding
    print('\nSummary:')
    print(f"- Source collection: {source_col}")
    print(f"- Target collection: {target_col}")
    print(f"- Embedding model: {model}")
    print(f"- Documents to process: {total}")
    print(f"- Estimated OpenAI embedding calls: {calls}\n")

    proceed = input('Proceed with re-embedding and writing to target collection? (yes/no): ').strip().lower()
    if proceed not in ('y','yes'):
        logger.info('Aborting per user request.')
        return

    # Create or get target collection
    try:
        tgt = client.get_collection(target_col)
        logger.info(f"Using existing target collection: {target_col}")
    except Exception:
        tgt = client.create_collection(target_col)
        logger.info(f"Created target collection: {target_col}")

    # Generate embeddings in batches and add to target collection
    logger.info('Generating embeddings and adding to target collection...')
    all_embeddings = []
    for i in range(0, total, batch_size):
        batch_docs = docs[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        batch_meta = metadatas[i:i+batch_size] if metadatas else [{}]*len(batch_docs)
        batch_embs = get_openai_embeddings(batch_docs, api_key, model=model, disable_ssl=disable_ssl)
        # add to target collection
        tgt.add(ids=batch_ids, documents=batch_docs, metadatas=batch_meta, embeddings=batch_embs)
        logger.info(f"Added batch {i//batch_size + 1} with {len(batch_docs)} docs")

    try:
        client.persist()
    except Exception:
        pass

    logger.info('Re-embedding complete. Target collection persisted.')


if __name__ == '__main__':
    main()
