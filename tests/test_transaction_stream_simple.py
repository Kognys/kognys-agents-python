#!/usr/bin/env python3
"""
Simple test for transaction stream endpoint.

This tests:
1. Transaction stream connection
2. Manual transaction event injection
3. Event reception

Usage:
    python tests/test_transaction_stream_simple.py
"""

import asyncio
import json
import sys
import time

# Add project root to path
sys.path.append('/Users/m/Desktop/dev/kognys/kognys-agents-python')

async def test_transaction_stream():
    """Test the transaction stream endpoint."""
    import aiohttp
    
    print("🔗 Testing Transaction Stream Endpoint")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8001/transactions/stream") as response:
                if response.status != 200:
                    print(f"❌ Failed to connect: {response.status}")
                    return
                
                print(f"✅ Connected to transaction stream")
                
                # Listen for events for 10 seconds
                start_time = time.time()
                event_count = 0
                
                async for line_bytes in response.content:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    try:
                        event = json.loads(line[6:])
                        event_count += 1
                        event_type = event.get("event_type", "unknown")
                        
                        elapsed = time.time() - start_time
                        print(f"[{elapsed:.1f}s] 📡 {event_type}")
                        
                        if event_type == "transaction_confirmed":
                            data = event.get("data", {})
                            tx_hash = data.get("transaction_hash", "Unknown")
                            task_id = data.get("task_id", "Unknown")
                            print(f"       🔗 Hash: {tx_hash}")
                            print(f"       🆔 Task: {task_id}")
                            break
                        
                        # Stop after 15 seconds or if we get connection confirmation
                        if elapsed > 15 or event_type == "transaction_stream_connected":
                            if event_type == "transaction_stream_connected":
                                print(f"✅ Stream connected successfully")
                            break
                            
                    except json.JSONDecodeError:
                        continue
                
                print(f"📊 Received {event_count} events in {elapsed:.1f}s")
                
    except Exception as e:
        print(f"❌ Stream error: {e}")

async def test_manual_transaction_injection():
    """Test manual injection of transaction events."""
    print(f"\n🧪 Testing Manual Transaction Event Injection")
    print("=" * 50)
    
    try:
        # Import the shared transaction system
        from kognys.services.transaction_events import emit_transaction_confirmed
        
        # Inject a test transaction event
        success = emit_transaction_confirmed(
            task_id="test-task-123",
            transaction_hash="0x1234567890abcdef",
            operation="test_operation"
        )
        
        if success:
            print(f"✅ Injected test transaction event")
        else:
            print(f"❌ Failed to inject test event")
            return
        
        # Now listen to the stream to see if it comes through
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8001/transactions/stream") as response:
                if response.status != 200:
                    print(f"❌ Failed to connect: {response.status}")
                    return
                
                print(f"✅ Listening for injected event...")
                
                start_time = time.time()
                async for line_bytes in response.content:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get("event_type", "unknown")
                        
                        elapsed = time.time() - start_time
                        print(f"[{elapsed:.1f}s] 📡 {event_type}")
                        
                        if event_type == "transaction_confirmed":
                            data = event.get("data", {})
                            tx_hash = data.get("transaction_hash", "Unknown")
                            print(f"✅ SUCCESS! Received transaction event with hash: {tx_hash}")
                            break
                        
                        if elapsed > 5:  # Only wait 5 seconds for the test event
                            print(f"⏰ Timeout waiting for test event")
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        print(f"❌ Manual injection test error: {e}")

async def main():
    """Run transaction stream tests."""
    
    # Test 1: Basic stream connection
    await test_transaction_stream()
    
    # Test 2: Manual event injection to verify infrastructure
    await test_manual_transaction_injection()
    
    print(f"\n🎯 SUMMARY:")
    print(f"   If manual injection works, the stream infrastructure is good")
    print(f"   If it doesn't work, there's an issue with the stream setup")
    print(f"   This isolates the problem from blockchain operations")

if __name__ == "__main__":
    asyncio.run(main())
