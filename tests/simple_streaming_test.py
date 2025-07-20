#!/usr/bin/env python3
"""
Simple test to debug the streaming API
"""

import asyncio
import aiohttp
import json

async def test_streaming():
    """Test the streaming endpoint with debug output."""
    
    url = "http://localhost:8000/papers/stream"
    payload = {
        "message": "What is quantum computing?",
        "user_id": "test_user"
    }
    
    print("🧪 Testing streaming API...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                # Read the raw response
                raw_data = await response.read()
                print(f"Raw response length: {len(raw_data)}")
                print(f"Raw response (first 500 chars): {raw_data[:500]}")
                
                # Try to decode as text
                try:
                    text_data = raw_data.decode('utf-8')
                    print(f"Text response: {text_data[:500]}")
                except Exception as e:
                    print(f"Error decoding text: {e}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_streaming()) 