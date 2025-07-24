#!/usr/bin/env python3
import asyncio
import uuid
import json
import sys
import os

# Add parent directory to path to import from kognys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kognys.graph.state import KognysState
from kognys.graph.unified_executor import unified_executor


async def main():
    """Test the execute_streaming method and print all received events."""
    
    print("🔍 Starting streaming duplicates test...")
    print("=" * 60)
    
    # Set up the inputs for the test
    initial_state = KognysState(
        question="What are the latest developments in quantum computing?",
        user_id="test_user_123"
    )
    
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }
    
    print(f"📝 Test Configuration:")
    print(f"   Question: {initial_state.question}")
    print(f"   User ID: {initial_state.user_id}")
    print(f"   Thread ID: {config['configurable']['thread_id']}")
    print("=" * 60)
    print()
    
    # Core logic: iterate through streaming events
    event_counter = 0
    try:
        async for event in unified_executor.execute_streaming(initial_state, config):
            event_counter += 1
            print(f"📡 CLIENT-SIDE EVENT #{event_counter}:")
            print(f"   Event Type: {event.get('event_type', 'unknown')}")
            print(f"   Agent: {event.get('agent', 'unknown')}")
            print(f"   Timestamp: {event.get('timestamp', 'unknown')}")
            
            # Print event data in a formatted way
            if 'data' in event:
                print(f"   Data:")
                for key, value in event['data'].items():
                    # Truncate long values for readability
                    if isinstance(value, str) and len(value) > 100:
                        display_value = f"{value[:97]}..."
                    else:
                        display_value = value
                    print(f"     {key}: {display_value}")
            
            # Uncomment below for full JSON debugging:
            # print(f"   Full Event JSON: {json.dumps(event, indent=4)}")
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ CLIENT-SIDE ERROR: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
    
    print("=" * 60)
    print(f"🔍 Test completed. Total events received: {event_counter}")


if __name__ == "__main__":
    asyncio.run(main()) 