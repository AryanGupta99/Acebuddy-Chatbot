"""
Semantic Cache for RAG System
============================

Implements intelligent caching with:
- Exact match caching (hash-based)
- Semantic similarity caching (embedding-based)
- TTL-based expiration
- Cache warming for common queries
- Analytics and statistics
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class SemanticCache:
    """Semantic cache with exact and similarity matching"""
    
    def __init__(
        self,
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 3600,
        max_cache_size: int = 1000
    ):
        """
        Initialize semantic cache
        
        Args:
            similarity_threshold: Min similarity for cache hit (0-1)
            ttl_seconds: Time-to-live for cache entries
            max_cache_size: Maximum number of cached entries
        """
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.max_cache_size = max_cache_size
        
        # Exact match cache (hash-based)
        self.exact_cache: Dict[str, Dict[str, Any]] = {}
        
        # Semantic cache (embedding-based)
        self.semantic_cache: List[Dict[str, Any]] = []
        
        # Statistics
        self.stats = {
            "exact_hits": 0,
            "semantic_hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0,
            "cache_saves_ms": 0
        }
        
        logger.info(f"Semantic cache initialized: threshold={similarity_threshold}, TTL={ttl_seconds}s")
    
    def get(
        self,
        query: str,
        query_embedding: Optional[np.ndarray] = None,
        conversation_context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve from cache
        
        Returns cached response if:
        1. Exact match found (same query + context)
        2. Semantic match found (similar query + context above threshold)
        
        Args:
            query: User query
            query_embedding: Query embedding for semantic matching
            conversation_context: Conversation context for matching
        
        Returns:
            Cached response dict or None
        """
        self.stats["total_queries"] += 1
        
        # 1. Try exact match
        cache_key = self._generate_cache_key(query, conversation_context)
        exact_result = self._get_exact(cache_key)
        
        if exact_result:
            self.stats["exact_hits"] += 1
            logger.debug(f"Cache exact hit: {query[:50]}...")
            return exact_result
        
        # 2. Try semantic match (if embedding provided)
        if query_embedding is not None:
            semantic_result = self._get_semantic(query_embedding, conversation_context)
            
            if semantic_result:
                self.stats["semantic_hits"] += 1
                logger.debug(f"Cache semantic hit: {query[:50]}... (similarity={semantic_result['similarity']:.3f})")
                return semantic_result
        
        # 3. Cache miss
        self.stats["misses"] += 1
        return None
    
    def set(
        self,
        query: str,
        query_embedding: Optional[np.ndarray],
        response: str,
        context_docs: List[Dict],
        metadata: Dict[str, Any],
        conversation_context: Optional[str] = None
    ):
        """
        Store in cache
        
        Args:
            query: User query
            query_embedding: Query embedding
            response: Generated response
            context_docs: Retrieved context documents
            metadata: Response metadata (confidence, sources, etc.)
            conversation_context: Conversation context
        """
        cache_entry = {
            "query": query,
            "response": response,
            "context_docs": context_docs,
            "metadata": metadata,
            "conversation_context": conversation_context,
            "timestamp": datetime.now(),
            "hits": 0
        }
        
        # Store in exact cache
        cache_key = self._generate_cache_key(query, conversation_context)
        self.exact_cache[cache_key] = cache_entry
        
        # Store in semantic cache (if embedding provided)
        if query_embedding is not None:
            semantic_entry = cache_entry.copy()
            semantic_entry["embedding"] = query_embedding
            self.semantic_cache.append(semantic_entry)
        
        # Enforce cache size limits
        self._enforce_cache_limits()
        
        logger.debug(f"Cached response: {query[:50]}...")
    
    def _get_exact(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get from exact match cache"""
        if cache_key not in self.exact_cache:
            return None
        
        entry = self.exact_cache[cache_key]
        
        # Check TTL
        if self._is_expired(entry):
            self.exact_cache.pop(cache_key)
            return None
        
        # Update hit count
        entry["hits"] += 1
        return entry
    
    def _get_semantic(
        self,
        query_embedding: np.ndarray,
        conversation_context: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get from semantic cache using similarity matching"""
        best_match = None
        best_similarity = 0.0
        
        for entry in self.semantic_cache:
            # Check TTL
            if self._is_expired(entry):
                continue
            
            # Check context match (if provided)
            if conversation_context and entry.get("conversation_context") != conversation_context:
                continue
            
            # Calculate similarity
            cached_embedding = entry["embedding"]
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_match = entry
        
        if best_match:
            best_match["hits"] += 1
            best_match["similarity"] = best_similarity
            return best_match
        
        return None
    
    def _generate_cache_key(self, query: str, conversation_context: Optional[str] = None) -> str:
        """Generate cache key from query and context"""
        key_data = query.lower().strip()
        if conversation_context:
            key_data += f"|{conversation_context}"
        
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        age = (datetime.now() - entry["timestamp"]).total_seconds()
        return age > self.ttl_seconds
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def _enforce_cache_limits(self):
        """Enforce cache size limits using LRU eviction"""
        # Evict from exact cache
        if len(self.exact_cache) > self.max_cache_size:
            # Sort by hits and timestamp (LRU)
            sorted_entries = sorted(
                self.exact_cache.items(),
                key=lambda x: (x[1]["hits"], x[1]["timestamp"])
            )
            
            # Remove oldest/least used 20%
            evict_count = len(self.exact_cache) - self.max_cache_size
            for key, _ in sorted_entries[:evict_count]:
                self.exact_cache.pop(key)
                self.stats["evictions"] += 1
        
        # Evict from semantic cache
        if len(self.semantic_cache) > self.max_cache_size:
            # Remove expired first
            self.semantic_cache = [e for e in self.semantic_cache if not self._is_expired(e)]
            
            # If still too large, remove least used
            if len(self.semantic_cache) > self.max_cache_size:
                self.semantic_cache.sort(key=lambda x: (x["hits"], x["timestamp"]), reverse=True)
                evict_count = len(self.semantic_cache) - self.max_cache_size
                self.semantic_cache = self.semantic_cache[:-evict_count]
                self.stats["evictions"] += evict_count
    
    def warm_cache(self, common_queries: List[Tuple[str, str, Dict]]):
        """
        Warm cache with common queries
        
        Args:
            common_queries: List of (query, response, metadata) tuples
        """
        logger.info(f"Warming cache with {len(common_queries)} common queries...")
        
        for query, response, metadata in common_queries:
            cache_key = self._generate_cache_key(query, None)
            self.exact_cache[cache_key] = {
                "query": query,
                "response": response,
                "context_docs": [],
                "metadata": metadata,
                "conversation_context": None,
                "timestamp": datetime.now(),
                "hits": 0,
                "warmed": True
            }
        
        logger.info("Cache warming complete")
    
    def invalidate(self, pattern: Optional[str] = None):
        """
        Invalidate cache entries
        
        Args:
            pattern: Optional pattern to match queries (None = clear all)
        """
        if pattern is None:
            # Clear all
            count_exact = len(self.exact_cache)
            count_semantic = len(self.semantic_cache)
            self.exact_cache.clear()
            self.semantic_cache.clear()
            logger.info(f"Cache cleared: {count_exact} exact, {count_semantic} semantic entries")
        else:
            # Clear matching pattern
            self.exact_cache = {
                k: v for k, v in self.exact_cache.items()
                if pattern.lower() not in v["query"].lower()
            }
            self.semantic_cache = [
                e for e in self.semantic_cache
                if pattern.lower() not in e["query"].lower()
            ]
            logger.info(f"Cache invalidated for pattern: {pattern}")
    
    def cleanup_expired(self):
        """Remove expired entries"""
        # Exact cache
        expired_keys = [
            k for k, v in self.exact_cache.items()
            if self._is_expired(v)
        ]
        for key in expired_keys:
            self.exact_cache.pop(key)
        
        # Semantic cache
        self.semantic_cache = [
            e for e in self.semantic_cache
            if not self._is_expired(e)
        ]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_queries = self.stats["total_queries"]
        hits = self.stats["exact_hits"] + self.stats["semantic_hits"]
        
        hit_rate = (hits / total_queries * 100) if total_queries > 0 else 0
        
        # Calculate average age
        all_entries = list(self.exact_cache.values()) + self.semantic_cache
        avg_age = 0
        if all_entries:
            ages = [(datetime.now() - e["timestamp"]).total_seconds() for e in all_entries]
            avg_age = sum(ages) / len(ages)
        
        return {
            "exact_hits": self.stats["exact_hits"],
            "semantic_hits": self.stats["semantic_hits"],
            "misses": self.stats["misses"],
            "total_queries": total_queries,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size_exact": len(self.exact_cache),
            "cache_size_semantic": len(self.semantic_cache),
            "evictions": self.stats["evictions"],
            "avg_age_seconds": round(avg_age, 2),
            "ttl_seconds": self.ttl_seconds,
            "similarity_threshold": self.similarity_threshold
        }
    
    def get_top_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently cached queries"""
        all_entries = list(self.exact_cache.values()) + self.semantic_cache
        sorted_entries = sorted(all_entries, key=lambda x: x["hits"], reverse=True)
        
        return [
            {
                "query": e["query"],
                "hits": e["hits"],
                "age_seconds": (datetime.now() - e["timestamp"]).total_seconds()
            }
            for e in sorted_entries[:limit]
        ]
