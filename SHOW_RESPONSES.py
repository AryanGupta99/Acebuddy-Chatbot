#!/usr/bin/env python3
"""
Complete Chatbot Test with Ollama - Shows responses and performance
"""
import requests
import json
import time
import sys

def test_chatbot():
    print("\n" + "="*90)
    print(" "*20 + "🚀 ACEBUDDY RAG CHATBOT - COMPLETE TEST WITH OLLAMA")
    print("="*90)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test queries
    queries = [
        ("How do I reset my password?", "Password Management"),
        ("How do I troubleshoot RDP connection issues?", "RDP Issues"),
        ("How do I add a new user?", "User Management"),
    ]
    
    print(f"\n📊 Test Configuration:")
    print(f"   Server: {base_url}")
    print(f"   Model: Ollama Mistral 7B")
    print(f"   Documents: 525")
    print(f"   Timeout: 120 seconds")
    print("\n" + "="*90 + "\n")
    
    results = []
    
    for i, (query, domain) in enumerate(queries, 1):
        print(f"[TEST {i}/3] {domain}")
        print("-" * 90)
        print(f"📝 Query: {query}\n")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{base_url}/chat",
                json={"query": query, "session_id": f"test_{i}"},
                timeout=120
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ STATUS: SUCCESS\n")
                print(f"💬 RESPONSE FROM OLLAMA:")
                print("-" * 90)
                answer = data.get('answer', 'No response')
                print(answer)
                print("-" * 90)
                
                print(f"\n📊 METRICS:")
                print(f"   ⏱️  Response Time: {elapsed:.0f}ms ({elapsed/1000:.1f}s)")
                print(f"   🤖 Model: {data.get('source', 'unknown')}")
                print(f"   📍 Intent: {data.get('intent', 'unknown')}")
                print(f"   📈 Confidence: {data.get('confidence', 0):.1f}%")
                print(f"   🎯 Quality Score: {data.get('response_quality', 0):.2f}/1.0")
                
                context_count = len(data.get('context_with_metadata', []))
                print(f"   📚 Documents Used: {context_count}")
                
                results.append({
                    'query': query,
                    'domain': domain,
                    'status': 'SUCCESS',
                    'time_ms': elapsed,
                    'answer_length': len(answer),
                    'confidence': data.get('confidence', 0)
                })
                
            else:
                print(f"❌ HTTP ERROR: {response.status_code}\n")
                print(f"Response: {response.text[:300]}\n")
                results.append({
                    'query': query,
                    'domain': domain,
                    'status': 'FAILED',
                    'error': f"HTTP {response.status_code}"
                })
        
        except requests.exceptions.Timeout:
            print(f"❌ TIMEOUT: Server took too long to respond (>120s)\n")
            results.append({
                'query': query,
                'domain': domain,
                'status': 'TIMEOUT'
            })
        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION ERROR: Cannot reach server\n")
            print(f"Make sure server is running at {base_url}\n")
            results.append({
                'query': query,
                'domain': domain,
                'status': 'CONNECTION_ERROR'
            })
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}\n")
            results.append({
                'query': query,
                'domain': domain,
                'status': 'ERROR',
                'error': str(e)
            })
        
        print("=" * 90 + "\n")
        time.sleep(1)
    
    # Summary
    print("=" * 90)
    print(" " * 35 + "📋 TEST SUMMARY")
    print("=" * 90 + "\n")
    
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    total = len(results)
    
    print(f"✅ SUCCESSFUL: {successful}/{total} tests passed\n")
    
    if successful > 0:
        times = [r.get('time_ms', 0) for r in results if r['status'] == 'SUCCESS']
        avg_time = sum(times) / len(times)
        print(f"⏱️  PERFORMANCE:")
        print(f"   Average Response Time: {avg_time:.0f}ms ({avg_time/1000:.1f}s)")
        print(f"   Fastest: {min(times):.0f}ms")
        print(f"   Slowest: {max(times):.0f}ms\n")
        
        confidences = [r.get('confidence', 0) for r in results if r['status'] == 'SUCCESS']
        avg_confidence = sum(confidences) / len(confidences)
        print(f"📊 CONFIDENCE:")
        print(f"   Average: {avg_confidence:.1f}%\n")
    
    print("=" * 90)
    
    if successful == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ Ollama integration is working perfectly!")
        print("✨ Your chatbot is generating real AI responses!")
    else:
        print(f"\n⚠️  {total - successful} test(s) failed")
        print("Check the output above for error details")
    
    print("\n" + "=" * 90 + "\n")
    
    return successful == total

if __name__ == "__main__":
    try:
        success = test_chatbot()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
