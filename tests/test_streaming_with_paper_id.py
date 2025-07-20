#!/usr/bin/env python3
"""
Test script to verify that /papers/stream now includes paper_id in the response.
This tests the enhanced SSE streaming functionality.
"""

import requests
import json
import time

def test_streaming_with_paper_id():
    """Test the enhanced streaming endpoint that includes paper ID."""
    
    url = "http://localhost:8000/papers/stream"
    
    payload = {
        "message": "What are the benefits of renewable energy?",
        "user_id": "test_user_stream"
    }
    
    print("🚀 Testing enhanced streaming endpoint with paper ID...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n" + "="*60)
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        print("✅ Connected to streaming endpoint")
        print("\n📡 Streaming events:")
        print("-" * 40)
        
        paper_id_found = False
        final_paper_event = False
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                    event_type = event_data.get('event_type', 'unknown')
                    data = event_data.get('data', {})
                    
                    print(f"📨 Event: {event_type}")
                    
                    # Check for paper_id in events
                    if 'paper_id' in data:
                        paper_id_found = True
                        print(f"   📄 Paper ID: {data['paper_id']}")
                    
                    # Check for paper_generated event
                    if event_type == 'paper_generated':
                        final_paper_event = True
                        print(f"   📄 Paper ID: {data.get('paper_id', 'NOT_FOUND')}")
                        print(f"   📝 Paper Length: {len(data.get('paper_content', ''))}")
                        print(f"   ✅ Status: {data.get('status', 'unknown')}")
                        break
                    
                    # Show other important info
                    if 'status' in data:
                        print(f"   ℹ️  Status: {data['status']}")
                    
                    print()
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    continue
                    
        print("-" * 40)
        print("\n🔍 Test Results:")
        print(f"✅ Paper ID found in events: {paper_id_found}")
        print(f"✅ Final paper_generated event: {final_paper_event}")
        
        if paper_id_found and final_paper_event:
            print("🎉 SUCCESS: Enhanced streaming with paper ID works correctly!")
        else:
            print("❌ FAILURE: Some expected features missing")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        print("💡 Make sure the server is running: uvicorn api_main:app --reload")
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_streaming_with_paper_id() 