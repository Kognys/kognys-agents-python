#!/usr/bin/env python3
"""
Simple test to verify unified executor event emission
"""

import time
import sys
import os

# Add parent directory to path to import from kognys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kognys.graph.unified_executor import unified_executor

def test_simple_events():
    """Test that the unified executor can emit events."""
    
    print("🧪 Testing Simple Event Emission")
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
    print(f"📝 Adding callback to unified executor")
    unified_executor.add_event_callback(event_callback)
    print(f"📝 Callback added, total callbacks: {len(unified_executor.event_callbacks)}")
    
    # Test manual event emission
    print("🚀 Testing manual event emission...")
    unified_executor._emit_event("test_event", {"message": "Hello World"})
    
    print(f"\n📊 Events received: {len(events_received)}")
    for i, event in enumerate(events_received, 1):
        print(f"{i:2d}. {event['type']}")

if __name__ == "__main__":
    test_simple_events() 