"""
Advanced Chat Endpoint with All Features
========================================

This module extends main.py with advanced RAG features:
- Streaming responses
- Semantic caching
- Query optimization
- Reranking and fusion
- Intelligent fallbacks
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import numpy as np

# This should be imported into main.py


class AdvancedChatRequest(BaseModel):
    query: str
    user_id: str = "default"
    session_id: Optional[str] = None
    use_history: bool = True
    enhance_query: bool = True
    enable_streaming: bool = False
    enable_cache: bool = True
    enable_optimization: bool = True
    enable_reranking: bool = True


class AdvancedChatResponse(BaseModel):
    answer: str
    intent: str = "unknown"
    intent_confidence: float = 0.0
    confidence: float = 0.0
    session_id: Optional[str] = None
    response_quality: float = 0.0
    query_enhanced: bool = False
    cache_hit: bool = False
    optimization_used: bool = False
    reranking_used: bool = False
    fallback_used: bool = False
    context_sources: List[str] = []
    related_questions: List[str] = []
    suggestions: List[str] = []
    processing_time_ms: float = 0.0


async def chat_advanced(request: AdvancedChatRequest, app_globals: dict) -> AdvancedChatResponse:
    """
    Advanced chat endpoint with all optimizations
    
    Flow:
    1. Check semantic cache
    2. Optimize query (multi-query, HyDE, expansion)
    3. Retrieve with multiple strategies
    4. Fuse and rerank results
    5. Generate response
    6. Validate and apply fallback if needed
    7. Cache result
    """
    import time
    start_time = time.time()
    
    # Extract globals
    embedding_model = app_globals.get("embedding_model")
    collection = app_globals.get("collection")
    conversation_manager = app_globals.get("conversation_manager")
    semantic_cache = app_globals.get("semantic_cache")
    query_optimizer = app_globals.get("query_optimizer")
    reranker_fusion = app_globals.get("reranker_fusion")
    fallback_handler = app_globals.get("fallback_handler")
    
    query = request.query
    cache_hit = False
    optimization_used = False
    reranking_used = False
    fallback_used = False
    
    # Get conversation context
    conversation_context = None
    if request.use_history and conversation_manager:
        history = conversation_manager.get_conversation_history(
            request.user_id,
            request.session_id
        )
        conversation_context = "|".join([msg.get("content", "") for msg in history[-2:]])
    
    # 1. Check cache
    query_embedding = None
    if request.enable_cache and semantic_cache:
        query_embedding = np.array(embedding_model.encode([query])[0])
        cached = semantic_cache.get(query, query_embedding, conversation_context)
        
        if cached:
            cache_hit = True
            processing_time = (time.time() - start_time) * 1000
            
            return AdvancedChatResponse(
                answer=cached["response"],
                intent=cached["metadata"].get("intent", "unknown"),
                confidence=cached["metadata"].get("confidence", 0.0),
                session_id=request.session_id,
                cache_hit=True,
                processing_time_ms=processing_time
            )
    
    # 2. Query optimization
    optimized_queries = [query]
    hyde_document = ""
    
    if request.enable_optimization and query_optimizer:
        try:
            intent, _ = classify_query(query)
            optimization_result = await query_optimizer.optimize_query(
                query,
                intent,
                conversation_history if request.use_history else None
            )
            
            optimized_queries = optimization_result.get("multi_queries", [query])
            hyde_document = optimization_result.get("hyde_document", "")
            optimization_used = True
            
        except Exception as e:
            logger.warning(f"Query optimization failed: {e}")
    
    # 3. Retrieve with multiple strategies
    all_results = []
    
    # Strategy 1: Multi-query retrieval
    for opt_query in optimized_queries[:3]:  # Limit to top 3
        try:
            embedding = embedding_model.encode([opt_query])[0]
            results = collection.query(
                query_embeddings=[embedding],
                n_results=10
            )
            
            # Convert to standard format
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    all_results.append({
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0.5,
                        "id": results["ids"][0][i] if results.get("ids") else ""
                    })
        except Exception as e:
            logger.error(f"Retrieval error for query '{opt_query}': {e}")
    
    # Strategy 2: HyDE retrieval (if available)
    if hyde_document and len(hyde_document) > 20:
        try:
            hyde_embedding = embedding_model.encode([hyde_document])[0]
            hyde_results = collection.query(
                query_embeddings=[hyde_embedding],
                n_results=5
            )
            
            if hyde_results and hyde_results.get("documents"):
                for i, doc in enumerate(hyde_results["documents"][0]):
                    all_results.append({
                        "text": doc,
                        "metadata": hyde_results["metadatas"][0][i] if hyde_results.get("metadatas") else {},
                        "distance": hyde_results["distances"][0][i] if hyde_results.get("distances") else 0.5,
                        "id": hyde_results["ids"][0][i] if hyde_results.get("ids") else "",
                        "hyde_result": True
                    })
        except Exception as e:
            logger.warning(f"HyDE retrieval failed: {e}")
    
    # 4. Fusion and reranking
    context_docs = all_results
    
    if request.enable_reranking and reranker_fusion and len(all_results) > 0:
        try:
            # Reciprocal rank fusion if we have multiple query results
            if len(optimized_queries) > 1:
                # Group results by query
                query_groups = []
                docs_per_query = len(all_results) // len(optimized_queries)
                
                for i in range(len(optimized_queries)):
                    start_idx = i * docs_per_query
                    end_idx = start_idx + docs_per_query if i < len(optimized_queries) - 1 else len(all_results)
                    query_groups.append(all_results[start_idx:end_idx])
                
                fused_results = reranker_fusion.reciprocal_rank_fusion(query_groups)
                context_docs = fused_results
            
            # Rerank with query
            context_docs = reranker_fusion.rerank_with_query(
                query,
                context_docs,
                top_k=5
            )
            reranking_used = True
            
        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            context_docs = all_results[:5]  # Fallback to top results
    else:
        context_docs = all_results[:5]
    
    # 5. Generate response
    intent, intent_conf = classify_query(query)
    
    # Build prompt with context
    context_text = "\n\n".join([
        f"[Source {i+1}] {doc.get('text', '')}"
        for i, doc in enumerate(context_docs[:3])
    ])
    
    prompt = f"""You are Ace Buddy, a professional IT support assistant.

Context:
{context_text}

Question: {query}

Provide a clear, helpful answer based on the context. Be professional and concise."""
    
    response_text = query_ollama(prompt)
    
    # 6. Calculate confidence and check for fallback
    confidence = calculate_confidence(response_text, context_docs)
    context_quality = 1.0 - (context_docs[0].get("distance", 0.5) if context_docs else 0.5)
    
    suggestions = []
    related_questions = []
    
    if fallback_handler and fallback_handler.should_use_fallback(
        confidence, context_quality, response_text
    ):
        fallback_result = fallback_handler.generate_fallback_response(
            query, intent, confidence, response_text, context_docs
        )
        
        response_text = fallback_result["answer"]
        suggestions = fallback_result.get("suggestions", [])
        related_questions = fallback_result.get("related_questions", [])
        fallback_used = True
    
    # 7. Cache result
    if request.enable_cache and semantic_cache and not fallback_used:
        try:
            if query_embedding is None:
                query_embedding = np.array(embedding_model.encode([query])[0])
            
            semantic_cache.set(
                query,
                query_embedding,
                response_text,
                context_docs,
                {"intent": intent, "confidence": confidence},
                conversation_context
            )
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    # Update conversation history
    if conversation_manager:
        if not request.session_id:
            request.session_id = f"{request.user_id}_{int(time.time())}"
        
        conversation_manager.add_message(
            request.user_id,
            request.session_id,
            "user",
            query
        )
        conversation_manager.add_message(
            request.user_id,
            request.session_id,
            "assistant",
            response_text
        )
    
    processing_time = (time.time() - start_time) * 1000
    
    return AdvancedChatResponse(
        answer=response_text,
        intent=intent,
        intent_confidence=intent_conf,
        confidence=confidence,
        session_id=request.session_id,
        response_quality=confidence,
        query_enhanced=optimization_used,
        cache_hit=cache_hit,
        optimization_used=optimization_used,
        reranking_used=reranking_used,
        fallback_used=fallback_used,
        context_sources=[doc.get("metadata", {}).get("source", "") for doc in context_docs[:3]],
        related_questions=related_questions,
        suggestions=suggestions,
        processing_time_ms=processing_time
    )


def calculate_confidence(response: str, context_docs: list) -> float:
    """Calculate response confidence score"""
    confidence = 0.5
    
    if len(response) > 50:
        confidence += 0.1
    
    if len(context_docs) >= 3:
        confidence += 0.2
    
    if any(kw in response.lower() for kw in ["according to", "based on", "as mentioned"]):
        confidence += 0.1
    
    if not any(word in response.lower() for word in ["maybe", "might", "not sure"]):
        confidence += 0.1
    
    return min(confidence, 1.0)


# Helper function to import Ollama query function
def query_ollama(prompt: str, model: str = "mistral") -> str:
    """This should use the actual query_ollama from main.py"""
    import requests
    import os
    
    try:
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        url = f"{ollama_host}/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "num_ctx": 4096,
                "num_predict": 512
            }
        }
        
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        return response.json().get('response', 'No response generated')
    except Exception as e:
        return f"Error generating response: {str(e)}"


# Helper function for intent classification
def classify_query(query: str):
    """This should use the actual classify_query from main.py"""
    # Simple fallback implementation
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["how", "setup", "configure", "install"]):
        return "how_to", 0.8
    elif any(word in query_lower for word in ["error", "issue", "problem", "fix", "trouble"]):
        return "troubleshooting", 0.8
    elif any(word in query_lower for word in ["bill", "invoice", "payment", "charge"]):
        return "billing", 0.9
    else:
        return "unknown", 0.5
