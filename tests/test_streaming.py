#!/usr/bin/env python3
"""
Simple test script for the Kognys Streaming API
"""

import asyncio
import aiohttp
import json
import time

async def test_streaming_api():
    """Test the streaming API endpoint."""
    
    url = "http://localhost:8000/papers/stream"
    payload = {
        "message": "What are the latest developments in artificial intelligence?",
        "user_id": "test_user_123"
    }
    
    print("🧪 Testing Kognys Streaming API")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            print("📡 Connecting to streaming endpoint...")
            
            async with session.post(url, json=payload) as response:
                print(f"📊 Response status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")
                    return
                
                print("✅ Connected successfully! Receiving events...")
                print()
                
                event_count = 0
                start_time = time.time()
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                            event_count += 1
                            
                            # Format timestamp
                            timestamp = event_data.get('timestamp', 0)
                            time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
                            
                            print(f"[{time_str}] 📝 Event #{event_count}: {event_data['event_type']}")
                            
                            # Show event details
                            data = event_data.get('data', {})
                            if 'status' in data:
                                print(f"    Status: {data['status']}")
                            if 'question' in data:
                                print(f"    Question: {data['question'][:50]}...")
                            if 'document_count' in data:
                                print(f"    Documents: {data['document_count']}")
                            if 'final_answer' in data:
                                print(f"    Answer: {data['final_answer'][:100]}...")
                            if 'error' in data:
                                print(f"    Error: {data['error']}")
                            
                            print()
                            
                            # Check if this is a final event
                            if event_data['event_type'] in ['research_completed', 'research_failed', 'error']:
                                elapsed = time.time() - start_time
                                print(f"⏱️  Total time: {elapsed:.2f} seconds")
                                print(f"📊 Total events received: {event_count}")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"❌ Error parsing event: {e}")
                            continue
                
                print("✅ Streaming test completed!")
                
    except aiohttp.ClientConnectorError:
        print("❌ Could not connect to server. Make sure the API is running on http://localhost:8000")
        print("💡 Start the server with: uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_streaming_api()) 