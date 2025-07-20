#!/usr/bin/env python3
"""
Example Python WebSocket client for the Kognys Research API.

This demonstrates how to consume the WebSocket streaming endpoint.
"""

import asyncio
import websockets
import json
import time

class KognysWebSocketClient:
    """WebSocket client for the Kognys research API."""
    
    def __init__(self, ws_url: str = "ws://localhost:8000/ws/research"):
        self.ws_url = ws_url
    
    async def stream_research(self, question: str, user_id: str):
        """
        Stream research progress via WebSocket.
        
        Args:
            question: The research question to investigate
            user_id: The user ID for the request
        """
        print(f"🔬 Starting WebSocket research on: {question}")
        print("=" * 60)
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("✅ Connected to WebSocket")
                
                # Send research request
                request_data = {
                    "message": question,
                    "user_id": user_id
                }
                
                await websocket.send(json.dumps(request_data))
                print("📤 Sent research request")
                print()
                
                event_count = 0
                start_time = time.time()
                
                # Listen for events
                async for message in websocket:
                    try:
                        event_data = json.loads(message)
                        event_count += 1
                        
                        # Format timestamp
                        timestamp = event_data.get('timestamp', 0)
                        time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
                        
                        event_type = event_data.get('event_type', event_data.get('type', 'unknown'))
                        data = event_data.get('data', {})
                        
                        print(f"[{time_str}] 📝 Event #{event_count}: {event_type}")
                        
                        # Show event details
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
                        if 'message' in data:
                            print(f"    Message: {data['message']}")
                        
                        print()
                        
                        # Check if this is a final event
                        if event_type in ['research_completed', 'research_failed', 'error']:
                            elapsed = time.time() - start_time
                            print(f"⏱️  Total time: {elapsed:.2f} seconds")
                            print(f"📊 Total events received: {event_count}")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Error parsing event: {e}")
                        continue
                
                print("✅ WebSocket research completed!")
                
        except websockets.exceptions.ConnectionClosed:
            print("❌ WebSocket connection closed unexpectedly")
        except websockets.exceptions.InvalidURI:
            print("❌ Invalid WebSocket URI")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

async def main():
    """Example usage of the WebSocket client."""
    
    client = KognysWebSocketClient()
    
    # Example research question
    question = "What are the latest developments in quantum computing?"
    user_id = "example_user_123"
    
    await client.stream_research(question, user_id)

if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 