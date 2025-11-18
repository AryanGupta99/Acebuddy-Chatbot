"""
Query Enhancement Module
========================

Improves queries through rewriting, expansion, and optimization
for better semantic search results.
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class EnhancedQuery:
    """Enhanced query with multiple variations"""
    original: str
    rewritten: str
    expanded: List[str]
    keywords: List[str]
    boost_terms: List[str]


class QueryEnhancer:
    """Enhances queries for better retrieval"""
    
    # Common stopwords to remove
    STOPWORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
        "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
        'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
        'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
        'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
        'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
        'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
        'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once'
    }
    
    # Synonym expansions for common IT terms
    SYNONYMS = {
        'password': ['passwd', 'pwd', 'credentials', 'login', 'authentication'],
        'reset': ['change', 'update', 'modify', 'recover'],
        'rdp': ['remote desktop', 'remote access', 'terminal server'],
        'disk': ['drive', 'storage', 'space', 'capacity'],
        'full': ['out of space', 'low space', 'no space'],
        'email': ['mail', 'e-mail', 'outlook', 'inbox'],
        'server': ['machine', 'system', 'computer'],
        'slow': ['sluggish', 'performance', 'lag', 'freeze'],
        'error': ['issue', 'problem', 'failure', 'bug'],
        'install': ['setup', 'installation', 'deployment'],
        'user': ['account', 'employee', 'person'],
        'printer': ['printing', 'print'],
        'network': ['internet', 'connection', 'connectivity'],
        'monitor': ['display', 'screen'],
    }
    
    # Question normalization patterns
    QUESTION_PATTERNS = [
        (r'^how (do|can) i\s+', 'steps to '),
        (r'^what (is|are)\s+', ''),
        (r'^why (is|are|does|do)\s+', 'reason for '),
        (r'^when (should|do)\s+', 'timing for '),
        (r'^where (is|are|can)\s+', 'location of '),
    ]
    
    def enhance(self, query: str) -> EnhancedQuery:
        """
        Enhance query with multiple variations
        
        Args:
            query: Original user query
            
        Returns:
            EnhancedQuery with multiple variations
        """
        # Extract keywords
        keywords = self._extract_keywords(query)
        
        # Rewrite query
        rewritten = self._rewrite_query(query, keywords)
        
        # Expand with synonyms
        expanded = self._expand_query(query, keywords)
        
        # Extract boost terms (important technical terms)
        boost_terms = self._extract_boost_terms(query)
        
        return EnhancedQuery(
            original=query,
            rewritten=rewritten,
            expanded=expanded,
            keywords=keywords,
            boost_terms=boost_terms
        )
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Lowercase and tokenize
        query_lower = query.lower()
        tokens = re.findall(r'\b\w+\b', query_lower)
        
        # Remove stopwords
        keywords = [t for t in tokens if t not in self.STOPWORDS and len(t) > 2]
        
        return keywords
    
    def _rewrite_query(self, query: str, keywords: List[str]) -> str:
        """Rewrite query to be more search-friendly"""
        rewritten = query.lower()
        
        # Apply question normalization patterns
        for pattern, replacement in self.QUESTION_PATTERNS:
            rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
        
        # Remove unnecessary punctuation
        rewritten = re.sub(r'[?!.]+$', '', rewritten)
        
        # If query is very short, just use keywords
        if len(keywords) <= 3:
            rewritten = ' '.join(keywords)
        
        return rewritten.strip()
    
    def _expand_query(self, query: str, keywords: List[str]) -> List[str]:
        """Expand query with synonyms and variations"""
        expanded = [query]
        query_lower = query.lower()
        
        # Find matching synonyms in query
        for term, synonyms in self.SYNONYMS.items():
            if term in query_lower:
                # Create variations with each synonym
                for syn in synonyms[:2]:  # Limit to 2 synonyms per term
                    variation = re.sub(
                        r'\b' + re.escape(term) + r'\b',
                        syn,
                        query_lower,
                        flags=re.IGNORECASE
                    )
                    if variation != query_lower:
                        expanded.append(variation)
        
        # Add keyword-only variation
        if len(keywords) > 1:
            expanded.append(' '.join(keywords))
        
        # Remove duplicates and limit
        expanded = list(dict.fromkeys(expanded))  # Preserve order
        return expanded[:5]  # Max 5 variations
    
    def _extract_boost_terms(self, query: str) -> List[str]:
        """Extract terms that should be boosted in search"""
        boost_terms = []
        query_lower = query.lower()
        
        # Technical terms that should be weighted higher
        tech_terms = [
            'password', 'rdp', 'remote desktop', 'disk', 'drive', 'email',
            'server', 'printer', 'network', 'monitor', 'quickbooks',
            'backup', 'restore', 'install', 'update', 'error', 'crash'
        ]
        
        for term in tech_terms:
            if term in query_lower:
                boost_terms.append(term)
        
        # Extract quoted phrases (exact matches)
        quoted = re.findall(r'"([^"]+)"', query)
        boost_terms.extend(quoted)
        
        return boost_terms
    
    def get_search_queries(self, query: str, top_k: int = 3) -> List[str]:
        """
        Get multiple search query variations for retrieval
        
        Args:
            query: Original query
            top_k: Number of query variations to return
            
        Returns:
            List of query strings to search with
        """
        enhanced = self.enhance(query)
        
        queries = [enhanced.original]
        
        # Add rewritten if different
        if enhanced.rewritten != enhanced.original:
            queries.append(enhanced.rewritten)
        
        # Add expanded variations
        queries.extend(enhanced.expanded)
        
        # Remove duplicates and limit
        unique_queries = list(dict.fromkeys(queries))
        return unique_queries[:top_k]


class ResponseValidator:
    """Validates LLM responses for quality"""
    
    def __init__(self, min_length: int = 20, max_length: int = 2000):
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, response: str, context_confidence: float) -> Tuple[bool, float, str]:
        """
        Validate response quality
        
        Returns:
            (is_valid, quality_score, reason)
        """
        # Check length
        if len(response) < self.min_length:
            return False, 0.2, "Response too short"
        
        if len(response) > self.max_length:
            return False, 0.3, "Response too long"
        
        # Check for common failure patterns
        failure_patterns = [
            (r"i don'?t (have|know)", 0.1, "Insufficient information"),
            (r"(sorry|apologize).+(can'?t|cannot|unable)", 0.2, "Unable to answer"),
            (r"^(no|not available|unavailable)", 0.1, "Not available"),
        ]
        
        response_lower = response.lower()
        for pattern, penalty_score, reason in failure_patterns:
            if re.search(pattern, response_lower):
                # Still valid, but low quality
                return True, penalty_score, reason
        
        # Calculate quality score
        quality_score = self._calculate_quality(response, context_confidence)
        
        if quality_score < 0.3:
            return False, quality_score, "Low quality response"
        
        return True, quality_score, "Valid"
    
    def _calculate_quality(self, response: str, context_confidence: float) -> float:
        """Calculate response quality score (0-1)"""
        score = 0.5  # Base score
        
        # Factor 1: Context confidence (40% weight)
        score += context_confidence * 0.4
        
        # Factor 2: Length appropriateness (20% weight)
        length_score = min(len(response) / 500, 1.0)  # Optimal around 500 chars
        score += length_score * 0.2
        
        # Factor 3: Structure (20% weight)
        has_sentences = len(re.findall(r'[.!?]', response)) > 1
        has_lists = 'steps' in response.lower() or bool(re.search(r'\d+\.', response))
        structure_score = (has_sentences + has_lists) / 2
        score += structure_score * 0.2
        
        # Factor 4: Technical terms (20% weight)
        tech_terms = ['password', 'system', 'server', 'file', 'user', 'settings', 'configuration']
        tech_score = sum(1 for term in tech_terms if term in response.lower()) / len(tech_terms)
        score += tech_score * 0.2
        
        return min(max(score, 0.0), 1.0)


# Global instances
_query_enhancer = None
_response_validator = None


def get_query_enhancer() -> QueryEnhancer:
    """Get or create global query enhancer"""
    global _query_enhancer
    if _query_enhancer is None:
        _query_enhancer = QueryEnhancer()
    return _query_enhancer


def get_response_validator() -> ResponseValidator:
    """Get or create global response validator"""
    global _response_validator
    if _response_validator is None:
        _response_validator = ResponseValidator()
    return _response_validator


if __name__ == "__main__":
    # Test query enhancement
    enhancer = QueryEnhancer()
    
    test_queries = [
        "How do I reset my password?",
        "I can't connect to RDP",
        "My disk is full",
        "Email not working",
    ]
    
    for query in test_queries:
        print(f"\nOriginal: {query}")
        enhanced = enhancer.enhance(query)
        print(f"Rewritten: {enhanced.rewritten}")
        print(f"Keywords: {enhanced.keywords}")
        print(f"Expanded: {enhanced.expanded[:2]}")
        print(f"Boost terms: {enhanced.boost_terms}")
        
        search_queries = enhancer.get_search_queries(query, top_k=3)
        print(f"Search queries: {search_queries}")
    
    # Test response validation
    validator = ResponseValidator()
    
    test_responses = [
        ("To reset your password, follow these steps...", 0.9),
        ("I don't have enough information", 0.3),
        ("Yes", 0.8),
        ("Sorry, I can't help with that", 0.5),
    ]
    
    print("\n" + "="*70)
    print("Response Validation:")
    for response, confidence in test_responses:
        valid, score, reason = validator.validate(response, confidence)
        print(f"\nResponse: {response[:50]}...")
        print(f"Valid: {valid}, Quality: {score:.2f}, Reason: {reason}")
