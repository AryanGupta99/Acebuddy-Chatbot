"""
Reranking and Fusion for Better Retrieval
========================================

Implements:
- Cross-encoder reranking for precision
- Reciprocal Rank Fusion (RRF) for multi-query results
- Diversity-aware reranking
- Metadata-based boosting
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class RerankerFusion:
    """Rerank and fuse retrieved documents for optimal results"""
    
    def __init__(self):
        self.diversity_threshold = 0.85  # Similarity threshold for diversity
    
    def reciprocal_rank_fusion(
        self,
        multi_query_results: List[List[Dict]],
        k: int = 60
    ) -> List[Dict]:
        """
        Fuse results from multiple queries using RRF
        
        RRF Score = sum(1 / (k + rank_i)) for each query result
        
        Args:
            multi_query_results: List of result lists from different queries
            k: RRF constant (typically 60)
        
        Returns:
            Fused and ranked document list
        """
        doc_scores = defaultdict(float)
        doc_data = {}
        
        # Calculate RRF scores
        for query_results in multi_query_results:
            for rank, doc in enumerate(query_results, start=1):
                doc_id = self._get_doc_id(doc)
                
                # RRF formula
                rrf_score = 1.0 / (k + rank)
                doc_scores[doc_id] += rrf_score
                
                # Store document data (first occurrence)
                if doc_id not in doc_data:
                    doc_data[doc_id] = doc
        
        # Sort by RRF score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Build final result list
        fused_results = []
        for doc_id, rrf_score in sorted_docs:
            doc = doc_data[doc_id].copy()
            doc["rrf_score"] = rrf_score
            doc["fusion_method"] = "reciprocal_rank_fusion"
            fused_results.append(doc)
        
        logger.debug(f"RRF fused {len(multi_query_results)} result sets into {len(fused_results)} docs")
        return fused_results
    
    def rerank_with_query(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 10,
        metadata_boost: bool = True
    ) -> List[Dict]:
        """
        Rerank documents based on query relevance
        
        Uses multiple signals:
        - Semantic similarity (from retrieval)
        - Lexical overlap
        - Metadata boosting (recency, popularity, type)
        - Query-document alignment
        
        Args:
            query: User query
            documents: Retrieved documents
            top_k: Number of top documents to return
            metadata_boost: Apply metadata-based boosting
        
        Returns:
            Reranked documents
        """
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        reranked_docs = []
        
        for doc in documents:
            text = doc.get("text", "").lower()
            metadata = doc.get("metadata", {})
            
            # Base score from retrieval (distance/similarity)
            base_score = 1.0 - doc.get("distance", 0.5)  # Convert distance to similarity
            
            # Lexical overlap score
            doc_terms = set(text.split())
            overlap = len(query_terms & doc_terms)
            lexical_score = overlap / len(query_terms) if query_terms else 0
            
            # Exact phrase match bonus
            phrase_bonus = 0.2 if query_lower in text else 0
            
            # Query-document length alignment
            length_score = self._calculate_length_alignment(query, text)
            
            # Combined score
            relevance_score = (
                base_score * 0.5 +
                lexical_score * 0.3 +
                phrase_bonus +
                length_score * 0.2
            )
            
            # Metadata boosting
            if metadata_boost:
                boost = self._calculate_metadata_boost(metadata, query)
                relevance_score *= boost
            
            doc_copy = doc.copy()
            doc_copy["relevance_score"] = relevance_score
            doc_copy["lexical_overlap"] = lexical_score
            doc_copy["phrase_match"] = phrase_bonus > 0
            reranked_docs.append(doc_copy)
        
        # Sort by relevance score
        reranked_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Apply diversity
        diverse_docs = self._ensure_diversity(reranked_docs, top_k * 2)
        
        logger.debug(f"Reranked {len(documents)} docs, returning top {top_k}")
        return diverse_docs[:top_k]
    
    def _calculate_length_alignment(self, query: str, document: str) -> float:
        """
        Calculate if document length is appropriate for query
        Short queries → prefer concise answers
        Long queries → OK with detailed answers
        """
        query_len = len(query.split())
        doc_len = len(document.split())
        
        # Ideal doc length based on query
        if query_len < 5:
            ideal_len = 100
        elif query_len < 10:
            ideal_len = 200
        else:
            ideal_len = 300
        
        # Penalize documents too far from ideal
        diff = abs(doc_len - ideal_len)
        alignment = max(0, 1.0 - (diff / ideal_len))
        
        return alignment
    
    def _calculate_metadata_boost(self, metadata: Dict, query: str) -> float:
        """
        Calculate boost factor based on metadata
        
        Boost for:
        - Recent documents
        - High-confidence sources
        - Specific document types (how-to guides > general info)
        - Topic match
        """
        boost = 1.0
        
        # Source boost (zobot knowledge is authoritative)
        source = metadata.get("source", "")
        if "acebuddy_chatbot" in source or "zobot" in source:
            boost *= 1.15
        elif "official_docs" in source:
            boost *= 1.10
        
        # Document type boost
        doc_type = metadata.get("doc_type", "")
        query_lower = query.lower()
        
        if "how" in query_lower and "qa_pair" in doc_type:
            boost *= 1.10  # Q&A pairs are good for how-to questions
        elif "comprehensive" in doc_type:
            boost *= 1.05  # Comprehensive docs are generally good
        
        # Topic match boost
        topic = metadata.get("topic", "").lower()
        if topic and topic in query_lower:
            boost *= 1.20
        
        # Has links/resources boost
        if metadata.get("has_links", False):
            boost *= 1.05
        if metadata.get("has_articles", False):
            boost *= 1.05
        
        return boost
    
    def _ensure_diversity(
        self,
        documents: List[Dict],
        max_similar: int = 20
    ) -> List[Dict]:
        """
        Ensure diversity in results (avoid too many similar documents)
        Uses MMR-like approach (Maximal Marginal Relevance)
        """
        if len(documents) <= max_similar:
            return documents
        
        selected = [documents[0]]  # Start with top document
        
        for doc in documents[1:]:
            # Check diversity with already selected
            is_diverse = True
            doc_text = doc.get("text", "").lower()
            
            for selected_doc in selected:
                selected_text = selected_doc.get("text", "").lower()
                
                # Simple token-based similarity
                similarity = self._text_similarity(doc_text, selected_text)
                
                if similarity > self.diversity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                selected.append(doc)
            
            if len(selected) >= max_similar:
                break
        
        return selected
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple Jaccard similarity between two texts"""
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def _get_doc_id(self, doc: Dict) -> str:
        """Generate unique ID for document"""
        # Use text hash as ID
        text = doc.get("text", "")
        return str(hash(text))
    
    def hybrid_fusion(
        self,
        semantic_results: List[Dict],
        lexical_results: List[Dict],
        alpha: float = 0.7
    ) -> List[Dict]:
        """
        Fuse semantic and lexical search results
        
        Args:
            semantic_results: Results from vector similarity
            lexical_results: Results from keyword/BM25 search
            alpha: Weight for semantic (1-alpha for lexical)
        
        Returns:
            Fused results
        """
        doc_scores = defaultdict(float)
        doc_data = {}
        
        # Score semantic results
        for rank, doc in enumerate(semantic_results, start=1):
            doc_id = self._get_doc_id(doc)
            score = alpha * (1.0 / rank)
            doc_scores[doc_id] += score
            
            if doc_id not in doc_data:
                doc_data[doc_id] = doc
        
        # Score lexical results
        for rank, doc in enumerate(lexical_results, start=1):
            doc_id = self._get_doc_id(doc)
            score = (1.0 - alpha) * (1.0 / rank)
            doc_scores[doc_id] += score
            
            if doc_id not in doc_data:
                doc_data[doc_id] = doc
        
        # Sort by combined score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        fused_results = []
        for doc_id, score in sorted_docs:
            doc = doc_data[doc_id].copy()
            doc["hybrid_score"] = score
            doc["fusion_method"] = "hybrid_semantic_lexical"
            fused_results.append(doc)
        
        logger.debug(f"Hybrid fusion: {len(fused_results)} docs (alpha={alpha})")
        return fused_results
