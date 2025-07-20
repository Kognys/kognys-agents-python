#!/usr/bin/env python3
"""
Test the unified executor directly
"""

import asyncio
import time
import sys
import os

# Add parent directory to path to import from kognys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kognys.graph.unified_executor import unified_executor
from kognys.graph.state import KognysState

def test_unified_executor():
    """Test the unified executor directly."""
    
    print("🧪 Testing Unified Executor")
    print("=" * 50)
    
    # Track events
    events_received = []
    
    def event_callback(event_type: str, data: dict):
        print(f"📡 Received event: {event_type}")
        events_received.append({
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        })
    
    # Add callback
    unified_executor.add_event_callback(event_callback)
    
    # Test with a simple question
    config = {"configurable": {"thread_id": "test-123"}}
    initial_state = KognysState(question="What are the latest developments in AI?")
    
    print("🚀 Starting research execution...")
    
    try:
        # Execute research
        result = unified_executor.execute_sync(initial_state, config)
        
        print(f"\n📊 Events received: {len(events_received)}")
        for i, event in enumerate(events_received, 1):
            print(f"{i:2d}. {event['type']}")
        
        print(f"\n✅ Research completed: {len(result.get('final_answer', ''))} chars")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_unified_executor() 