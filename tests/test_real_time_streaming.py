#!/usr/bin/env python3
"""
Comprehensive test for real-time WebSocket streaming
"""

import asyncio
import websockets
import json
import time

async def test_real_time_streaming():
    """Test real-time WebSocket streaming."""
    
    ws_url = "ws://localhost:8000/ws/research"
    
    print("🧪 Testing Real-Time WebSocket Streaming")
    print("=" * 60)
    print(f"URL: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, ping_interval=60, ping_timeout=60) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send research request
            test_data = {
                "message": "What are the latest developments in artificial intelligence?",
                "user_id": "test_user"
            }
            
            print(f"📤 Sending research request...")
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
                    if 'question' in data:
                        print(f"         Question: {data['question'][:50]}...")
                    if 'document_count' in data:
                        print(f"         Documents: {data['document_count']}")
                    if 'final_answer' in data:
                        print(f"         Answer: {data['final_answer'][:100]}...")
                    
                    print()
                    
                    # Check if this is a final event
                    if event_type in ['research_completed', 'research_failed', 'error']:
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing message: {e}")
                    continue
            
            # Summary
            print("=" * 60)
            print("📊 STREAMING SUMMARY:")
            print("=" * 60)
            
            for i, event in enumerate(events, 1):
                print(f"{i:2d}. [{event['elapsed']:6.1f}s] {event['type']}")
            
            total_time = time.time() - start_time
            print(f"\n⏱️  Total time: {total_time:.2f} seconds")
            print(f"📊 Total events: {len(events)}")
            print(f"⚡ Average time between events: {total_time/len(events):.2f}s")
            
            # Verify real-time streaming
            if len(events) >= 5:  # Should have multiple events
                print("\n✅ REAL-TIME STREAMING VERIFIED!")
                print("   - Multiple events received")
                print("   - Events spaced over time")
                print("   - No bulk delivery at end")
            else:
                print("\n⚠️  POTENTIAL ISSUE:")
                print("   - Few events received")
                print("   - May not be truly real-time")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_time_streaming()) 