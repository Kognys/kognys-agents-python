#!/usr/bin/env python3
"""
Test question reformulation
"""

import asyncio
import websockets
import json
import time
import sys
import os

# Add parent directory to path to import from kognys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_question_reformulation():
    """Test that questions are reformulated instead of rejected."""
    
    ws_url = "ws://localhost:8000/ws/research"
    
    print("🧪 Testing Question Reformulation")
    print("=" * 60)
    print(f"URL: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, ping_interval=60, ping_timeout=60) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send a question that should be reformulated
            test_data = {
                "message": "Research about politicians in Portugal",  # This should be reformulated
                "user_id": "test_user"
            }
            
            print(f"📤 Sending question that should be reformulated...")
            await websocket.send(json.dumps(test_data))
            
            # Track events and timing
            events = []
            start_time = time.time()
            
            print("\n📊 Real-time events:")
            print("-" * 40)
            
            async for message in websocket:
                try:
                    event_data = json.loads(message)
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    event_type = event_data.get('event_type', event_data.get('type', 'unknown'))
                    events.append({
                        'type': event_type,
                        'elapsed': elapsed,
                        'data': event_data.get('data', {})
                    })
                    
                    print(f"[{elapsed:6.1f}s] 📝 {event_type}")
                    
                    # Show event details
                    data = event_data.get('data', {})
                    if 'status' in data:
                        print(f"         Status: {data['status']}")
                    if 'error' in data:
                        print(f"         Error: {data['error']}")
                    if 'final_answer' in data:
                        print(f"         Answer: {data['final_answer'][:100]}...")
                    
                    print()
                    
                    # Check if this is a final event
                    if event_type in ['research_completed', 'research_failed', 'validation_error', 'error']:
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing message: {e}")
                    continue
            
            # Summary
            print("=" * 60)
            print("📊 REFORMULATION TEST SUMMARY:")
            print("=" * 60)
            
            for i, event in enumerate(events, 1):
                print(f"{i:2d}. [{event['elapsed']:6.1f}s] {event['type']}")
            
            # Check if question was reformulated and research completed
            validation_events = [e for e in events if e['type'] == 'validation_error']
            success_events = [e for e in events if e['type'] == 'research_completed']
            
            if validation_events:
                print("\n⚠️  QUESTION WAS REJECTED:")
                print("   - Validation error received")
                print("   - Question was not reformulated")
            elif success_events:
                print("\n✅ QUESTION WAS REFORMULATED:")
                print("   - Research completed successfully")
                print("   - Question was reformulated and processed")
            else:
                print("\n❓ UNKNOWN RESULT:")
                print("   - Neither validation error nor success")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_question_reformulation()) 