#!/usr/bin/env python3
"""
Test script for the refactored token-by-token streaming architecture.

This test connects to the SSE endpoint and verifies that:
1. It receives discrete token events (e.g., 'draft_answer_token').
2. It can aggregate these tokens into a complete response.
3. It still receives the standard node completion events.
"""

import requests
import json
import time

def test_token_streaming():
    """Connects to the streaming endpoint and validates token-based events."""
    
    url = "http://localhost:8000/papers/stream"
    payload = {
        "message": "Explain the importance of token-based streaming in LLM applications.",
        "user_id": "token_stream_test"
    }
    
    print("🚀 Testing Token-by-Token Streaming Architecture...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n" + "="*60)
    
    try:
        response = requests.post(url, json=payload, headers={"Accept": "text/event-stream"}, stream=True, timeout=120)
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code} - {response.text}")
            return

        print("✅ Connected to SSE endpoint. Waiting for events...")
        print("-" * 60)
        
        # Trackers
        token_events = {"draft_answer_token": 0, "criticism_token": 0, "final_answer_token": 0}
        node_completion_events = set()
        full_draft = ""
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                event = json.loads(line[6:])
                event_type = event.get('event_type', 'unknown')
                data = event.get('data', {})

                # Handle token-level events
                if event_type.endswith("_token"):
                    token_events[event_type] += 1
                    token_content = data.get("token", "")
                    
                    # Live print the tokens as they arrive
                    if event_type == "draft_answer_token":
                        print(token_content, end="", flush=True)
                        full_draft += token_content
                    
                # Handle node completion events
                else:
                    node_completion_events.add(event_type)
                    # Print a newline after a stream of tokens is done
                    if token_events["draft_answer_token"] > 0 and "draft_generated" in node_completion_events:
                        print("\n--- [End of Draft Stream] ---")
                    
                    print(f"\n🔵 NODE EVENT: {event_type.upper()}")
                    print(f"   Status: {data.get('status', 'N/A')}")
                    
                    if event_type == 'paper_generated':
                        break

        print("-" * 60)
        print("\n📊 Streaming Test Summary:")
        print("Token Events Received:")
        for key, count in token_events.items():
            print(f"  - {key}: {count} tokens")
            
        print("\nNode Completion Events Received:")
        for event in sorted(list(node_completion_events)):
            print(f"  - {event}")
            
        print(f"\n📝 Length of aggregated draft: {len(full_draft)} characters")

        # Validation
        if sum(token_events.values()) > 0 and len(node_completion_events) > 3:
            print("\n🎉 SUCCESS: Token-based streaming is working correctly!")
        else:
            print("\n❌ FAILURE: Did not receive the expected mix of token and node events.")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Error: {e}")
        print("💡 Make sure the server is running: uvicorn api_main:app --reload")

if __name__ == "__main__":
    test_token_streaming() 