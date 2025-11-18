#!/usr/bin/env python3
"""
Complete RAG Chatbot Test with Ollama
Tests multiple queries and shows responses
"""
import requests
import json
import time

def test_chatbot():
    base_url = "http://127.0.0.1:8000"
    
    # Test queries covering different domains
    queries = [
        ("How do I reset my password?", "Password Management"),
        ("How do I troubleshoot RDP connection issues?", "RDP Issues"),
        ("How do I add a new user to my system?", "User Management"),
        ("What should I do if my server is running slow?", "Server Performance"),
        ("How do I set up a printer?", "Printer Setup"),
    ]
    
    print("\n" + "="*80)
    print("🚀 ACEBUDDY RAG CHATBOT TEST WITH OLLAMA")
    print("="*80)
    print(f"Server: {base_url}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = []
    
    for i, (query, domain) in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {domain}")
        print("-" * 80)
        print(f"📝 Query: {query}")
        
        try:
            start_time = time.time()
            
            # Make request to chatbot
            response = requests.post(
                f"{base_url}/chat",
                json={"query": query, "session_id": f"test_{i}"},
                timeout=120  # Long timeout for Ollama
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response details
                answer = data.get('answer', '')
                confidence = data.get('confidence', 0)
                intent = data.get('intent', 'unknown')
                source = data.get('source', 'ollama')
                
                print(f"✅ Status: SUCCESS")
                print(f"⏱️  Response Time: {elapsed_ms:.0f}ms")
                print(f"🤖 Source: {source}")
                print(f"🎯 Intent: {intent}")
                print(f"📊 Confidence: {confidence:.1f}%")
                print(f"\n💬 Response:")
                print("-" * 80)
                print(answer[:800])
                if len(answer) > 800:
                    print("... (truncated)")
                print("-" * 80)
                
                results.append({
                    'query': query,
                    'domain': domain,
                    'status': 'SUCCESS',
                    'time_ms': elapsed_ms,
                    'confidence': confidence
                })
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                results.append({
                    'query': query,
                    'domain': domain,
                    'status': 'FAILED',
                    'error': f"HTTP {response.status_code}"
                })
        
        except requests.exceptions.Timeout:
            print(f"❌ Timeout: Request took longer than 120 seconds")
            results.append({
                'query': query,
                'domain': domain,
                'status': 'TIMEOUT'
            })
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error: Cannot reach server at {base_url}")
            print("Make sure the server is running!")
            results.append({
                'query': query,
                'domain': domain,
                'status': 'CONNECTION_ERROR'
            })
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
            results.append({
                'query': query,
                'domain': domain,
                'status': 'ERROR',
                'error': str(e)
            })
        
        time.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total}")
    print(f"Avg Response Time: {sum(r.get('time_ms', 0) for r in results if r['status'] == 'SUCCESS') / max(1, successful):.0f}ms")
    
    if successful == total:
        print("\n🎉 ALL TESTS PASSED! Ollama integration is working perfectly!")
    
    print("="*80 + "\n")
    
    return successful == total

if __name__ == "__main__":
    success = test_chatbot()
    exit(0 if success else 1)
