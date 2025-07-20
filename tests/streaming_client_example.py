#!/usr/bin/env python3
"""
Example Python client for the Kognys Streaming API.

This demonstrates how to consume the Server-Sent Events (SSE) streaming endpoint.
"""

import asyncio
import aiohttp
import json
import time
from typing import AsyncGenerator

class KognysStreamingClient:
    """Client for consuming the Kognys streaming API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def stream_research(self, question: str, user_id: str) -> AsyncGenerator[dict, None]:
        """
        Stream research progress for a given question.
        
        Args:
            question: The research question to investigate
            user_id: The user ID for the request
            
        Yields:
            dict: Event data with event_type, data, and timestamp
        """
        url = f"{self.base_url}/papers/stream"
        payload = {
            "message": question,
            "user_id": user_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                
                # Process Server-Sent Events
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                            yield event_data
                        except json.JSONDecodeError as e:
                            print(f"Error parsing event: {e}")
                            continue

async def main():
    """Example usage of the streaming client."""
    
    client = KognysStreamingClient()
    
    # Example research question
    question = "What are the latest developments in quantum computing?"
    user_id = "example_user_123"
    
    print(f"🔬 Starting research on: {question}")
    print("=" * 60)
    
    try:
        async for event in client.stream_research(question, user_id):
            event_type = event.get('event_type', 'unknown')
            data = event.get('data', {})
            timestamp = event.get('timestamp', 0)
            
            # Format timestamp
            time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
            
            # Print event based on type
            if event_type == 'research_started':
                print(f"[{time_str}] 🚀 Research started")
                print(f"    Question: {data.get('question', 'N/A')}")
                print(f"    Task ID: {data.get('task_id', 'N/A')}")
                
            elif event_type == 'question_validated':
                print(f"[{time_str}] ✅ Question validated")
                print(f"    Refined question: {data.get('validated_question', 'N/A')}")
                
            elif event_type == 'documents_retrieved':
                print(f"[{time_str}] 📚 Documents retrieved")
                print(f"    Found {data.get('document_count', 0)} relevant documents")
                
            elif event_type == 'draft_generated':
                print(f"[{time_str}] ✍️ Draft generated")
                print(f"    Draft length: {data.get('draft_length', 0)} characters")
                
            elif event_type == 'criticisms_received':
                print(f"[{time_str}] 🤔 Criticisms received")
                print(f"    {data.get('criticism_count', 0)} criticisms for improvement")
                
            elif event_type == 'research_completed':
                print(f"[{time_str}] 🎉 Research completed!")
                final_answer = data.get('final_answer', '')
                print(f"    Final answer: {final_answer[:200]}{'...' if len(final_answer) > 200 else ''}")
                
            elif event_type == 'research_failed':
                print(f"[{time_str}] ❌ Research failed")
                print(f"    Error: {data.get('error', 'Unknown error')}")
                
            elif event_type == 'error':
                print(f"[{time_str}] 💥 Error occurred")
                print(f"    Error: {data.get('error', 'Unknown error')}")
                
            else:
                print(f"[{time_str}] 📝 {event_type}")
                print(f"    Data: {data}")
            
            print()
            
            # If this is a final event, break
            if event_type in ['research_completed', 'research_failed', 'error']:
                break
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 