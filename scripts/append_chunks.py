import os
import json
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
import logging
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_chunks(chunks_file: Path):
    if not chunks_file.exists():
        raise FileNotFoundError(chunks_file)
    with open(chunks_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def get_openai_embeddings(texts, api_key, model='text-embedding-3-small', disable_ssl=False):
    # Create OpenAI client; optionally disable SSL verification for local testing
    if disable_ssl:
        # Globally disable SSL verification for local testing (not for production)
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

    chunks_file = project_root / 'data' / 'processed_chunks.json'
    chunks = load_chunks(chunks_file)
    logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")

    provider = os.getenv('EMBEDDING_PROVIDER', 'OPENAI').upper()
    disable_ssl = os.getenv('DISABLE_SSL_VERIFY', 'false').lower() in ('1','true','yes')

    # Connect to persistent Chroma
    chroma_dir = project_root / 'data' / 'chroma'
    # Create client consistent with app: prefer PersistentClient, fallback to Client
    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        logger.info("Connected to persistent Chroma via PersistentClient")
    except Exception:
        try:
            from chromadb.config import Settings
            client = chromadb.Client(Settings(persist_directory=str(chroma_dir)))
            logger.info("Connected to persistent Chroma via Client(Settings)")
        except Exception:
            client = chromadb.Client()
            logger.info("Connected to Chroma via default Client")

    # Get or create collection
    collection_name = os.getenv('VECTOR_DB_COLLECTION', 'acebuddy_kb')
    try:
        collection = client.get_collection(collection_name)
        logger.info(f"Using existing collection: {collection_name}")
    except Exception:
        collection = client.create_collection(collection_name)
        logger.info(f"Created collection: {collection_name}")

    # Prepare data
    ids = [c['id'] for c in chunks]
    docs = [c['content'] for c in chunks]
    metadatas = [c.get('metadata', {}) for c in chunks]

    # Inspect existing collection to determine embedding dimension (if any)
    existing = None
    try:
        existing = collection.get()
    except Exception:
        existing = None

    existing_dim = None
    if existing and existing.get('ids'):
        sample_id = existing.get('ids')[0]
        try:
            samp = collection.get(ids=[sample_id], include=['embeddings'])
            emb = samp.get('embeddings', [[]])[0][0]
            if emb:
                existing_dim = len(emb)
                logger.info(f"Detected existing collection embedding dim: {existing_dim}")
        except Exception:
            existing_dim = None

    # Choose embedding provider: prefer explicit provider setting, else match existing collection
    embeddings = None
    provider_env = os.getenv('EMBEDDING_PROVIDER', 'OPENAI').upper()

    if provider_env == 'OPENAI' or existing_dim == 1536:
        # Use OpenAI embeddings (1536-d) when requested or when collection already uses 1536-d
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception('OPENAI_API_KEY missing in .env')
        model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        logger.info(f"Generating embeddings via OpenAI ({model}) to match provider {provider_env} or existing dim {existing_dim}")
        embeddings = get_openai_embeddings(docs, api_key, model=model, disable_ssl=disable_ssl)
    else:
        # Default to local SentenceTransformer 384-dim embeddings to match older Chroma collections
        from sentence_transformers import SentenceTransformer
        local_model = os.getenv('LOCAL_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        logger.info(f"Generating embeddings via local SentenceTransformer ({local_model})")
        model = SentenceTransformer(local_model)
        embeddings = model.encode(docs)
        try:
            embeddings = embeddings.tolist()
        except Exception:
            pass

    # Append to collection (avoid duplicate ids)
    existing_ids = set()
    try:
        existing = collection.get()
        for cid in existing.get('ids', []):
            existing_ids.add(cid)
    except Exception:
        pass

    to_add_ids = []
    to_add_docs = []
    to_add_emb = []
    to_add_meta = []
    for i, idx in enumerate(ids):
        if idx in existing_ids:
            logger.info(f"Skipping existing chunk id: {idx}")
            continue
        to_add_ids.append(idx)
        to_add_docs.append(docs[i])
        to_add_emb.append(embeddings[i])
        to_add_meta.append(metadatas[i])

    if not to_add_ids:
        logger.info("No new chunks to add; exiting")
        return

    logger.info(f"Adding {len(to_add_ids)} new chunks to collection '{collection_name}'")
    collection.add(ids=to_add_ids, documents=to_add_docs, embeddings=to_add_emb, metadatas=to_add_meta)

    try:
        client.persist()
    except Exception:
        pass

    logger.info("Append complete. Persisted Chroma DB.")


if __name__ == '__main__':
    main()
