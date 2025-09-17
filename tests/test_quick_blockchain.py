#!/usr/bin/env python3
"""
Quick blockchain test to verify transaction events work.
"""

import asyncio
import sys
import time
import uuid

# Add project root to path
sys.path.append('/Users/m/Desktop/dev/kognys/kognys-agents-python')

async def quick_blockchain_test():
    """Quick test of blockchain operations with transaction events."""
    
    print("🧪 QUICK BLOCKCHAIN + TRANSACTION TEST")
    print("=" * 50)
    
    try:
        from kognys.services.membase_client import async_finish_blockchain_operations
        import os
        
        task_id = str(uuid.uuid4())
        agent_id = os.getenv("MEMBASE_ID", "kognys_starter")
        
        print(f"Task ID: {task_id}")
        print(f"Agent ID: {agent_id}")
        
        # Test transaction event emission
        events_received = []
        
        def test_callback(event):
            events_received.append(event)
            print(f"📡 Received event: {event.get('event_type')}")
            if event.get('event_type') == 'transaction_confirmed':
                data = event.get('data', {})
                tx_hash = data.get('transaction_hash', 'Unknown')
                print(f"🔗 Transaction Hash: {tx_hash}")
        
        print(f"\n🔗 Testing transaction event emission...")
        start_time = time.time()
        
        # This should emit transaction_confirmed event
        result = await async_finish_blockchain_operations(task_id, agent_id, test_callback)
        
        elapsed = time.time() - start_time
        print(f"✅ Blockchain operation completed: {result} ({elapsed:.2f}s)")
        print(f"📊 Events received: {len(events_received)}")
        
        if events_received:
            print(f"🎉 SUCCESS: Transaction events are working!")
            return True
        else:
            print(f"❌ FAILED: No transaction events received")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(quick_blockchain_test())
    print(f"\n🎯 RESULT: {'✅ SUCCESS' if result else '❌ FAILED'}")
