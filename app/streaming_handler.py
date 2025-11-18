"""
Streaming Response Handler for Real-time LLM Output
==================================================

Implements Server-Sent Events (SSE) streaming for real-time responses,
improving perceived performance and user experience.
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class StreamingHandler:
    """Handle streaming responses for real-time LLM output"""
    
    def __init__(self):
        self.active_streams = {}
    
    async def stream_chat_response(
        self,
        query: str,
        context_docs: List[Dict],
        conversation_history: List[Dict],
        ollama_client,
        model: str = "mistral"
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response with SSE format
        
        Yields JSON events:
        - data: {"type": "start", "timestamp": "..."}
        - data: {"type": "context", "count": 3, "sources": [...]}
        - data: {"type": "token", "content": "Hello"}
        - data: {"type": "metadata", "confidence": 0.85}
        - data: {"type": "done", "total_tokens": 150}
        """
        stream_id = f"stream_{int(time.time()*1000)}"
        self.active_streams[stream_id] = {"start_time": datetime.now(), "status": "active"}
        
        try:
            # 1. Send start event
            yield self._format_sse({
                "type": "start",
                "stream_id": stream_id,
                "timestamp": datetime.now().isoformat(),
                "query": query
            })
            
            # 2. Send context information
            sources = [
                {
                    "title": doc.get("metadata", {}).get("title", "Unknown"),
                    "source": doc.get("metadata", {}).get("source", "kb"),
                    "relevance": doc.get("distance", 0)
                }
                for doc in context_docs[:3]
            ]
            
            yield self._format_sse({
                "type": "context",
                "count": len(context_docs),
                "sources": sources
            })
            
            # 3. Build prompt
            prompt = self._build_streaming_prompt(query, context_docs, conversation_history)
            
            # 4. Stream tokens from Ollama
            token_count = 0
            full_response = []
            
            async for chunk in self._stream_from_ollama(ollama_client, model, prompt):
                if chunk:
                    token_count += 1
                    full_response.append(chunk)
                    
                    yield self._format_sse({
                        "type": "token",
                        "content": chunk,
                        "token_num": token_count
                    })
            
            # 5. Send metadata
            complete_response = "".join(full_response)
            confidence = self._calculate_confidence(complete_response, context_docs)
            
            yield self._format_sse({
                "type": "metadata",
                "confidence": confidence,
                "sources_used": len(sources),
                "response_length": len(complete_response)
            })
            
            # 6. Send done event
            yield self._format_sse({
                "type": "done",
                "stream_id": stream_id,
                "total_tokens": token_count,
                "duration_ms": (datetime.now() - self.active_streams[stream_id]["start_time"]).total_seconds() * 1000
            })
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield self._format_sse({
                "type": "error",
                "message": str(e)
            })
        finally:
            self.active_streams.pop(stream_id, None)
    
    async def _stream_from_ollama(
        self,
        ollama_client,
        model: str,
        prompt: str
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama API"""
        try:
            # Use Ollama's streaming API
            response = await ollama_client.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            async for chunk in response:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
                    
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            # Fallback to non-streaming
            try:
                response = await ollama_client.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Simulate streaming by yielding words
                content = response.get("message", {}).get("content", "")
                words = content.split()
                for word in words:
                    yield word + " "
                    await asyncio.sleep(0.05)  # Simulate streaming delay
                    
            except Exception as e2:
                logger.error(f"Fallback streaming error: {e2}")
                yield f"Error generating response: {str(e2)}"
    
    def _build_streaming_prompt(
        self,
        query: str,
        context_docs: List[Dict],
        conversation_history: List[Dict]
    ) -> str:
        """Build optimized prompt for streaming"""
        context_text = "\n\n".join([
            f"[Source {i+1}] {doc.get('text', '')}"
            for i, doc in enumerate(context_docs[:3])
        ])
        
        history_text = ""
        if conversation_history:
            recent_history = conversation_history[-4:]  # Last 2 exchanges
            history_text = "Previous conversation:\n"
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_text += f"{role.capitalize()}: {content}\n"
        
        prompt = f"""You are Ace Buddy, a professional IT support assistant for Ace Cloud Hosting.

{history_text}

Context from knowledge base:
{context_text}

Current question: {query}

Instructions:
- Provide a clear, concise answer based on the context
- Be professional and helpful
- If the context doesn't fully answer the question, acknowledge it
- Keep responses focused and actionable
- Format with bullet points or steps when appropriate

Answer:"""
        
        return prompt
    
    def _calculate_confidence(self, response: str, context_docs: List[Dict]) -> float:
        """Calculate response confidence score"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if response is substantial
        if len(response) > 50:
            confidence += 0.1
        
        # Higher confidence with more relevant context
        if len(context_docs) >= 3:
            confidence += 0.2
        
        # Check if response references context
        if any(keyword in response.lower() for keyword in ["according to", "as mentioned", "based on"]):
            confidence += 0.1
        
        # Check if response is not too vague
        if not any(word in response.lower() for word in ["maybe", "might", "possibly", "not sure"]):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _format_sse(self, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event"""
        json_data = json.dumps(data)
        return f"data: {json_data}\n\n"
    
    def get_active_streams(self) -> Dict:
        """Get information about active streams"""
        return {
            stream_id: {
                "start_time": info["start_time"].isoformat(),
                "status": info["status"],
                "duration_seconds": (datetime.now() - info["start_time"]).total_seconds()
            }
            for stream_id, info in self.active_streams.items()
        }
