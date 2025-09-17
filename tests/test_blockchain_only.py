#!/usr/bin/env python3
"""
Test blockchain operations only - isolated from research flow.

This tests:
1. Agent registration
2. Task creation  
3. Task joining
4. Task finishing
5. Transaction event emission

Usage:
    python tests/test_blockchain_only.py
"""

import asyncio
import time
import uuid
import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append('/Users/m/Desktop/dev/kognys/kognys-agents-python')

# Load environment variables
load_dotenv()

async def test_blockchain_operations():
    """Test blockchain operations in isolation."""
    
    print("🧪 TESTING BLOCKCHAIN OPERATIONS ONLY")
    print("=" * 60)
    
    # Test configuration
    agent_id = os.getenv("MEMBASE_ID", "kognys_starter")
    task_id = str(uuid.uuid4())
    
    print(f"🔧 Configuration:")
    print(f"   Agent ID: {agent_id}")
    print(f"   Task ID: {task_id}")
    print(f"   Membase URL: {os.getenv('MEMBASE_API_URL', 'Not set')}")
    print(f"   API Key: {'Set' if os.getenv('MEMBASE_API_KEY') else 'Not set'}")
    print()
    
    # Import blockchain functions
    try:
        from kognys.services.membase_client import (
            register_agent_if_not_exists,
            async_create_task,
            async_join_task, 
            async_finish_task
        )
        print("✅ Blockchain functions imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    start_time = time.time()
    
    # Test 1: Agent Registration
    print(f"\n1️⃣ Testing Agent Registration...")
    try:
        reg_start = time.time()
        registration_success = register_agent_if_not_exists(agent_id)
        reg_time = time.time() - reg_start
        print(f"   Result: {'✅ Success' if registration_success else '❌ Failed'} ({reg_time:.2f}s)")
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return
    
    # Test 2: Task Creation
    print(f"\n2️⃣ Testing Task Creation...")
    try:
        create_start = time.time()
        create_success = await async_create_task(task_id, price=1000)
        create_time = time.time() - create_start
        print(f"   Result: {'✅ Success' if create_success else '❌ Failed'} ({create_time:.2f}s)")
        
        if not create_success:
            print("   🛑 Stopping test - task creation failed")
            return
    except Exception as e:
        print(f"   ❌ Task creation error: {e}")
        return
    
    # Test 3: Task Joining
    print(f"\n3️⃣ Testing Task Joining...")
    try:
        join_start = time.time()
        join_success = await async_join_task(task_id, agent_id)
        join_time = time.time() - join_start
        print(f"   Result: {'✅ Success' if join_success else '❌ Failed'} ({join_time:.2f}s)")
        
        if not join_success:
            print("   ⚠️ Join failed, but continuing to test finish...")
    except Exception as e:
        print(f"   ❌ Task joining error: {e}")
    
    # Test 4: Task Finishing
    print(f"\n4️⃣ Testing Task Finishing...")
    try:
        finish_start = time.time()
        finish_success = await async_finish_task(task_id, agent_id)
        finish_time = time.time() - finish_start
        print(f"   Result: {'✅ Success' if finish_success else '❌ Failed'} ({finish_time:.2f}s)")
    except Exception as e:
        print(f"   ❌ Task finishing error: {e}")
    
    # Test 5: Transaction Event Emission
    print(f"\n5️⃣ Testing Transaction Event Emission...")
    try:
        # Test the callback mechanism
        events_received = []
        
        def test_callback(event):
            events_received.append(event)
            print(f"   📡 Callback received: {event.get('event_type')}")
        
        # Test with callback using the correct function
        callback_start = time.time()
        from kognys.services.membase_client import async_finish_blockchain_operations
        await async_finish_blockchain_operations(task_id, agent_id, test_callback)
        callback_time = time.time() - callback_start
        
        print(f"   Callback test: {'✅ Success' if events_received else '❌ No events'} ({callback_time:.2f}s)")
        print(f"   Events received: {len(events_received)}")
        
        for event in events_received:
            event_type = event.get("event_type", "unknown")
            tx_hash = event.get("data", {}).get("transaction_hash", "No hash")
            print(f"     - {event_type}: {tx_hash}")
            
    except Exception as e:
        print(f"   ❌ Transaction event test error: {e}")
    
    total_time = time.time() - start_time
    print(f"\n⏱️ Total test time: {total_time:.2f} seconds")
    print("=" * 60)


async def test_transaction_stream_endpoint():
    """Test the transaction stream endpoint directly."""
    import aiohttp
    
    print(f"\n🌐 TESTING TRANSACTION STREAM ENDPOINT")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8001/transactions/stream") as response:
                if response.status != 200:
                    print(f"❌ Transaction stream endpoint failed: {response.status}")
                    return
                
                print(f"✅ Transaction stream connected (status: {response.status})")
                
                # Listen for a few events
                event_count = 0
                start_time = time.time()
                
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
                        
                        # Stop after getting connection confirmation or after 10 seconds
                        if event_type == "transaction_stream_connected" or elapsed > 10:
                            break
                            
                    except json.JSONDecodeError:
                        continue
                
                print(f"✅ Transaction stream test completed ({event_count} events)")
                
    except Exception as e:
        print(f"❌ Transaction stream endpoint error: {e}")


async def main():
    """Run all blockchain tests."""
    
    # Test 1: Blockchain operations in isolation
    await test_blockchain_operations()
    
    # Test 2: Transaction stream endpoint
    await test_transaction_stream_endpoint()
    
    print(f"\n🎯 SUMMARY:")
    print(f"   This test isolates blockchain operations from research flow")
    print(f"   If blockchain operations are slow/failing, this will show it")
    print(f"   Normal blockchain operations should take 5-15 seconds total")


if __name__ == "__main__":
    asyncio.run(main())
