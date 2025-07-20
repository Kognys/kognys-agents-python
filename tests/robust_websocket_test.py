#!/usr/bin/env python3
"""
Robust WebSocket test with better error handling
"""

import asyncio
import websockets
import json
import time

async def test_websocket_robust():
    """Test WebSocket with better error handling."""
    
    ws_url = "ws://localhost:8000/ws/research"
    
    print("🧪 Testing WebSocket connection (robust)...")
    print(f"URL: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, ping_interval=60, ping_timeout=60) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send a simple test message
            test_data = {
                "message": "What is quantum computing?",
                "user_id": "test_user"
            }
            
            print(f"📤 Sending: {json.dumps(test_data)}")
            await websocket.send(json.dumps(test_data))
            
            # Listen for messages with timeout
            message_count = 0
            start_time = time.time()
            
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=300)  # 5 minute timeout
                    message_count += 1
                    
                    print(f"📥 Received message #{message_count}: {message[:200]}...")
                    
                    # Parse the message
                    try:
                        event_data = json.loads(message)
                        event_type = event_data.get('event_type', event_data.get('type', 'unknown'))
                        
                        if event_type in ['research_completed', 'research_failed', 'error']:
                            elapsed = time.time() - start_time
                            print(f"⏱️  Total time: {elapsed:.2f} seconds")
                            print(f"📊 Total messages received: {message_count}")
                            break
                            
                    except json.JSONDecodeError:
                        print("⚠️  Could not parse message as JSON")
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                    
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    asyncio.run(test_websocket_robust()) 