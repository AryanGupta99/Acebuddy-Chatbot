import csv
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import openai
import chromadb
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_and_chunk_data(data_path: Path) -> List[Dict]:
    """Load and chunk KB data from CSV files"""
    chunks = []
    
    # Load from real_user_issues.csv if it exists
    csv_file = data_path.parent / 'real_user_issues.csv'
    if csv_file.exists():
        logger.info(f"Loading data from {csv_file}")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                issue = row.get('issue', '')
                category = row.get('category', 'uncategorized')
                
                if issue.strip():
                    chunks.append({
                        'id': f'issue_{i}',
                        'content': f"Issue: {issue}\nCategory: {category}",
                        'metadata': {'category': category, 'source': 'user_issues'}
                    })
    
    # Load any KB files from data/kb/ directory (.txt and .md)
    kb_dir = data_path / 'kb'
    if kb_dir.exists():
        # configurable chunk size/overlap via env
        CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '800'))  # approx chars
        CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))

        for ext in ('*.txt', '*.md'):
            for file_path in kb_dir.glob(ext):
                logger.info(f"Loading KB file: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                    if not content:
                        continue

                    # Simple chunking by characters with overlap to preserve context
                    start = 0
                    chunk_id = 0
                    content_len = len(content)

                    while start < content_len:
                        end = start + CHUNK_SIZE
                        chunk_text = content[start:end].strip()
                        if chunk_text:
                            chunks.append({
                                'id': f'{file_path.stem}_{chunk_id}',
                                'content': chunk_text,
                                'metadata': {'source': 'kb_file', 'file': file_path.name}
                            })
                            chunk_id += 1

                        # advance with overlap
                        start = max(end - CHUNK_OVERLAP, end)
    
    logger.info(f"Loaded {len(chunks)} chunks total")
    return chunks

def generate_embeddings(chunks: List[Dict], model_name: str = 'all-MiniLM-L6-v2') -> List[List[float]]:
    """Generate embeddings for text chunks.
    Supports two providers controlled by `EMBEDDING_PROVIDER` env var: OPENAI or LOCAL (SentenceTransformer).
    """
    provider = os.getenv('EMBEDDING_PROVIDER', 'LOCAL').upper()
    texts = [chunk['content'] for chunk in chunks]

    if provider == 'OPENAI':
        model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        logger.info(f"Generating embeddings using OpenAI model: {model}")
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception('OPENAI_API_KEY is not set in environment')

        client = openai.OpenAI(api_key=api_key)
        # OpenAI has limits on batch size; chunk if necessary
        embeddings = []
        batch_size = 256
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            resp = client.embeddings.create(model=model, input=batch)
            for item in resp.data:
                embeddings.append(item.embedding)

        logger.info(f"Generated {len(embeddings)} embeddings via OpenAI")
        return embeddings

    # Fallback to local SentenceTransformer
    logger.info(f"Generating embeddings using local model: {model_name}")
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts)
    logger.info(f"Generated {len(embeddings)} embeddings (local)")
    return embeddings.tolist()

def ingest_to_chroma(chunks: List[Dict], embeddings: List[List[float]], collection_name: str = 'acebuddy_kb', persist_directory: str = None):
    """Ingest chunks and embeddings into Chroma vector database"""
    logger.info("Initializing Chroma client")
    
    # Use persistent Chroma DB if persist_directory provided; otherwise default client
    if persist_directory:
        from chromadb.config import Settings
        client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_directory))
        logger.info(f"Using persistent Chroma at: {persist_directory}")
    else:
        client = chromadb.Client()
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(collection_name)
        logger.info(f"Deleted existing collection: {collection_name}")
    except:
        pass
    
    # Create new collection
    collection = client.create_collection(collection_name)
    logger.info(f"Created collection: {collection_name}")
    
    # Prepare data for ingestion
    ids = [chunk['id'] for chunk in chunks]
    documents = [chunk['content'] for chunk in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]
    
    # Add to collection
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    logger.info(f"Ingested {len(chunks)} documents into collection")
    
    # Test query using same embedding provider to avoid Chroma downloading its own models
    try:
        query_chunks = [{'id': 'q0', 'content': 'password reset', 'metadata': {}}]
        query_embeddings = generate_embeddings(query_chunks)
        test_results = collection.query(
            query_embeddings=[query_embeddings[0]],
            n_results=3
        )
        logger.info(f"Test query returned {len(test_results['documents'][0])} results")
    except Exception as e:
        logger.warning(f"Skipping test query due to: {e}")
    
    # Persist if using persistent client
    try:
        client.persist()
    except Exception:
        pass

    return collection

def main():
    """Main ingestion script"""
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / 'data'
    # Load environment variables from project .env
    load_dotenv(project_root / '.env')
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    
    # Create data/kb directory if it doesn't exist
    kb_dir = data_dir / 'kb'
    kb_dir.mkdir(exist_ok=True)
    
    # Load and chunk data
    chunks = load_and_chunk_data(data_dir)
    
    if not chunks:
        logger.warning("No data found to ingest. Please add KB files to data/kb/ or ensure real_user_issues.csv exists.")
        return
    
    # Generate embeddings
    embeddings = generate_embeddings(chunks)
    
    # Ingest to Chroma (persist to project data/chroma for app pickup)
    chroma_dir = project_root / 'data' / 'chroma'
    chroma_dir.mkdir(exist_ok=True)
    collection = ingest_to_chroma(chunks, embeddings, persist_directory=str(chroma_dir))
    
    # Save chunks for reference
    chunks_file = data_dir / 'processed_chunks.json'
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved processed chunks to: {chunks_file}")
    logger.info("Data ingestion completed successfully!")

if __name__ == "__main__":
    main()