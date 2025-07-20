# kognys/graph/unified_executor.py
"""
Unified executor that handles all streaming and real-time functionality.
This consolidates the redundant implementations from:
- api_main.py WebSocket logic
- streaming_wrapper.py SSE logic  
- real_time_executor.py event emission
- builder.py StreamingKognysGraph
"""

import asyncio
import time
import threading
from typing import AsyncGenerator, Dict, Any, Callable, Optional
import queue
from kognys.graph.state import KognysState
from kognys.graph.builder import kognys_graph

class UnifiedExecutor:
    """Unified executor that handles all streaming and real-time functionality."""
    
    def __init__(self, graph):
        self.graph = graph
        self.event_callbacks = []
        self._stop_event = threading.Event()
    
    def add_event_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add a callback function to be called when events occur."""
        self.event_callbacks.append(callback)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all registered callbacks."""
        print(f"📡 UnifiedExecutor emitting: {event_type}")
        if not self._stop_event.is_set():
            for callback in self.event_callbacks:
                try:
                    callback(event_type, data)
                except Exception as e:
                    print(f"Error in event callback: {e}")
    
    def execute_sync(self, initial_state: KognysState, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the graph synchronously with real-time event emission during execution."""
        
        print(f"🚀 UnifiedExecutor.execute_sync called with question: {initial_state.question}")
        
        # Emit start event
        self._emit_event("research_started", {
            "question": initial_state.question,
            "task_id": config.get("configurable", {}).get("thread_id"),
            "status": "Starting research process..."
        })
        
        try:
            print(f"📝 Executing graph with real-time streaming...")
            
            # Use graph.stream() to get real-time updates during execution
            final_result = None
            for chunk in self.graph.stream(initial_state, config=config):
                # Each chunk contains the output of one node
                node_name = list(chunk.keys())[0] if chunk else None
                state = chunk[node_name] if node_name else None
                
                print(f"🔄 Processing node: {node_name}")
                
                if state and node_name:
                    # Emit events based on which node just completed
                    if node_name == "input_validator":
                        if state.get("validated_question"):
                            print(f"📝 Emitting question_validated event")
                            self._emit_event("question_validated", {
                                "validated_question": state["validated_question"],
                                "status": "Question validated and refined"
                            })
                    
                    elif node_name == "retriever":
                        if state.get("documents"):
                            print(f"📝 Emitting documents_retrieved event")
                            self._emit_event("documents_retrieved", {
                                "document_count": len(state["documents"]),
                                "status": f"Retrieved {len(state['documents'])} relevant documents"
                            })
                    
                    elif node_name == "synthesizer":
                        if state.get("draft_answer"):
                            print(f"📝 Emitting draft_generated event")
                            self._emit_event("draft_generated", {
                                "draft_length": len(state["draft_answer"]),
                                "status": "Initial draft generated"
                            })
                    
                    elif node_name == "challenger":
                        if state.get("criticisms"):
                            print(f"📝 Emitting criticisms_received event")
                            self._emit_event("criticisms_received", {
                                "criticism_count": len(state["criticisms"]),
                                "status": f"Received {len(state['criticisms'])} criticisms for improvement"
                            })
                    
                    elif node_name == "orchestrator":
                        # Extract decision from the latest transcript entry
                        decision = "unknown"
                        if state.get("transcript") and len(state["transcript"]) > 0:
                            latest_entry = state["transcript"][-1]
                            if latest_entry.get("agent") == "Orchestrator":
                                decision = latest_entry.get("output", "unknown")
                        
                        print(f"📝 Emitting orchestrator_decision event: {decision}")
                        self._emit_event("orchestrator_decision", {
                            "decision": decision,
                            "status": f"Orchestrator decided: {decision}"
                        })
                    
                    elif node_name == "publisher":
                        if state.get("final_answer"):
                            print(f"📝 Emitting research_completed event")
                            self._emit_event("research_completed", {
                                "final_answer": state["final_answer"],
                                "status": "Research completed successfully"
                            })
                            final_result = state
                
                # Store the final state
                if state:
                    final_result = state
            
            print(f"📝 Graph execution completed")
            
            # If no final answer was generated, emit failure
            if not final_result or not final_result.get("final_answer"):
                print(f"📝 Emitting research_failed event")
                self._emit_event("research_failed", {
                    "error": "No final answer generated",
                    "status": "Research process failed to generate a final answer"
                })
            
            return final_result or {}
            
        except Exception as e:
            print(f"❌ Error in execute_sync: {e}")
            # Handle validation errors specifically
            if isinstance(e, ValueError):
                self._emit_event("validation_error", {
                    "error": str(e),
                    "status": "Question validation failed",
                    "suggestion": "Please rephrase your question to be more specific and research-worthy."
                })
            else:
                self._emit_event("error", {
                    "error": str(e),
                    "status": "An error occurred during research"
                })
            raise
        finally:
            self._stop_event.set()
    
    async def execute_async(self, initial_state: KognysState, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the graph asynchronously with event emission."""
        
        print(f"🚀 UnifiedExecutor.execute_async called with question: {initial_state.question}")
        
        def run_execution():
            print(f"📝 Thread pool execution started")
            return self.execute_sync(initial_state, config)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_execution)
        print(f"📝 Thread pool execution completed")
        return result
    
    async def execute_streaming(self, initial_state: KognysState, config: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the graph with streaming events (for SSE)."""
        
        # Create a queue for events
        event_queue = queue.Queue()
        
        def event_callback(event_type: str, data: Dict[str, Any]):
            event_queue.put({
                "event_type": event_type,
                "data": data,
                "timestamp": time.time()
            })
        
        # Add our callback
        self.add_event_callback(event_callback)
        
        # Start execution in background
        def run_execution():
            try:
                return self.execute_sync(initial_state, config)
            except Exception as e:
                event_queue.put({
                    "event_type": "error",
                    "data": {"error": str(e)},
                    "timestamp": time.time()
                })
                raise
        
        # Start execution thread
        execution_thread = threading.Thread(target=run_execution)
        execution_thread.start()
        
        # Stream events as they arrive
        while True:
            try:
                # Wait for events with timeout
                event = event_queue.get(timeout=1.0)
                yield event
                
                # If this is a final event, break
                if event["event_type"] in ["research_completed", "research_failed", "error", "validation_error"]:
                    break
                    
            except queue.Empty:
                # Check if execution thread is still running
                if not execution_thread.is_alive():
                    break
                continue
        
        # Wait for execution thread to finish
        execution_thread.join(timeout=5.0)

# Create unified executor instance
unified_executor = UnifiedExecutor(kognys_graph) 