from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import requests
import chromadb
try:
    from chromadb.config import Settings  # Older Chroma versions
except Exception:
    Settings = None
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None
import os
import sys
from dotenv import load_dotenv
import logging
try:
    import openai
except Exception:
    openai = None

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from intent import classify_query
except ImportError:
    # Fallback if intent module not available
    def classify_query(query: str):
        return "unknown", 0.0

try:
    from conversation_manager import get_conversation_manager
except ImportError:
    get_conversation_manager = None

try:
    from query_enhancement import get_query_enhancer, get_response_validator
except ImportError:
    get_query_enhancer = None
    get_response_validator = None

# Load environment variables
load_dotenv()

# Configure OpenAI API key if provided
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if openai and OPENAI_API_KEY:
    try:
        openai.api_key = OPENAI_API_KEY
        logger = logging.getLogger(__name__)
        logger.info("OpenAI API key loaded from environment")
    except Exception:
        pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import advanced RAG features
try:
    from .streaming_handler import StreamingHandler
    from .semantic_cache import SemanticCache
    from .query_optimizer import QueryOptimizer
    from .reranker_fusion import RerankerFusion
    from .fallback_handler import FallbackHandler
    from .analytics import AnalyticsTracker
    from .advanced_chat import chat_advanced, AdvancedChatRequest, AdvancedChatResponse
except ImportError as e:
    logger.warning(f"Some advanced features not available: {e}")
    StreamingHandler = None
    SemanticCache = None
    QueryOptimizer = None
    RerankerFusion = None
    FallbackHandler = None
    AnalyticsTracker = None
    chat_advanced = None
    AdvancedChatRequest = None
    AdvancedChatResponse = None

app = FastAPI(title="AceBuddy RAG Chatbot", version="2.0.0")

# Initialize models and clients
embedding_model = None
chroma_client = None
collection = None
conversation_manager = None
query_enhancer = None
response_validator = None

# Advanced RAG components
streaming_handler = None
semantic_cache = None
query_optimizer = None
reranker_fusion = None
fallback_handler = None

# Optional offline embedding mode (useful for testing without HF downloads)
# Default to FALSE so we use real embeddings for accuracy; can be overridden via env.
EMBEDDING_OFFLINE = os.getenv("EMBEDDING_OFFLINE", "false").lower() == "true"

# Dummy embedding for offline mode
class DummyEmbedding:
    """Deterministic hash-based dummy embedding for testing only.
    Returns a fixed-length vector (384 dims) derived from the sha256 of the text.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def encode(self, texts):
        import hashlib
        out = []
        if isinstance(texts, str):
            texts = [texts]
        for t in texts:
            h = hashlib.sha256(t.encode('utf-8')).digest()
            # expand/repeat digest to reach required dims
            vals = []
            i = 0
            while len(vals) < self.dim:
                chunk = h[i % len(h)]
                # map byte to float in [0,1)
                vals.append((chunk / 255.0))
                i += 1
            out.append(vals[:self.dim])
        return out

# Feature flags
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
ENABLE_QUERY_OPTIMIZATION = os.getenv("ENABLE_QUERY_OPTIMIZATION", "true").lower() == "true"
ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "true").lower() == "true"
ENABLE_FALLBACK = os.getenv("ENABLE_FALLBACK", "true").lower() == "true"


class OllamaEmbedding:
    """Embedding backend using Ollama's /api/embeddings endpoint."""
    def __init__(self, model: str = "nomic-embed-text", host: str = None, timeout: int = 20):
        self.model = model
        self.host = host or os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.timeout = timeout

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        url = f"{self.host}/api/embeddings"
        out = []
        for t in texts:
            try:
                resp = requests.post(url, json={"model": self.model, "prompt": t}, timeout=self.timeout)
                resp.raise_for_status()
                emb = resp.json().get("embedding")
                if not emb:
                    raise ValueError("No embedding returned")
                out.append(emb)
            except Exception as e:
                logger.warning(f"Ollama embedding failed: {e}. Falling back to dummy for this item.")
                out.append(DummyEmbedding().encode([t])[0])
        return out


class OpenAIEmbedding:
    """Embedding backend using OpenAI embeddings API."""
    def __init__(self, model: str = None, api_key: str = None, batch_size: int = 256):
        self.model = model or os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.batch_size = batch_size

    def _get_client(self):
        if not openai:
            raise Exception('OpenAI SDK not installed')

        client = None
        if hasattr(openai, 'OpenAI'):
            try:
                client = openai.OpenAI(api_key=self.api_key)
            except Exception:
                client = None

        if client is None:
            if self.api_key:
                try:
                    openai.api_key = self.api_key
                except Exception:
                    pass
            client = openai

        return client

    def _create_embeddings(self, client, batch):
        embed_factory = None
        if hasattr(client, 'embeddings') and callable(getattr(client.embeddings, 'create', None)):
            embed_factory = client.embeddings.create
        elif hasattr(client, 'Embedding') and callable(getattr(client.Embedding, 'create', None)):
            embed_factory = client.Embedding.create
        elif hasattr(client, 'Embedding') and isinstance(client.Embedding, dict) and callable(client.Embedding.get('create')):
            embed_factory = client.Embedding.get('create')

        if embed_factory is None:
            raise Exception('Unable to access OpenAI embeddings creation method')

        return embed_factory(model=self.model, input=batch)

    def _extract_embeddings(self, resp):
        data = getattr(resp, 'data', None)
        if data is None and isinstance(resp, dict):
            data = resp.get('data')
        if not data:
            raise Exception('OpenAI embeddings response missing data payload')

        embeddings = []
        for item in data:
            embedding = getattr(item, 'embedding', None)
            if embedding is None and isinstance(item, dict):
                embedding = item.get('embedding')
            if embedding is None:
                raise Exception('Failed to read embedding from OpenAI response item')
            embeddings.append(embedding)
        return embeddings

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = []

        client = self._get_client()

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            resp = self._create_embeddings(client, batch)
            embeddings.extend(self._extract_embeddings(resp))

        return embeddings

class ChatRequest(BaseModel):
    query: str
    user_id: str = "default"
    session_id: Optional[str] = None  # Optional session ID for conversation history
    use_history: bool = True  # Whether to use conversation context
    enhance_query: bool = True  # Whether to enhance query with synonyms/rewrites

class ContextItem(BaseModel):
    """Rich context item with provenance"""
    content: str
    source: str = ""
    chunk_id: str = ""
    rank: int = 0
    confidence: float = 0.0

class ChatResponse(BaseModel):
    answer: str
    intent: str = "unknown"
    intent_confidence: float = 0.0
    context: list = []  # Deprecated - kept for backward compatibility
    context_with_metadata: list = []  # List of ContextItem dicts
    confidence: float = 0.0
    session_id: Optional[str] = None  # Session ID for conversation tracking
    response_quality: float = 0.0  # Quality score (0-1) of response
    query_enhanced: bool = False  # Whether query was enhanced

def initialize_services():
    """Initialize embedding model and vector database"""
    global embedding_model, chroma_client, collection, conversation_manager, query_enhancer, response_validator
    global streaming_handler, semantic_cache, query_optimizer, reranker_fusion, fallback_handler
    
    try:
        # Initialize embedding model
        logger.info("Loading embedding model...")
        if EMBEDDING_OFFLINE:
            logger.info("EMBEDDING_OFFLINE=true -> using DummyEmbedding for testing")
            embedding_model = DummyEmbedding()
        else:
            embedding_model = None
            # Prefer OpenAI embeddings when API key is available (highest quality)
            if os.getenv('OPENAI_API_KEY'):
                try:
                    embedding_model = OpenAIEmbedding()
                    logger.info(f"Using OpenAI embeddings: {os.getenv('OPENAI_EMBEDDING_MODEL')} to match collection")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
                    embedding_model = None
            
            # Prefer Ollama embeddings if available and no higher-priority provider was selected
            if embedding_model is None:
                try:
                    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
                    ollama_embed_model = os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text')
                    ping = requests.get(f"{ollama_host}/api/tags", timeout=3)
                    if ping.status_code == 200:
                        embedding_model = OllamaEmbedding(model=ollama_embed_model, host=ollama_host)
                        logger.info(f"Using Ollama embeddings: {ollama_embed_model}")
                except Exception as e:
                    logger.warning(f"Ollama embeddings not available: {e}")

            # Fallback to SentenceTransformer if installed
            if embedding_model is None and SentenceTransformer is not None:
                try:
                    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("Using SentenceTransformer embeddings: all-MiniLM-L6-v2")
                except Exception as e:
                    logger.warning(f"Failed to load SentenceTransformer: {e}")

            # Last resort
            if embedding_model is None:
                logger.warning("Falling back to DummyEmbedding due to missing embedding backends")
                embedding_model = DummyEmbedding()

        # Initialize Chroma client (use persistent client)
        logger.info("Connecting to Chroma...")
        chroma_dir = Path(__file__).parent.parent / "data" / "chroma"
        # Disable anonymized telemetry to avoid external SSL calls where supported
        try:
            chroma_client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False) if Settings else None
            )
        except Exception:
            try:
                # Older API
                if Settings:
                    chroma_client = chromadb.Client(Settings(persist_directory=str(chroma_dir), anonymized_telemetry=False))
                else:
                    chroma_client = chromadb.Client()
            except Exception as ce:
                logger.error(f"Failed to connect to Chroma: {ce}")
                raise
        logger.info(f"Connected to persistent ChromaDB at: {chroma_dir}")
        
        # Get or create collection
        collection_name = os.getenv('VECTOR_DB_COLLECTION', 'acebuddy_kb')
        try:
            collection = chroma_client.get_collection(collection_name)
            doc_count = collection.count()
            logger.info(f"Connected to existing collection: {collection_name} ({doc_count} documents)")
        except:
            collection = chroma_client.create_collection(collection_name)
            logger.info(f"Created new collection: {collection_name}")
        
        # Initialize conversation manager
        if get_conversation_manager:
            try:
                conversation_manager = get_conversation_manager()
                logger.info("Conversation manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize conversation manager: {e}")
                conversation_manager = None
        
        # Initialize query enhancer
        if get_query_enhancer:
            try:
                query_enhancer = get_query_enhancer()
                logger.info("Query enhancer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize query enhancer: {e}")
                query_enhancer = None
        
        # Initialize response validator
        if get_response_validator:
            try:
                response_validator = get_response_validator()
                logger.info("Response validator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize response validator: {e}")
                response_validator = None
        
        # Initialize advanced RAG components
        if StreamingHandler and ENABLE_STREAMING:
            try:
                streaming_handler = StreamingHandler()
                logger.info("Streaming handler initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize streaming handler: {e}")
        
        if SemanticCache and ENABLE_CACHE:
            try:
                cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
                semantic_cache = SemanticCache(ttl_seconds=cache_ttl)
                logger.info(f"Semantic cache initialized (TTL: {cache_ttl}s)")
            except Exception as e:
                logger.warning(f"Failed to initialize semantic cache: {e}")
        
        if QueryOptimizer and ENABLE_QUERY_OPTIMIZATION:
            try:
                query_optimizer = QueryOptimizer()
                logger.info("Query optimizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize query optimizer: {e}")
        
        if RerankerFusion and ENABLE_RERANKING:
            try:
                reranker_fusion = RerankerFusion()
                logger.info("Reranker/fusion initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize reranker: {e}")
        
        if FallbackHandler and ENABLE_FALLBACK:
            try:
                fallback_handler = FallbackHandler()
                logger.info("Fallback handler initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize fallback handler: {e}")
            
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

def _ollama_model_present(ollama_host: str, model: str) -> bool:
    try:
        tags = requests.get(f"{ollama_host}/api/tags", timeout=5)
        tags.raise_for_status()
        data = tags.json()
        models = {m.get("name", "") for m in data.get("models", [])}
        # normalize names like "mistral:latest"
        return any(model in m for m in models)
    except Exception:
        return False

def query_openai(prompt: str, model: str = None) -> str:
    """Query OpenAI ChatCompletion API for generation (OpenAI SDK v2.8.0+)"""
    if not openai:
        raise Exception("OpenAI SDK not installed")
    model = model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    try:
        logger.info(f"Querying OpenAI [{model}]")
        
        # Initialize client with API key
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Make request using new SDK syntax
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.2')),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '512'))
        )
        
        # Extract text from response
        if resp and resp.choices and len(resp.choices) > 0:
            text = resp.choices[0].message.content
            if not text:
                text = 'No response from OpenAI'
        else:
            text = 'No response from OpenAI'
        
        logger.info(f"OpenAI response received ({len(text)} chars)")
        return text
    except Exception as e:
        logger.error(f"Error querying OpenAI: {e}")
        raise

def query_ollama(prompt: str, model: str = None) -> str:
    """Query Ollama for text generation (defaults to small model for reliability)"""
    try:
        model = model or os.getenv('OLLAMA_MODEL', 'llama3.2:1b')
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

        logger.info(f"Querying Ollama [{model}] at {ollama_host}")

        # Verify Ollama connection
        ping = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if ping.status_code != 200:
            raise Exception(f"Ollama not responding (status: {ping.status_code})")

        # Check that model is available; provide actionable error if missing
        if not _ollama_model_present(ollama_host, model):
            raise Exception(
                f"Ollama model '{model}' not found. Run: `ollama pull {model}` in a terminal, then retry."
            )
        
        url = f"{ollama_host}/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,      # Balanced creativity vs accuracy
                "top_p": 0.9,            # Nucleus sampling for quality
                "top_k": 40,             # Limit token choices
                "repeat_penalty": 1.1,   # Reduce repetition
                "num_ctx": 4096,         # Context window
                "num_predict": 512,
                "num_gpu": int(os.getenv('OLLAMA_NUM_GPU', '0'))
            }
        }
        
        logger.info("Sending request to Ollama...")
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json().get('response', 'No response generated')
        logger.info(f"Ollama response received ({len(result)} chars)")
        return result
        
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to Ollama at {ollama_host}")
        logger.error("Please start Ollama with: ollama serve")
        raise Exception(f"Ollama connection failed at {ollama_host}")
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out after 60 seconds")
        raise Exception("Ollama timeout - response took too long")
    except Exception as e:
        logger.error(f"Error querying Ollama: {type(e).__name__}: {e}")
        raise

def generate_fallback_response(contexts: list) -> str:
    """Generate a response directly from context when LLM is unavailable"""
    if not contexts:
        return "I couldn't find relevant information to answer your question. Please contact support for assistance."
    
    # Find the most relevant context (highest confidence)
    best_context = max(contexts, key=lambda x: x.get("confidence", 0))
    
    # Extract the content
    content = best_context.get("content", "")
    confidence = best_context.get("confidence", 0)
    
    # If confidence is too low, provide a generic response
    if confidence < 0.3:
        return f"I found some information that might be related, but I'm not very confident it answers your question:\n\n{content[:500]}...\n\nFor more accurate assistance, please contact support."
    
    # Return the most relevant content with a disclaimer
    response = f"Based on the knowledge base, here's what I found:\n\n{content}"
    
    # Add source if available
    source = best_context.get("source", "")
    if source:
        response += f"\n\n(Source: {source})"
    
    return response

def retrieve_context(query: str, top_k: int = 5, enhance: bool = True) -> list:
    """Retrieve relevant context from vector database with rich metadata
    
    Args:
        query: Original user query
        top_k: Number of results to retrieve per query
        enhance: Whether to enhance query with synonyms/rewrites
    
    Returns:
        List of context items with metadata
    """
    try:
        if not collection:
            logger.warning("Collection not initialized")
            return []
        
        # Enhance query if enabled and enhancer available
        queries_to_search = [query]  # Always include original
        query_was_enhanced = False
        
        if enhance and query_enhancer:
            try:
                enhanced = query_enhancer.enhance(query)  # Fixed: use 'enhance' not 'enhance_query'
                if enhanced.rewritten and enhanced.rewritten != query:
                    queries_to_search.append(enhanced.rewritten)
                    query_was_enhanced = True
                # Add top 2 expanded variations
                for expanded in enhanced.expanded_queries[:2]:
                    if expanded not in queries_to_search:
                        queries_to_search.append(expanded)
                        query_was_enhanced = True
                
                if query_was_enhanced:
                    logger.info(f"Enhanced query into {len(queries_to_search)} variations")
            except Exception as e:
                logger.warning(f"Query enhancement failed: {e}, using original query")
        
        # Retrieve contexts for all query variations
        all_contexts = {}  # Use dict to deduplicate by chunk_id
        
        for search_query in queries_to_search:
            # Generate query embedding
            emb = embedding_model.encode([search_query])
            try:
                emb_list = emb.tolist()
            except AttributeError:
                emb_list = emb
            except Exception as e:
                logger.warning(f"Embedding conversion issue: {e}, using as-is")
                emb_list = emb
            
            query_embedding = emb_list[0] if isinstance(emb_list, list) else emb_list
            
            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Extract documents and metadata
            documents = results.get('documents', [[]])[0]
            distances = results.get('distances', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            ids = results.get('ids', [[]])[0]
            
            # Process results, keeping best confidence for each chunk
            for i, (doc, distance, metadata, doc_id) in enumerate(zip(documents, distances, metadatas, ids)):
                source = metadata.get('source', '') if metadata else ''
                if not source and metadata:
                    source = metadata.get('file', metadata.get('source_doc_id', ''))
                
                confidence = max(0, 1 - distance)
                
                # Keep best confidence score if duplicate
                if doc_id not in all_contexts or all_contexts[doc_id]["confidence"] < confidence:
                    all_contexts[doc_id] = {
                        "content": doc,
                        "source": source,
                        "chunk_id": doc_id,
                        "rank": 0,  # Will rerank later
                        "confidence": confidence,
                        "metadata": metadata or {}
                    }
        
        # Sort by confidence and assign ranks
        context = sorted(all_contexts.values(), key=lambda x: x["confidence"], reverse=True)
        for i, ctx in enumerate(context):
            ctx["rank"] = i + 1
        
        logger.info(f"Retrieved {len(context)} unique contexts (from {len(queries_to_search)} query variations)")
        return context[:top_k * 2]  # Return up to 2x top_k results
        
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    initialize_services()

@app.get("/")
async def root():
    return {"message": "AceBuddy RAG Chatbot API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if services are available
        services_status = {
            "embedding_model": embedding_model is not None,
            "chroma_client": chroma_client is not None,
            "collection": collection is not None,
            "conversation_manager": conversation_manager is not None,
            "query_enhancer": query_enhancer is not None,
            "response_validator": response_validator is not None
        }

        # Check Ollama availability and model presence
        try:
            ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            model = os.getenv('OLLAMA_MODEL', 'mistral')
            resp = requests.get(f"{ollama_host}/api/tags", timeout=3)
            services_status["ollama_up"] = (resp.status_code == 200)
            services_status["ollama_model_ready"] = _ollama_model_present(ollama_host, model) if services_status["ollama_up"] else False
        except Exception:
            services_status["ollama_up"] = False
            services_status["ollama_model_ready"] = False
        all_healthy = all(services_status.values())
        return {
            "status": "healthy" if all_healthy else "partial",
            "services": services_status,
            "version": "2.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

@app.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 50):
    """Get conversation history for a session"""
    try:
        if not conversation_manager:
            raise HTTPException(status_code=503, detail="Conversation manager not available")
        
        session = conversation_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        history = conversation_manager.get_conversation_history(session_id, limit=limit)
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "message_count": len(history),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "intent": msg.intent,
                    "confidence": msg.confidence,
                    "metadata": msg.metadata
                }
                for msg in history
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {e}")

@app.get("/conversation/stats")
async def get_conversation_stats():
    """Get conversation manager statistics"""
    try:
        if not conversation_manager:
            raise HTTPException(status_code=503, detail="Conversation manager not available")
        
        stats = conversation_manager.get_stats()
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {e}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with conversation history, intent classification, query enhancement, and response validation"""
    try:
        logger.info(f"Received query: {request.query} (user: {request.user_id}, session: {request.session_id})")
        
        # Get or create conversation session
        session_id = request.session_id
        conversation_context = ""
        
        if conversation_manager and request.use_history:
            try:
                if not session_id:
                    # Create new session (returns session_id string)
                    session_id = conversation_manager.create_session(user_id=request.user_id)
                    logger.info(f"Created new conversation session: {session_id}")
                else:
                    # Get existing session
                    session = conversation_manager.get_or_create_session(user_id=request.user_id, session_id=session_id)
                    session_id = session.session_id
                
                # Get conversation context for LLM prompt
                conversation_context = conversation_manager.get_context_for_prompt(session_id, max_turns=3)
                
                # Add user message to history
                conversation_manager.add_message(
                    session_id=session_id,
                    role="user",
                    content=request.query
                )
                
                if conversation_context:
                    logger.info(f"Using conversation context: {len(conversation_context)} chars")
            except Exception as e:
                logger.warning(f"Conversation history failed: {e}, continuing without history")
                session_id = None
        
        # Classify intent
        intent, intent_confidence = classify_query(request.query)
        logger.info(f"Detected intent: {intent} (confidence: {intent_confidence:.2f})")
        
        # Retrieve relevant context (with optional query enhancement)
        context = retrieve_context(request.query, top_k=5, enhance=request.enhance_query)
        query_was_enhanced = request.enhance_query and query_enhancer is not None
        
        if not context:
            # No context found, provide a fallback response
            answer = "I don't have enough information to answer that question. Please contact support for assistance."
            
            # Add assistant response to history
            if conversation_manager and session_id:
                conversation_manager.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=answer,
                    intent=intent,
                    confidence=0.0
                )
            
            return ChatResponse(
                answer=answer,
                intent=intent,
                intent_confidence=intent_confidence,
                context=[],
                context_with_metadata=[],
                confidence=0.0,
                session_id=session_id,
                response_quality=0.0,
                query_enhanced=query_was_enhanced
            )
        
        # Prepare prompt for Ollama with enhanced instructions
        context_text = "\n\n".join([f"[Source {i+1}]: {ctx['content']}" for i, ctx in enumerate(context[:5])])  # Use top 5 results
        
        # Build prompt with conversation history if available
        if conversation_context:
            prompt = f"""You are AceBuddy, an expert IT support assistant. Your goal is to provide accurate, helpful, and professional technical support.

INSTRUCTIONS:
1. Use ONLY the information from the Knowledge Base Context below
2. Provide clear, step-by-step instructions when applicable
3. Reference the conversation history for context if relevant
4. If the Knowledge Base doesn't contain the answer, politely say so and suggest contacting support
5. Be specific with technical details (port numbers, file paths, commands)
6. Keep your response concise but complete

PREVIOUS CONVERSATION:
{conversation_context}

KNOWLEDGE BASE CONTEXT:
{context_text}

CURRENT QUESTION: {request.query}

RESPONSE (provide a professional, accurate answer):"""
        else:
            prompt = f"""You are AceBuddy, an expert IT support assistant. Your goal is to provide accurate, helpful, and professional technical support.

INSTRUCTIONS:
1. Use ONLY the information from the Knowledge Base Context below
2. Provide clear, step-by-step instructions when applicable
3. If the context doesn't contain the answer, politely say so and suggest contacting support
4. Be specific with technical details (port numbers, file paths, commands)
5. Keep your response concise but complete

KNOWLEDGE BASE CONTEXT:
{context_text}

QUESTION: {request.query}

RESPONSE (provide a professional, accurate answer):"""

        # Generate response using selected LLM backend
        use_openai = os.getenv('USE_OPENAI', 'false').lower() == 'true'
        answer = None

        if use_openai and OPENAI_API_KEY:
            try:
                answer = query_openai(prompt)
                logger.info(f"✅ Got answer from OpenAI: {len(answer)} chars")
            except Exception as e:
                logger.error(f"OpenAI generation failed: {e}")
                # Try Ollama as fallback if available
                try:
                    answer = query_ollama(prompt)
                    logger.info(f"✅ Fallback answer from Ollama: {len(answer)} chars")
                except Exception as e2:
                    logger.error(f"Ollama fallback also failed: {e2}")
                    answer = f"I apologize, but I'm unable to generate a response at the moment. The AI response system is not available. Please try again later or contact support.\n\nErrors: OpenAI: {str(e)} | Ollama: {str(e2)}"
        else:
            # Prefer Ollama by default
            try:
                answer = query_ollama(prompt)
                logger.info(f"✅ Got answer from Ollama: {len(answer)} chars")
            except Exception as e:
                logger.error(f"Ollama failed: {e}")
                # If OpenAI key present, try OpenAI as fallback
                if OPENAI_API_KEY and openai:
                    try:
                        answer = query_openai(prompt)
                        logger.info(f"✅ Fallback answer from OpenAI: {len(answer)} chars")
                    except Exception as e2:
                        logger.error(f"OpenAI fallback also failed: {e2}")
                        answer = f"I apologize, but I'm unable to generate a response at the moment. The AI response system is not available. Please try again later or contact support.\n\nErrors: Ollama: {str(e)} | OpenAI: {str(e2)}"
                else:
                    answer = f"I apologize, but I'm unable to generate a response at the moment. The AI response system is not available. Please try again later or contact support.\n\nError: {str(e)}"
        
        # Calculate average confidence from retrieved context
        avg_confidence = sum(ctx["confidence"] for ctx in context) / len(context) if context else 0.0
        
        # Validate response quality
        response_quality = 0.5  # Default neutral quality
        if response_validator:
            try:
                is_valid, quality_score, reason = response_validator.validate(
                    response=answer,
                    query=request.query,
                    context_confidence=avg_confidence
                )
                response_quality = quality_score
                
                if not is_valid:
                    logger.warning(f"Response validation flagged issue: {reason} (quality: {quality_score:.2f})")
                    
                    # If quality is very low, add disclaimer
                    if quality_score < 0.3:
                        answer += "\n\n*Note: I may not have enough context to fully answer this question. Please contact support if you need more help.*"
                
                logger.info(f"Response quality score: {quality_score:.2f}")
            except Exception as e:
                logger.warning(f"Response validation failed: {e}")
        
        # Add assistant response to conversation history
        if conversation_manager and session_id:
            conversation_manager.add_message(
                session_id=session_id,
                role="assistant",
                content=answer,
                intent=intent,
                confidence=avg_confidence,
                metadata={
                    "response_quality": response_quality,
                    "contexts_used": len(context)
                }
            )
        
        # Prepare context for response (both formats for compatibility)
        context_simple = [ctx["content"] for ctx in context]
        context_with_metadata = [
            {
                "content": ctx["content"],
                "source": ctx["source"],
                "chunk_id": ctx["chunk_id"],
                "rank": ctx["rank"],
                "confidence": ctx["confidence"]
            }
            for ctx in context
        ]
        
        logger.info(f"Generated response for query: {request.query} (quality: {response_quality:.2f})")
        
        return ChatResponse(
            answer=answer,
            intent=intent,
            intent_confidence=intent_confidence,
            context=context_simple,
            context_with_metadata=context_with_metadata,
            confidence=avg_confidence,
            session_id=session_id,
            response_quality=response_quality,
            query_enhanced=query_was_enhanced
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing request: {e}")

@app.post("/ingest")
async def ingest_knowledge():
    """Endpoint to trigger knowledge base ingestion using RAGIngester"""
    try:
        # Import RAGIngester
        try:
            from rag_ingestion import RAGIngester
        except ImportError:
            # Fallback to inline ingestion if module not available
            logger.warning("RAGIngester not available, using fallback inline ingestion")
            return await _ingest_fallback()
        
        # Use prepared chunks if available
        prepared_chunks = os.path.join(os.getcwd(), 'data', 'prepared', 'chunks_for_rag.json')
        
        if os.path.exists(prepared_chunks):
            logger.info(f"Using prepared chunks from: {prepared_chunks}")
            ingester = RAGIngester(
                collection_name=os.getenv('VECTOR_DB_COLLECTION', 'acebuddy_kb'),
                embedding_offline=EMBEDDING_OFFLINE
            )
            stats = ingester.ingest_chunks(prepared_chunks, min_quality_score=0.3)
            
            return {
                "message": f"Ingested {stats.get('ingested_chunks', 0)} chunks from prepared data",
                "stats": {
                    "total_chunks": stats.get('total_chunks', 0),
                    "ingested": stats.get('ingested_chunks', 0),
                    "filtered": stats.get('quality_filtered', 0),
                    "failed": stats.get('failed_chunks', 0)
                }
            }
        else:
            # Fallback: ingest raw KB files
            logger.info("Prepared chunks not found, ingesting raw KB files")
            return await _ingest_fallback()
            
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


async def _ingest_fallback():
    """Fallback inline ingestion for raw KB files"""
    global collection
    
    data_dir = os.path.join(os.getcwd(), 'data')
    kb_dir = os.path.join(data_dir, 'kb')
    if not os.path.exists(kb_dir):
        return {"message": f"KB directory not found: {kb_dir}"}

    chunks = []
    for fname in os.listdir(kb_dir):
        if not fname.lower().endswith(('.txt', '.md')):
            continue
        path = os.path.join(kb_dir, fname)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        sentences = content.split('. ')
        current = ''
        chunk_id = 0
        for s in sentences:
            if len(current) + len(s) < 500:
                current += s + '. '
            else:
                if current.strip():
                    chunks.append({
                        'id': f"{fname}_{chunk_id}",
                        'content': current.strip(),
                        'metadata': {'file': fname, 'source': path}
                    })
                    chunk_id += 1
                current = s + '. '
        if current.strip():
            chunks.append({
                'id': f"{fname}_{chunk_id}",
                'content': current.strip(),
                'metadata': {'file': fname, 'source': path}
            })

    if not chunks:
        return {"message": "No KB chunks found to ingest"}

    # Generate embeddings
    texts = [c['content'] for c in chunks]
    logger.info(f"Generating embeddings for {len(texts)} chunks")
    embeddings = embedding_model.encode(texts)
    
    # Convert to list safely
    try:
        emb_list = embeddings.tolist()
    except AttributeError:
        emb_list = embeddings
    except Exception as e:
        logger.warning(f"Embedding conversion issue: {e}")
        emb_list = embeddings

    # Upsert into Chroma collection
    ids = [c['id'] for c in chunks]
    docs = [c['content'] for c in chunks]
    metas = [c['metadata'] for c in chunks]

    try:
        collection.add(ids=ids, documents=docs, embeddings=emb_list, metadatas=metas)
    except Exception as e:
        logger.warning(f"Failed to add to collection: {e}, trying to recreate...")
        try:
            chroma_client.delete_collection(collection.name)
        except:
            pass
        newcol = chroma_client.create_collection(collection.name)
        newcol.add(ids=ids, documents=docs, embeddings=emb_list, metadatas=metas)
        collection = newcol

    return {"message": f"Ingested {len(chunks)} chunks into collection {collection.name}"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv('FASTAPI_HOST', '0.0.0.0')
    port = int(os.getenv('FASTAPI_PORT', 8000))
    uvicorn.run(app, host=host, port=port)