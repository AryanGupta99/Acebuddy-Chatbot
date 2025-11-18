"""
Intent Classification Module
============================

Lightweight rule-based intent classifier for AceBuddy support queries.
Uses keyword matching to identify user intent for routing and analytics.
"""

import re
from typing import Dict, List, Tuple
from enum import Enum


class Intent(Enum):
    """Supported intent types"""
    PASSWORD_RESET = "password_reset"
    RDP_ISSUE = "rdp_issue"
    DISK_ISSUE = "disk_issue"
    USER_MANAGEMENT = "user_management"
    MONITOR_ISSUE = "monitor_issue"
    QUICKBOOKS = "quickbooks_issue"
    EMAIL_ISSUE = "email_issue"
    SERVER_PERFORMANCE = "server_performance"
    PRINTER_ISSUE = "printer_issue"
    NETWORK_ISSUE = "network_issue"
    SOFTWARE_INSTALL = "software_install"
    UNKNOWN = "unknown"


class IntentClassifier:
    """Rule-based intent classifier using keyword patterns"""
    
    # Intent patterns: (intent, keywords, weight_multiplier)
    INTENT_PATTERNS = {
        Intent.PASSWORD_RESET: [
            r'\b(password|passwd|pwd|login|signin|sign in|authentication|auth)\b',
            r'\b(reset|forgot|forgotten|recover|change|update)\b',
            r'\b(locked out|can\'t login|cannot login|access denied)\b',
        ],
        Intent.RDP_ISSUE: [
            r'\b(rdp|remote desktop|remote access|remote connection)\b',
            r'\b(can\'t connect|cannot connect|connection failed|connection refused)\b',
            r'\b(remote|terminal server|ts|rds)\b',
        ],
        Intent.DISK_ISSUE: [
            r'\b(disk|drive|storage|space|capacity)\b',
            r'\b(full|low space|out of space|no space|running out)\b',
            r'\b(cleanup|clean up|free up|delete|remove files)\b',
            r'\b(quota|limit|exceeded)\b',
        ],
        Intent.USER_MANAGEMENT: [
            r'\b(user|account|employee)\b',
            r'\b(add|create|new|setup|provision)\b',
            r'\b(remove|delete|disable|deactivate|terminate)\b',
            r'\b(permissions|access|rights|privileges)\b',
        ],
        Intent.MONITOR_ISSUE: [
            r'\b(monitor|display|screen|dual monitor|second screen)\b',
            r'\b(not working|doesn\'t work|blank|black screen|no signal)\b',
            r'\b(setup|configure|connect|detect)\b',
        ],
        Intent.QUICKBOOKS: [
            r'\b(quickbooks|qb|accounting software)\b',
            r'\b(error|issue|problem|not working|crash|freeze)\b',
            r'\b(company file|backup|restore|update)\b',
        ],
        Intent.EMAIL_ISSUE: [
            r'\b(email|e-mail|mail|outlook|inbox)\b',
            r'\b(not receiving|can\'t send|cannot send|not working)\b',
            r'\b(spam|junk|blocked|bounce|delivery failed)\b',
            r'\b(sync|synchronize|offline)\b',
        ],
        Intent.SERVER_PERFORMANCE: [
            r'\b(server|system|computer|pc)\b',
            r'\b(slow|sluggish|performance|lag|freeze|hang)\b',
            r'\b(cpu|memory|ram|resource|utilization)\b',
            r'\b(optimize|speed up|improve performance)\b',
        ],
        Intent.PRINTER_ISSUE: [
            r'\b(printer|print|printing)\b',
            r'\b(not working|doesn\'t work|error|jam|offline)\b',
            r'\b(queue|stuck|paused|cancel)\b',
            r'\b(driver|install|setup|configure)\b',
        ],
        Intent.NETWORK_ISSUE: [
            r'\b(network|internet|wifi|wi-fi|connection)\b',
            r'\b(slow|down|offline|disconnected|no connection)\b',
            r'\b(vpn|firewall|dns|ip address)\b',
        ],
        Intent.SOFTWARE_INSTALL: [
            r'\b(install|installation|setup|download)\b',
            r'\b(software|application|app|program|tool)\b',
            r'\b(license|activation|registration)\b',
        ],
    }
    
    def __init__(self, confidence_threshold: float = 0.3):
        """
        Initialize classifier
        
        Args:
            confidence_threshold: Minimum confidence to assign an intent
        """
        self.confidence_threshold = confidence_threshold
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[Intent, List[re.Pattern]]:
        """Compile regex patterns for efficiency"""
        compiled = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            compiled[intent] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in patterns
            ]
        return compiled
    
    def classify(self, query: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Classify query intent
        
        Args:
            query: User query text
            
        Returns:
            Tuple of (intent_name, confidence, all_scores)
            - intent_name: The predicted intent (string)
            - confidence: Confidence score (0-1)
            - all_scores: Dict of all intent scores for debugging
        """
        if not query or not query.strip():
            return Intent.UNKNOWN.value, 0.0, {}
        
        query_lower = query.lower()
        scores = {}
        
        # Score each intent
        for intent, patterns in self.compiled_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if pattern.search(query_lower):
                    matches += 1
                    score += 1.0
            
            # Normalize by number of patterns for this intent
            if patterns:
                scores[intent.value] = score / len(patterns)
        
        # Get best intent
        if not scores:
            return Intent.UNKNOWN.value, 0.0, {}
        
        best_intent = max(scores, key=scores.get)
        best_confidence = scores[best_intent]
        
        # Apply threshold
        if best_confidence < self.confidence_threshold:
            return Intent.UNKNOWN.value, best_confidence, scores
        
        return best_intent, best_confidence, scores
    
    def classify_batch(self, queries: List[str]) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Classify multiple queries
        
        Args:
            queries: List of query strings
            
        Returns:
            List of (intent, confidence, scores) tuples
        """
        return [self.classify(query) for query in queries]
    
    def get_intent_keywords(self, intent: str) -> List[str]:
        """Get keywords associated with an intent for explanation"""
        try:
            intent_enum = Intent(intent)
            patterns = self.INTENT_PATTERNS.get(intent_enum, [])
            # Extract human-readable keywords from regex patterns
            keywords = []
            for pattern in patterns:
                # Simple extraction - remove regex special chars
                cleaned = re.sub(r'[\\()|\[\]{}^$.*+?]', '', pattern)
                cleaned = cleaned.replace(r'\b', '').strip()
                if cleaned:
                    keywords.append(cleaned)
            return keywords
        except ValueError:
            return []


# Global classifier instance (singleton pattern)
_classifier_instance = None


def get_classifier() -> IntentClassifier:
    """Get or create global classifier instance"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier()
    return _classifier_instance


def classify_query(query: str) -> Tuple[str, float]:
    """
    Convenience function to classify a single query
    
    Args:
        query: User query text
        
    Returns:
        Tuple of (intent_name, confidence)
    """
    classifier = get_classifier()
    intent, confidence, _ = classifier.classify(query)
    return intent, confidence


# Example usage and testing
if __name__ == "__main__":
    classifier = IntentClassifier()
    
    test_queries = [
        "How do I reset my password?",
        "I can't connect to RDP",
        "My disk is full, how do I clean it up?",
        "How do I add a new user?",
        "My monitor isn't working",
        "QuickBooks is showing an error",
        "I'm not receiving emails",
        "The server is very slow",
        "Printer is jammed",
        "How do I install Microsoft Office?",
        "The internet is down",
        "What is the weather today?",  # Should be UNKNOWN
    ]
    
    print("Intent Classification Test Results")
    print("=" * 70)
    
    for query in test_queries:
        intent, confidence, all_scores = classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {intent}")
        print(f"Confidence: {confidence:.2f}")
        
        # Show top 3 scores
        if all_scores:
            top_3 = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"Top scores: {', '.join([f'{i}={s:.2f}' for i, s in top_3])}")
    
    print("\n" + "=" * 70)
    print("Test complete!")
