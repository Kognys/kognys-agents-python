#!/usr/bin/env python3
"""
Quick test to verify transaction events work during actual research.

This runs a minimal research question and monitors both streams.
"""

import asyncio
import json
import sys
import time

# Add project root to path
sys.path.append('/Users/m/Desktop/dev/kognys/kognys-agents-python')

async def monitor_both_streams():
    """Monitor both research and transaction streams simultaneously."""
    import aiohttp
    
    print("🚀 Testing Both Streams with Quick Research")
    print("=" * 60)
    
    # Start both streams
    async def monitor_research():
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://127.0.0.1:8001/papers/stream",
                json={"message": "What is AI?", "user_id": "test"}
            ) as response:
                print(f"🔬 Research stream: {response.status}")
                
                async for line_bytes in response.content:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get("event_type", "unknown")
                        
                        if event_type in ["research_started", "research_completed", "validation_error"]:
                            ts = time.strftime('%H:%M:%S', time.localtime(event.get('timestamp', 0)))
                            print(f"[{ts}] 🔬 {event_type}")
                            
                            if event_type in ["research_completed", "validation_error"]:
                                break
                                
                    except json.JSONDecodeError:
                        continue
    
    async def monitor_transactions():
        await asyncio.sleep(1)  # Start transaction monitoring after research starts
        
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:8001/transactions/stream") as response:
                print(f"🔗 Transaction stream: {response.status}")
                
                start_time = time.time()
                async for line_bytes in response.content:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get("event_type", "unknown")
                        
                        elapsed = time.time() - start_time
                        ts = time.strftime('%H:%M:%S', time.localtime(event.get('timestamp', 0)))
                        
                        if event_type == "transaction_confirmed":
                            data = event.get("data", {})
                            tx_hash = data.get("transaction_hash", "Unknown")
                            print(f"[{ts}] 🔗 ✅ TRANSACTION CONFIRMED: {tx_hash}")
                            break
                        elif event_type == "transaction_failed":
                            data = event.get("data", {})
                            error = data.get("error", "Unknown")
                            print(f"[{ts}] 🔗 ❌ TRANSACTION FAILED: {error}")
                            break
                        elif event_type == "transaction_stream_connected":
                            print(f"[{ts}] 🔗 Transaction stream connected")
                        elif elapsed % 30 < 1:  # Show heartbeats every 30 seconds
                            print(f"[{ts}] 🔗 💓 Transaction stream alive ({elapsed:.0f}s)")
                        
                        # Stop after 2 minutes if no transaction events
                        if elapsed > 120:
                            print(f"[{ts}] 🔗 ⏰ Transaction stream timeout (2 min)")
                            break
                            
                    except json.JSONDecodeError:
                        continue
    
    # Run both streams concurrently
    await asyncio.gather(
        monitor_research(),
        monitor_transactions()
    )

if __name__ == "__main__":
    asyncio.run(monitor_both_streams())
