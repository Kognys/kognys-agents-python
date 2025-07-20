#!/usr/bin/env python3
"""
Standalone test to verify event emission logic
"""

import time
import threading
from typing import Dict, Any, Callable

class StandaloneExecutor:
    """Standalone executor for testing event emission."""
    
    def __init__(self):
        self.event_callbacks = []
        self._stop_event = threading.Event()
    
    def add_event_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add a callback function to be called when events occur."""
        self.event_callbacks.append(callback)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all registered callbacks."""
        print(f"📡 StandaloneExecutor emitting: {event_type}")
        if not self._stop_event.is_set():
            for callback in self.event_callbacks:
                try:
                    callback(event_type, data)
                except Exception as e:
                    print(f"Error in event callback: {e}")
    
    def execute_test(self):
        """Execute a test with event emission."""
        
        # Emit start event
        self._emit_event("research_started", {
            "question": "Test question",
            "task_id": "test-123",
            "status": "Starting research process..."
        })
        
        time.sleep(0.5)
        
        # Emit validation event
        self._emit_event("question_validated", {
            "validated_question": "Test question",
            "status": "Question validated and refined"
        })
        
        time.sleep(0.5)
        
        # Emit documents event
        self._emit_event("documents_retrieved", {
            "document_count": 5,
            "status": "Retrieved 5 relevant documents"
        })
        
        time.sleep(0.5)
        
        # Emit completion event
        self._emit_event("research_completed", {
            "final_answer": "Test answer",
            "status": "Research completed successfully"
        })

def test_standalone_executor():
    """Test the standalone executor."""
    
    print("🧪 Testing Standalone Event Emission")
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
    
    # Create executor
    executor = StandaloneExecutor()
    
    # Add callback
    print(f"📝 Adding callback to executor")
    executor.add_event_callback(event_callback)
    print(f"📝 Callback added, total callbacks: {len(executor.event_callbacks)}")
    
    # Execute test
    print("🚀 Executing test...")
    executor.execute_test()
    
    print(f"\n📊 Events received: {len(events_received)}")
    for i, event in enumerate(events_received, 1):
        print(f"{i:2d}. {event['type']}")

if __name__ == "__main__":
    test_standalone_executor() 