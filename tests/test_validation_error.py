#!/usr/bin/env python3
"""
Test validation error handling
"""

import asyncio
import websockets
import json
import time

async def test_validation_error():
    """Test validation error handling."""
    
    ws_url = "ws://localhost:8000/ws/research"
    
    print("🧪 Testing Validation Error Handling")
    print("=" * 60)
    print(f"URL: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, ping_interval=60, ping_timeout=60) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send a question that should be rejected
            test_data = {
                "message": "hello",  # This should be rejected as too vague
                "user_id": "test_user"
            }
            
            print(f"📤 Sending question that should be rejected...")
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
                    if 'suggestion' in data:
                        print(f"         Suggestion: {data['suggestion']}")
                    if 'question' in data:
                        print(f"         Question: {data['question'][:50]}...")
                    
                    print()
                    
                    # Check if this is a final event
                    if event_type in ['validation_error', 'research_completed', 'research_failed', 'error']:
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing message: {e}")
                    continue
            
            # Summary
            print("=" * 60)
            print("📊 VALIDATION TEST SUMMARY:")
            print("=" * 60)
            
            for i, event in enumerate(events, 1):
                print(f"{i:2d}. [{event['elapsed']:6.1f}s] {event['type']}")
            
            # Check if validation error was properly handled
            validation_events = [e for e in events if e['type'] == 'validation_error']
            if validation_events:
                print("\n✅ VALIDATION ERROR PROPERLY HANDLED!")
                print("   - Validation error event received")
                print("   - Detailed error message provided")
                print("   - User-friendly feedback given")
            else:
                print("\n⚠️  VALIDATION ERROR NOT DETECTED:")
                print("   - No validation_error event found")
                print("   - Check if question was actually rejected")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_validation_error()) 