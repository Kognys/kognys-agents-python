#!/usr/bin/env python3
"""
Test successful research with valid questions
"""

import asyncio
import websockets
import json
import time

async def test_successful_research():
    """Test successful research with valid questions."""
    
    ws_url = "ws://localhost:8000/ws/research"
    
    print("🧪 Testing Successful Research")
    print("=" * 60)
    print(f"URL: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, ping_interval=60, ping_timeout=60) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send a valid research question
            test_data = {
                "message": "What are the latest developments in artificial intelligence?",
                "user_id": "test_user"
            }
            
            print(f"📤 Sending valid research question...")
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
            print("📊 SUCCESS TEST SUMMARY:")
            print("=" * 60)
            
            for i, event in enumerate(events, 1):
                print(f"{i:2d}. [{event['elapsed']:6.1f}s] {event['type']}")
            
            # Check if research was successful
            success_events = [e for e in events if e['type'] == 'research_completed']
            if success_events:
                print("\n✅ RESEARCH SUCCESSFUL!")
                print("   - Research completed event received")
                print("   - Final answer generated")
                print("   - No validation errors")
            else:
                print("\n⚠️  RESEARCH NOT SUCCESSFUL:")
                print("   - No research_completed event found")
                print("   - Check for validation errors or other issues")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_successful_research()) 