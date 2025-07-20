#!/usr/bin/env python3
"""
Simple WebSocket test to debug connection issues
"""

import asyncio
import websockets
import json

async def test_websocket():
    """Test basic WebSocket connection."""
    
    ws_url = "ws://localhost:8000/ws/research"
    
    print("🧪 Testing WebSocket connection...")
    print(f"URL: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send a simple test message
            test_data = {
                "message": "What is quantum computing?",
                "user_id": "test_user"
            }
            
            print(f"📤 Sending: {json.dumps(test_data)}")
            await websocket.send(json.dumps(test_data))
            
            # Listen for a few messages
            message_count = 0
            async for message in websocket:
                message_count += 1
                print(f"📥 Received message #{message_count}: {message[:200]}...")
                
                if message_count >= 3:  # Just get first 3 messages
                    break
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 