#!/usr/bin/env python3
"""
Manual test to verify transaction events work by directly calling blockchain operations.
"""

import asyncio
import json
import sys
import time
import uuid

# Add project root to path
sys.path.append('/Users/m/Desktop/dev/kognys/kognys-agents-python')

async def test_manual_blockchain_with_events():
    """Manually call blockchain operations and verify transaction events are emitted."""
    
    print("🧪 MANUAL BLOCKCHAIN + TRANSACTION EVENT TEST")
    print("=" * 60)
    
    # Start transaction stream listener
    import aiohttp
    
    async def listen_for_transaction():
        print("🔗 Starting transaction stream listener...")
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8001/transactions/stream") as response:
                if response.status != 200:
                    print(f"❌ Transaction stream failed: {response.status}")
                    return
                
                print(f"✅ Transaction stream connected")
                
                async for line_bytes in response.content:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get("event_type", "unknown")
                        
                        if event_type == "transaction_confirmed":
                            data = event.get("data", {})
                            tx_hash = data.get("transaction_hash", "Unknown")
                            task_id = data.get("task_id", "Unknown")
                            print(f"🎉 SUCCESS! Received transaction_confirmed:")
                            print(f"   🔗 Hash: {tx_hash}")
                            print(f"   🆔 Task: {task_id}")
                            return True
                        elif event_type == "transaction_failed":
                            data = event.get("data", {})
                            error = data.get("error", "Unknown")
                            print(f"❌ Received transaction_failed: {error}")
                            return False
                        elif event_type == "transaction_stream_connected":
                            print(f"📡 Transaction stream ready")
                        
                    except json.JSONDecodeError:
                        continue
    
    async def trigger_blockchain_operation():
        """Manually trigger blockchain operations."""
        await asyncio.sleep(2)  # Give stream time to connect
        
        print(f"\n⚡ Manually triggering blockchain operations...")
        
        from kognys.services.membase_client import async_finish_blockchain_operations
        import os
        
        task_id = str(uuid.uuid4())
        agent_id = os.getenv("MEMBASE_ID", "kognys_starter")
        
        print(f"   Task ID: {task_id}")
        print(f"   Agent ID: {agent_id}")
        
        # First create and join the task
        from kognys.services.membase_client import async_create_task, async_join_task
        
        print(f"🔗 Creating task...")
        create_success = await async_create_task(task_id)
        if not create_success:
            print(f"❌ Task creation failed")
            return False
        
        print(f"🔗 Joining task...")
        join_success = await async_join_task(task_id, agent_id)
        if not join_success:
            print(f"❌ Task joining failed")
            return False
        
        print(f"🔗 Finishing task (should emit transaction_confirmed)...")
        finish_success = await async_finish_blockchain_operations(task_id, agent_id)
        
        print(f"✅ Blockchain operations completed: {finish_success}")
        return finish_success
    
    # Run both tasks concurrently
    listener_task = asyncio.create_task(listen_for_transaction())
    blockchain_task = asyncio.create_task(trigger_blockchain_operation())
    
    # Wait for blockchain operation to complete
    blockchain_result = await blockchain_task
    
    # Give listener a bit more time to receive the event
    try:
        listener_result = await asyncio.wait_for(listener_task, timeout=10.0)
        return blockchain_result and listener_result
    except asyncio.TimeoutError:
        print(f"⏰ Transaction event listener timeout")
        listener_task.cancel()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_manual_blockchain_with_events())
    
    print(f"\n🎯 RESULT: {'✅ SUCCESS' if result else '❌ FAILED'}")
    print(f"   This test verifies if blockchain operations emit transaction events")
    print(f"   If this works, the problem is in the research flow integration")
    print(f"   If this fails, the transaction event system needs debugging")
