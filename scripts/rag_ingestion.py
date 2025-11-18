"""
RAG Data Ingestion Pipeline
===========================

Takes cleaned data and ingests into vector database (Chroma)
with quality validation and metadata enrichment.
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import time
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGIngester:
    """Ingest cleaned data into Chroma vector database"""
    
    def __init__(
        self,
        collection_name: str = "acebuddy_kb",
        embedding_offline: bool = None,
        chroma_host: str = "localhost",
        chroma_port: int = 8000
    ):
        """
        Initialize RAG ingester
        
        Args:
            collection_name: Chroma collection name
            embedding_offline: Use offline embedding (DummyEmbedding)
            chroma_host: Chroma server host
            chroma_port: Chroma server port
        """
        self.collection_name = collection_name
        
        # Determine embedding mode
        if embedding_offline is None:
            embedding_offline = os.getenv("EMBEDDING_OFFLINE", "false").lower() == "true"
        self.embedding_offline = embedding_offline
        
        # Initialize Chroma client
        try:
            logger.info(f"Connecting to Chroma at {chroma_host}:{chroma_port}")
            self.client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        except Exception as e:
            logger.warning(f"Failed to connect to Chroma server, using local client: {e}")
            self.client = chromadb.Client()
        
        # Initialize embedding model
        self._init_embedding_model()
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        self.stats = {
            'total_chunks': 0,
            'ingested_chunks': 0,
            'failed_chunks': 0,
            'quality_filtered': 0,
            'start_time': None,
            'end_time': None,
        }
    
    def _init_embedding_model(self):
        """Initialize embedding model"""
        if self.embedding_offline:
            logger.info("Using offline DummyEmbedding (testing mode)")
            self.embedding_model = self._DummyEmbedding()
        else:
            logger.info("Loading SentenceTransformer embedding model...")
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}, falling back to dummy")
                self.embedding_model = self._DummyEmbedding()
    
    class _DummyEmbedding:
        """Offline embedding for testing"""
        def __init__(self, dim: int = 384):
            self.dim = dim
        
        def encode(self, texts):
            import hashlib
            out = []
            for t in texts:
                h = hashlib.sha256(t.encode('utf-8')).digest()
                vals = []
                i = 0
                while len(vals) < self.dim:
                    chunk = h[i % len(h)]
                    vals.append((chunk / 255.0))
                    i += 1
                out.append(vals[:self.dim])
            return out
    
    def _get_or_create_collection(self):
        """Get existing or create new collection"""
        try:
            collection = self.client.get_collection(self.collection_name)
            logger.info(f"Connected to existing collection: {self.collection_name}")
        except Exception:
            collection = self.client.create_collection(self.collection_name)
            logger.info(f"Created new collection: {self.collection_name}")
        
        return collection
    
    def ingest_chunks(
        self,
        chunks_file: str,
        min_quality_score: float = 0.5,
        batch_size: int = 50
    ) -> Dict:
        """
        Ingest chunks from cleaned data file
        
        Args:
            chunks_file: Path to chunks_for_rag.json
            min_quality_score: Filter chunks below this quality
            batch_size: Process in batches
            
        Returns:
            Ingestion statistics
        """
        self.stats['start_time'] = datetime.now()
        
        logger.info(f"Loading chunks from: {chunks_file}")
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load chunks: {e}")
            return self.stats
        
        self.stats['total_chunks'] = len(chunks)
        logger.info(f"Loaded {len(chunks)} chunks")
        
        # Filter by quality
        quality_filtered = [c for c in chunks if c.get('metadata', {}).get('quality_score', 1.0) < min_quality_score]
        if quality_filtered:
            chunks = [c for c in chunks if c not in quality_filtered]
            self.stats['quality_filtered'] = len(quality_filtered)
            logger.info(f"Filtered {len(quality_filtered)} low-quality chunks")
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            self._ingest_batch(batch)
        
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        logger.info(f"Ingestion completed in {duration:.1f}s")
        
        return self.stats
    
    def _ingest_batch(self, batch: List[Dict]):
        """Ingest a batch of chunks"""
        try:
            # Prepare batch data
            ids = [chunk['id'] for chunk in batch]
            documents = [chunk['content'] for chunk in batch]
            metadatas = [chunk['metadata'] for chunk in batch]
            
            # Generate embeddings
            logger.debug(f"Generating embeddings for {len(documents)} chunks...")
            embeddings = self.embedding_model.encode(documents)
            
            # Convert numpy to list with robust error handling
            try:
                # Try standard numpy tolist()
                embeddings_list = embeddings.tolist()
                logger.debug("Embeddings converted using .tolist()")
            except AttributeError:
                # Already a list or list-like object
                logger.debug("Embeddings already in list format")
                embeddings_list = embeddings
            except Exception as e:
                logger.warning(f"Embedding conversion issue: {e}, attempting fallback")
                # Fallback: try converting each embedding individually
                try:
                    embeddings_list = [list(emb) if hasattr(emb, '__iter__') else emb for emb in embeddings]
                    logger.debug("Embeddings converted using fallback method")
                except Exception as e2:
                    logger.error(f"Failed to convert embeddings: {e2}, using as-is")
                    embeddings_list = embeddings
            
            # Add to collection
            logger.debug(f"Adding {len(ids)} chunks to Chroma...")
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings_list,
                metadatas=metadatas
            )
            
            self.stats['ingested_chunks'] += len(ids)
            logger.info(f"Ingested batch: {len(ids)} chunks")
            
        except Exception as e:
            logger.error(f"Error ingesting batch: {e}")
            import traceback
            traceback.print_exc()
            self.stats['failed_chunks'] += len(batch)
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'total_documents': count,
                'embedding_offline': self.embedding_offline,
                'ingestion_stats': self.stats
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}
    
    def print_stats(self):
        """Print ingestion statistics"""
        stats = self.get_collection_stats()
        
        print("""
═══════════════════════════════════════════════════════════════
RAG INGESTION REPORT
═══════════════════════════════════════════════════════════════
Collection:                     {}
Total Chunks Processed:         {}
Chunks Ingested:                {}
Chunks Failed:                  {}
Quality Filtered:               {}
Documents in Collection:        {}
Embedding Mode:                 {}

Performance:
Start Time:                     {}
End Time:                       {}
Duration:                       {:.1f}s
Chunks/Second:                  {:.1f}
═══════════════════════════════════════════════════════════════
        """.format(
            stats.get('collection_name'),
            stats.get('ingestion_stats', {}).get('total_chunks', 0),
            stats.get('ingestion_stats', {}).get('ingested_chunks', 0),
            stats.get('ingestion_stats', {}).get('failed_chunks', 0),
            stats.get('ingestion_stats', {}).get('quality_filtered', 0),
            stats.get('total_documents', 0),
            'Offline (DummyEmbedding)' if self.embedding_offline else 'Online (SentenceTransformer)',
            stats.get('ingestion_stats', {}).get('start_time', ''),
            stats.get('ingestion_stats', {}).get('end_time', ''),
            (stats.get('ingestion_stats', {}).get('end_time') - stats.get('ingestion_stats', {}).get('start_time')).total_seconds()
            if stats.get('ingestion_stats', {}).get('end_time') else 0,
            stats.get('ingestion_stats', {}).get('ingested_chunks', 0) / 
            max(1, (stats.get('ingestion_stats', {}).get('end_time') - stats.get('ingestion_stats', {}).get('start_time')).total_seconds())
            if stats.get('ingestion_stats', {}).get('end_time') else 0
        ))


def main():
    """Example usage"""
    ingester = RAGIngester()
    
    # Ingest cleaned chunks
    chunks_file = "data/prepared/chunks_for_rag.json"
    ingester.ingest_chunks(chunks_file, min_quality_score=0.5)
    
    # Print statistics
    ingester.print_stats()


if __name__ == "__main__":
    main()
