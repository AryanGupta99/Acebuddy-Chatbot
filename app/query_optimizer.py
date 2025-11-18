"""
Advanced Query Optimization for RAG
==================================

Implements:
- Multi-query generation for better retrieval
- Query decomposition for complex questions
- HyDE (Hypothetical Document Embeddings)
- Query expansion with synonyms
- Intent-aware query rewriting
"""

import logging
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Optimize queries for better RAG retrieval"""
    
    def __init__(self, ollama_client=None):
        self.ollama_client = ollama_client
        
        # IT support synonyms and expansions
        self.synonym_map = {
            "reset": ["reset", "change", "update", "restore"],
            "password": ["password", "credentials", "login", "authentication"],
            "server": ["server", "machine", "instance", "VM"],
            "upgrade": ["upgrade", "update", "install", "deploy"],
            "issue": ["issue", "problem", "error", "trouble"],
            "slow": ["slow", "sluggish", "laggy", "performance"],
            "connection": ["connection", "connectivity", "access", "link"],
            "storage": ["storage", "disk", "space", "capacity"],
            "memory": ["memory", "RAM", "resources"],
            "backup": ["backup", "snapshot", "restore point"],
        }
    
    async def optimize_query(
        self,
        query: str,
        intent: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Optimize query using multiple techniques
        
        Returns:
            {
                "original": str,
                "rewritten": str,
                "multi_queries": List[str],
                "expanded": str,
                "decomposed": List[str],
                "hyde_document": str
            }
        """
        result = {
            "original": query,
            "rewritten": query,
            "multi_queries": [query],
            "expanded": query,
            "decomposed": [],
            "hyde_document": ""
        }
        
        # 1. Context-aware rewriting (if conversation history)
        if conversation_history and len(conversation_history) > 0:
            result["rewritten"] = self._add_conversation_context(query, conversation_history)
        
        # 2. Multi-query generation (3-5 variations)
        result["multi_queries"] = await self._generate_multi_queries(result["rewritten"], intent)
        
        # 3. Query expansion with synonyms
        result["expanded"] = self._expand_query(result["rewritten"])
        
        # 4. Query decomposition for complex questions
        if self._is_complex_query(query):
            result["decomposed"] = self._decompose_query(result["rewritten"])
        
        # 5. HyDE - Generate hypothetical answer
        if self.ollama_client:
            result["hyde_document"] = await self._generate_hyde_document(result["rewritten"])
        
        logger.debug(f"Query optimization: {len(result['multi_queries'])} variations, "
                    f"{len(result['decomposed'])} sub-queries")
        
        return result
    
    def _add_conversation_context(
        self,
        query: str,
        conversation_history: List[Dict]
    ) -> str:
        """Add conversation context to ambiguous queries"""
        # Check if query is ambiguous (pronouns, no specific nouns)
        ambiguous_indicators = ["it", "this", "that", "the issue", "the problem"]
        
        is_ambiguous = any(indicator in query.lower() for indicator in ambiguous_indicators)
        
        if not is_ambiguous:
            return query
        
        # Get last user message context
        last_topics = []
        for msg in reversed(conversation_history[-4:]):
            if msg.get("role") == "user":
                # Extract key entities
                entities = self._extract_entities(msg.get("content", ""))
                last_topics.extend(entities)
                if last_topics:
                    break
        
        if last_topics:
            # Add context to query
            context = " ".join(last_topics[:2])
            rewritten = f"{query} (regarding {context})"
            logger.debug(f"Added context: {query} -> {rewritten}")
            return rewritten
        
        return query
    
    async def _generate_multi_queries(
        self,
        query: str,
        intent: Optional[str]
    ) -> List[str]:
        """Generate multiple query variations"""
        queries = [query]
        
        # Template-based variations
        if intent == "how_to":
            queries.extend([
                f"How to {query.replace('how to', '').replace('how do i', '').strip()}",
                f"Steps to {query.replace('how to', '').replace('how do i', '').strip()}",
                f"Guide for {query.replace('how to', '').replace('how do i', '').strip()}"
            ])
        elif intent == "troubleshooting":
            queries.extend([
                f"Troubleshoot {query}",
                f"Fix {query}",
                f"Resolve {query}"
            ])
        else:
            # Generic variations
            queries.extend([
                f"Information about {query}",
                f"Details on {query}",
                f"Help with {query}"
            ])
        
        # LLM-based generation (if available)
        if self.ollama_client:
            try:
                llm_queries = await self._generate_llm_variations(query)
                queries.extend(llm_queries)
            except Exception as e:
                logger.warning(f"LLM query generation failed: {e}")
        
        # Deduplicate and limit
        unique_queries = []
        seen = set()
        for q in queries:
            q_lower = q.lower().strip()
            if q_lower not in seen and len(q_lower) > 5:
                unique_queries.append(q)
                seen.add(q_lower)
        
        return unique_queries[:5]  # Max 5 variations
    
    async def _generate_llm_variations(self, query: str) -> List[str]:
        """Generate query variations using LLM"""
        prompt = f"""Generate 2 alternative ways to ask this question. Keep them concise and focused.

Original: {query}

Alternative 1:
Alternative 2:"""
        
        try:
            response = await self.ollama_client.chat(
                model="mistral",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.get("message", {}).get("content", "")
            
            # Extract alternatives
            alternatives = []
            for line in content.split("\n"):
                if "Alternative" in line or line.strip().startswith(("1.", "2.", "-", "*")):
                    # Clean up the line
                    cleaned = re.sub(r'^(Alternative \d:|[\d\-\*\.]+)', '', line).strip()
                    if cleaned and len(cleaned) > 5:
                        alternatives.append(cleaned)
            
            return alternatives[:2]
        except Exception as e:
            logger.warning(f"LLM variation generation error: {e}")
            return []
    
    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms"""
        words = query.lower().split()
        expanded_words = []
        
        for word in words:
            # Check if word has synonyms
            if word in self.synonym_map:
                # Add original + top synonym
                expanded_words.append(word)
                expanded_words.extend(self.synonym_map[word][:1])
            else:
                expanded_words.append(word)
        
        return " ".join(expanded_words)
    
    def _is_complex_query(self, query: str) -> bool:
        """Check if query is complex and needs decomposition"""
        complexity_indicators = [
            " and ",
            " then ",
            " after ",
            " while ",
            " also ",
            "multiple",
            "several",
            "step",
            "process"
        ]
        
        word_count = len(query.split())
        has_indicators = any(ind in query.lower() for ind in complexity_indicators)
        
        return word_count > 15 or has_indicators
    
    def _decompose_query(self, query: str) -> List[str]:
        """Decompose complex query into sub-queries"""
        sub_queries = []
        
        # Split on conjunctions
        parts = re.split(r'\band\b|\bthen\b|\bafter\b', query, flags=re.IGNORECASE)
        
        for part in parts:
            part = part.strip()
            if len(part) > 10:  # Meaningful length
                sub_queries.append(part)
        
        # If no splits, try to identify multiple questions
        if len(sub_queries) <= 1:
            # Check for multiple question marks or numbered steps
            if query.count("?") > 1:
                sub_queries = [q.strip() + "?" for q in query.split("?") if q.strip()]
            elif any(marker in query for marker in ["1.", "2.", "3."]):
                sub_queries = [
                    line.strip()
                    for line in query.split("\n")
                    if any(line.strip().startswith(f"{i}.") for i in range(1, 10))
                ]
        
        return sub_queries if len(sub_queries) > 1 else []
    
    async def _generate_hyde_document(self, query: str) -> str:
        """
        Generate hypothetical document (HyDE technique)
        Creates a fake but plausible answer to embed and retrieve similar real docs
        """
        prompt = f"""Generate a brief, factual answer to this IT support question. 
Keep it concise (2-3 sentences) and professional.

Question: {query}

Answer:"""
        
        try:
            response = await self.ollama_client.chat(
                model="mistral",
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3}  # Lower temperature for factual generation
            )
            
            hyde_doc = response.get("message", {}).get("content", "").strip()
            logger.debug(f"Generated HyDE document: {hyde_doc[:100]}...")
            return hyde_doc
        except Exception as e:
            logger.warning(f"HyDE generation error: {e}")
            return ""
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities from text (simple rule-based)"""
        entities = []
        
        # Common IT entities
        it_patterns = [
            r'\b(QuickBooks|Sage|ProSeries|Drake|Lacerte|ATX|Office 365)\b',
            r'\b(server|VM|instance|machine)\b',
            r'\b(password|credentials|login)\b',
            r'\b(disk|storage|memory|RAM)\b',
            r'\b(printer|scanner|UniPrint)\b',
            r'\b(RDP|connection|access)\b'
        ]
        
        for pattern in it_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))[:5]  # Max 5 entities
    
    def get_best_query_for_retrieval(
        self,
        optimization_result: Dict[str, Any]
    ) -> str:
        """
        Select best query variant for retrieval
        
        Strategy:
        - Use expanded query for better recall
        - Fall back to rewritten if expansion too long
        - Use original if all else fails
        """
        expanded = optimization_result.get("expanded", "")
        rewritten = optimization_result.get("rewritten", "")
        original = optimization_result.get("original", "")
        
        # Prefer expanded, but not if too long (>200 chars)
        if expanded and len(expanded) < 200:
            return expanded
        
        return rewritten or original
