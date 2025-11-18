"""
Analytics and Monitoring Module
==============================

Track query patterns, performance metrics, and system health.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    """Track and analyze chatbot usage and performance"""
    
    def __init__(self, persist_path: Optional[str] = None):
        self.persist_path = Path(persist_path) if persist_path else None
        
        # Metrics storage
        self.query_history: List[Dict] = []
        self.intent_distribution = Counter()
        self.topic_distribution = Counter()
        self.response_times: List[float] = []
        self.confidence_scores: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.fallback_triggers = 0
        self.total_queries = 0
        
        # Session tracking
        self.active_sessions = {}
        self.completed_sessions = []
        
        # Load persisted data
        if self.persist_path and self.persist_path.exists():
            self._load_analytics()
    
    def track_query(
        self,
        query: str,
        intent: str,
        response_time_ms: float,
        confidence: float,
        cache_hit: bool,
        fallback_used: bool,
        topics: List[str] = None,
        session_id: Optional[str] = None
    ):
        """Track a single query"""
        self.total_queries += 1
        
        # Record query
        self.query_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "intent": intent,
            "response_time_ms": response_time_ms,
            "confidence": confidence,
            "cache_hit": cache_hit,
            "fallback_used": fallback_used,
            "topics": topics or [],
            "session_id": session_id
        })
        
        # Update counters
        self.intent_distribution[intent] += 1
        self.response_times.append(response_time_ms)
        self.confidence_scores.append(confidence)
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        if fallback_used:
            self.fallback_triggers += 1
        
        if topics:
            for topic in topics:
                self.topic_distribution[topic] += 1
        
        # Update session tracking
        if session_id:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    "start_time": datetime.now(),
                    "queries": [],
                    "intents": []
                }
            
            self.active_sessions[session_id]["queries"].append(query)
            self.active_sessions[session_id]["intents"].append(intent)
    
    def get_summary_stats(self, time_window_hours: Optional[int] = None) -> Dict[str, Any]:
        """Get summary statistics"""
        
        # Filter by time window if specified
        queries = self.query_history
        if time_window_hours:
            cutoff = datetime.now() - timedelta(hours=time_window_hours)
            queries = [
                q for q in queries
                if datetime.fromisoformat(q["timestamp"]) > cutoff
            ]
        
        if not queries:
            return {"error": "No queries in specified time window"}
        
        # Calculate metrics
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        avg_confidence = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0
        
        cache_hit_rate = (self.cache_hits / self.total_queries * 100) if self.total_queries > 0 else 0
        fallback_rate = (self.fallback_triggers / self.total_queries * 100) if self.total_queries > 0 else 0
        
        return {
            "total_queries": len(queries),
            "time_window_hours": time_window_hours or "all_time",
            "avg_response_time_ms": round(avg_response_time, 2),
            "avg_confidence": round(avg_confidence, 3),
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "fallback_rate_percent": round(fallback_rate, 2),
            "top_intents": self.intent_distribution.most_common(5),
            "top_topics": self.topic_distribution.most_common(5),
            "active_sessions": len(self.active_sessions),
            "completed_sessions": len(self.completed_sessions)
        }
    
    def get_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns"""
        
        # Time-based patterns
        hour_distribution = Counter()
        day_distribution = Counter()
        
        for query in self.query_history:
            timestamp = datetime.fromisoformat(query["timestamp"])
            hour_distribution[timestamp.hour] += 1
            day_distribution[timestamp.strftime("%A")] += 1
        
        # Intent transitions (what users ask after)
        intent_transitions = defaultdict(Counter)
        
        for i in range(len(self.query_history) - 1):
            current_intent = self.query_history[i]["intent"]
            next_intent = self.query_history[i + 1]["intent"]
            intent_transitions[current_intent][next_intent] += 1
        
        # Common query phrases
        all_queries = [q["query"].lower() for q in self.query_history]
        common_words = Counter()
        
        for query in all_queries:
            words = query.split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    common_words[word] += 1
        
        return {
            "peak_hours": hour_distribution.most_common(3),
            "busiest_days": day_distribution.most_common(3),
            "intent_transitions": dict(intent_transitions),
            "common_terms": common_words.most_common(10)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        
        if not self.response_times:
            return {"error": "No performance data available"}
        
        # Calculate percentiles
        sorted_times = sorted(self.response_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Confidence distribution
        low_confidence = sum(1 for c in self.confidence_scores if c < 0.3)
        medium_confidence = sum(1 for c in self.confidence_scores if 0.3 <= c < 0.6)
        high_confidence = sum(1 for c in self.confidence_scores if c >= 0.6)
        
        return {
            "response_time_ms": {
                "min": round(min(self.response_times), 2),
                "max": round(max(self.response_times), 2),
                "avg": round(sum(self.response_times) / len(self.response_times), 2),
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2)
            },
            "confidence_distribution": {
                "low": low_confidence,
                "medium": medium_confidence,
                "high": high_confidence
            },
            "cache_performance": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate_percent": round(self.cache_hits / self.total_queries * 100, 2) if self.total_queries > 0 else 0
            },
            "fallback_triggers": self.fallback_triggers
        }
    
    def get_session_analytics(self) -> Dict[str, Any]:
        """Get session-based analytics"""
        
        all_sessions = list(self.active_sessions.values()) + self.completed_sessions
        
        if not all_sessions:
            return {"error": "No session data available"}
        
        # Calculate session metrics
        session_lengths = []
        queries_per_session = []
        
        for session in all_sessions:
            queries_per_session.append(len(session["queries"]))
            
            if "end_time" in session:
                duration = (session["end_time"] - session["start_time"]).total_seconds()
                session_lengths.append(duration)
        
        avg_queries = sum(queries_per_session) / len(queries_per_session) if queries_per_session else 0
        avg_duration = sum(session_lengths) / len(session_lengths) if session_lengths else 0
        
        return {
            "total_sessions": len(all_sessions),
            "active_sessions": len(self.active_sessions),
            "avg_queries_per_session": round(avg_queries, 2),
            "avg_session_duration_seconds": round(avg_duration, 2),
            "max_queries_in_session": max(queries_per_session) if queries_per_session else 0
        }
    
    def end_session(self, session_id: str):
        """Mark session as completed"""
        if session_id in self.active_sessions:
            session = self.active_sessions.pop(session_id)
            session["end_time"] = datetime.now()
            self.completed_sessions.append(session)
    
    def _save_analytics(self):
        """Persist analytics data"""
        if not self.persist_path:
            return
        
        data = {
            "query_history": self.query_history[-1000:],  # Keep last 1000
            "intent_distribution": dict(self.intent_distribution),
            "topic_distribution": dict(self.topic_distribution),
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "fallback_triggers": self.fallback_triggers
        }
        
        self.persist_path.write_text(json.dumps(data, indent=2))
        logger.debug(f"Analytics saved to {self.persist_path}")
    
    def _load_analytics(self):
        """Load persisted analytics data"""
        try:
            data = json.loads(self.persist_path.read_text())
            
            self.query_history = data.get("query_history", [])
            self.intent_distribution = Counter(data.get("intent_distribution", {}))
            self.topic_distribution = Counter(data.get("topic_distribution", {}))
            self.total_queries = data.get("total_queries", 0)
            self.cache_hits = data.get("cache_hits", 0)
            self.cache_misses = data.get("cache_misses", 0)
            self.fallback_triggers = data.get("fallback_triggers", 0)
            
            logger.info(f"Analytics loaded from {self.persist_path}")
        except Exception as e:
            logger.warning(f"Could not load analytics: {e}")
