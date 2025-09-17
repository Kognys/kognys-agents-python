#!/usr/bin/env python3
"""
Test script for dual streaming: research events + transaction events.

This simulates how the frontend should handle both streams:
1. Main research stream: /papers/stream  
2. Transaction stream: /transactions/stream

Usage:
    python tests/test_dual_streams.py --message "What are recent advances in AI?"
"""

import argparse
import asyncio
import json
import time


async def monitor_research_stream(base_url, message, user_id):
    """Monitor the main research stream."""
    import aiohttp
    
    url = f"{base_url}/papers/stream"
    payload = {"message": message, "user_id": user_id}
    
    print(f"🔬 RESEARCH STREAM: Starting research...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    print(f"❌ Research stream failed: {response.status}")
                    return
                
                event_count = 0
                async for line_bytes in response.content:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    
                    try:
                        event = json.loads(line[6:])
                        event_count += 1
                        event_type = event.get("event_type", "unknown")
                        
                        # Only show key research events to avoid spam
                        if event_type in ["research_started", "question_validated", "documents_retrieved", 
                                        "draft_generated", "criticisms_received", "orchestrator_decision", 
                                        "research_completed", "agent_message", "agent_debate"]:
                            
                            ts = time.strftime('%H:%M:%S', time.localtime(event.get('timestamp', 0)))
                            
                            if event_type == "agent_message":
                                agent = event.get("data", {}).get("agent_name", "Unknown")
                                msg_type = event.get("data", {}).get("message_type", "unknown")
                                print(f"[{ts}] 🤖 {agent} [{msg_type}]")
                            elif event_type == "research_completed":
                                print(f"[{ts}] 🎉 Research completed!")
                                break  # Research stream ends here
                            elif event_type == "agent_debate":
                                print(f"[{ts}] 💬 Agent debate started")
                            else:
                                print(f"[{ts}] 📝 {event_type}")
                    
                    except json.JSONDecodeError:
                        continue
                
                print(f"✅ Research stream completed ({event_count} events)")
                
    except Exception as e:
        print(f"❌ Research stream error: {e}")


async def monitor_transaction_stream(base_url):
    """Monitor the transaction stream for blockchain events."""
    import aiohttp
    
    url = f"{base_url}/transactions/stream"
    
    print(f"🔗 TRANSACTION STREAM: Waiting for blockchain events...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"❌ Transaction stream failed: {response.status}")
                    return
                
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
                        data = event.get("data", {})
                        
                        ts = time.strftime('%H:%M:%S', time.localtime(event.get('timestamp', 0)))
                        
                        if event_type == "transaction_stream_connected":
                            print(f"[{ts}] 🔗 Transaction stream connected")
                        elif event_type == "transaction_confirmed":
                            task_id = data.get("task_id", "Unknown")[:8] + "..."
                            tx_hash = data.get("transaction_hash", "Unknown")
                            operation = data.get("operation", "Unknown")
                            print(f"[{ts}] ✅ TRANSACTION CONFIRMED!")
                            print(f"    🆔 Task: {task_id}")
                            print(f"    🔗 Hash: {tx_hash}")
                            print(f"    ⚡ Operation: {operation}")
                        elif event_type == "transaction_failed":
                            task_id = data.get("task_id", "Unknown")[:8] + "..."
                            error = data.get("error", "Unknown")
                            print(f"[{ts}] ❌ Transaction failed: {error} (Task: {task_id})")
                        elif event_type == "transaction_heartbeat":
                            # Only show heartbeats occasionally
                            if event_count % 10 == 0:
                                elapsed = time.time() - start_time
                                print(f"[{ts}] 💓 Transaction stream alive ({elapsed:.0f}s)")
                    
                    except json.JSONDecodeError:
                        continue
                
    except Exception as e:
        print(f"❌ Transaction stream error: {e}")


async def test_dual_streams(base_url, message, user_id):
    """Test both research and transaction streams simultaneously."""
    print(f"🚀 Starting dual-stream test...")
    print(f"📋 Research question: {message}")
    print(f"👤 User ID: {user_id}")
    print("="*60)
    
    # Start both streams concurrently
    research_task = asyncio.create_task(monitor_research_stream(base_url, message, user_id))
    transaction_task = asyncio.create_task(monitor_transaction_stream(base_url))
    
    # Wait for research to complete
    await research_task
    
    # Give transaction stream extra time to receive blockchain events
    print(f"\n⏳ Waiting up to 60 seconds for transaction events...")
    try:
        await asyncio.wait_for(transaction_task, timeout=60.0)
    except asyncio.TimeoutError:
        print(f"⏰ Transaction stream timeout - cancelling")
        transaction_task.cancel()
    
    print(f"\n✅ Dual-stream test completed!")


def main():
    parser = argparse.ArgumentParser(description="Test dual streaming: research + transactions")
    parser.add_argument("--message", required=True, help="Research question to submit")
    parser.add_argument("--user-id", default="test_user", help="User ID for the request")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="Base API URL")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(test_dual_streams(args.base_url, args.message, args.user_id))
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")


if __name__ == "__main__":
    main()
