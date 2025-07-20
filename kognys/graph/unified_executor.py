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
from langchain_core.runnables.base import Runnable

class UnifiedExecutor:
    """Unified executor that handles all streaming and real-time functionality."""
    
    def __init__(self, graph):
        self.graph = graph
        self.event_callbacks = []
        self._stop_event = threading.Event()
        # Store recent events for logs endpoint (max 100 events)
        self._recent_events = []
        self._max_events = 100
        self._events_lock = threading.Lock()
    
    def add_event_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add a callback function to be called when events occur."""
        self.event_callbacks.append(callback)
    
    def get_recent_events(self, limit: int = 50) -> list:
        """Get recent system events for logs display."""
        with self._events_lock:
            return self._recent_events[-limit:] if self._recent_events else []
    
    async def stream_recent_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream recent events for real-time logs monitoring."""
        # Return existing events first
        recent = self.get_recent_events()
        for event in recent:
            yield event
        
        # Then stream new events as they arrive
        event_queue = queue.Queue()
        
        def log_callback(event_type: str, data: Dict[str, Any]):
            # Get the most recent event (which includes agent info)
            with self._events_lock:
                if self._recent_events:
                    event_queue.put(self._recent_events[-1])
        
        self.add_event_callback(log_callback)
        
        try:
            while True:
                try:
                    event = event_queue.get(timeout=30)  # 30 second timeout
                    yield event
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield {
                        "event_type": "heartbeat",
                        "data": {"status": "alive"},
                        "timestamp": time.time(),
                        "agent": "system"
                    }
        except Exception as e:
            print(f"Error in log streaming: {e}")
            yield {
                "event_type": "error",
                "data": {"error": str(e)},
                "timestamp": time.time(),
                "agent": "system"
            }
    
    def _emit_event(self, event_type: str, data: Dict[str, Any], agent: str = None):
        """Emit an event to all registered callbacks."""
        print(f"📡 UnifiedExecutor emitting: {event_type}")
        
        # Create event with timestamp and agent info
        event = {
            "event_type": event_type,
            "data": data.copy(),  # Copy to avoid modifying original
            "timestamp": time.time(),
            "agent": agent
        }
        
        # Add agent to data if provided (for backward compatibility)
        if agent:
            event["data"]["agent"] = agent
        
        # Store in recent events for logs endpoint
        with self._events_lock:
            self._recent_events.append(event)
            # Keep only the most recent events
            if len(self._recent_events) > self._max_events:
                self._recent_events.pop(0)
        
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
        }, agent="system")
        
        try:
            print(f"📝 Executing graph with real-time streaming...")
            
            # Use a sync bridge to call the async astream_events from our sync method
            final_result = None
            research_completed = False
            
            async def _stream_and_process():
                nonlocal final_result, research_completed
                async for event in self.graph.astream_events(initial_state, config=config, version="v1"):
                    kind = event["event"]
                    
                    if kind == "on_chain_start":
                        # A new node is starting to execute
                        node_name = event["name"]
                        print(f"🚀 Starting node: {node_name}")
                    
                    elif kind == "on_chain_stream":
                        # A streaming node is yielding a chunk
                        chunk = event["data"]["chunk"]
                        node_name = event.get("name", "unknown")
                        
                        if not chunk:
                            continue
                            
                        # Check for our custom token keys and include agent name
                        if "draft_answer_token" in chunk:
                            self._emit_event("draft_answer_token", {"token": chunk["draft_answer_token"]}, agent="synthesizer")
                        elif "criticism_token" in chunk:
                            self._emit_event("criticism_token", {"token": chunk["criticism_token"]}, agent="challenger")
                        elif "final_answer_token" in chunk:
                            self._emit_event("final_answer_token", {"token": chunk["final_answer_token"]}, agent="orchestrator")

                    elif kind == "on_chain_end":
                        # A node has finished executing
                        node_name = event["name"]
                        state_update = event["data"]["output"]
                        print(f"🔄 Processing node completion: {node_name}")
                        self._emit_node_completion_event(node_name, state_update)
                        final_result = state_update # Store the last complete state
            
            # Run the async generator, handling existing event loop safely
            try:
                # Check if we're already in an event loop
                asyncio.get_running_loop()
                # We're in an async context, so create a new thread with its own loop
                import concurrent.futures
                import threading
                
                def run_in_new_thread():
                    return asyncio.run(_stream_and_process())
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_new_thread)
                    future.result()
            except RuntimeError:
                # No event loop running, safe to use asyncio.run directly
                asyncio.run(_stream_and_process())

            print(f"📝 Graph execution completed")
            
            # Final check for success - but first check if we already emitted research_completed
            # If the publisher successfully completed with a final_answer, don't emit research_failed
            if not final_result or not final_result.get("final_answer"):
                # Double-check: look for any research_completed events in our event history
                # If research was actually completed, don't emit failure
                if not hasattr(self, '_research_completed_emitted') or not self._research_completed_emitted:
                    print(f"📝 Emitting research_failed event")
                    self._emit_event("research_failed", {
                        "error": "No final answer generated",
                        "status": "Research process failed to generate a final answer"
                    }, agent="system")
            else:
                 # This case is now handled by the 'publisher' node completion event
                 pass
            
            return final_result or {}
            
        except Exception as e:
            print(f"❌ Error in execute_sync: {e}")
            # Handle validation errors specifically
            if isinstance(e, ValueError):
                self._emit_event("validation_error", {
                    "error": str(e),
                    "status": "Question validation failed",
                    "suggestion": "Please rephrase your question to be more specific and research-worthy."
                }, agent="input_validator")
            else:
                self._emit_event("error", {
                    "error": str(e),
                    "status": "An error occurred during research"
                }, agent="system")
            raise
        finally:
            self._stop_event.set()

    def _emit_node_completion_event(self, node_name: str, state: Dict[str, Any]):
        """Emits a single event summarizing the completion of a node's work."""
        if not state:
            return

        # Allow all events through for presentation

        # Map node names to agent names for better frontend display
        agent_name = node_name.replace("_", " ").title()
        
        if node_name == "input_validator" and state.get("validated_question"):
            self._emit_event("question_validated", {
                "validated_question": state["validated_question"],
                "status": "Question validated and refined"
            }, agent="input_validator")
        elif node_name == "retriever" and state.get("documents"):
            self._emit_event("documents_retrieved", {
                "document_count": len(state["documents"]),
                "status": f"Retrieved {len(state['documents'])} relevant documents"
            }, agent="retriever")
        elif node_name == "synthesizer" and state.get("draft_answer"):
            self._emit_event("draft_generated", {
                "draft_length": len(state["draft_answer"]),
                "status": "Initial draft generated"
            }, agent="synthesizer")
        elif node_name == "challenger" and state.get("criticisms"):
            self._emit_event("criticisms_received", {
                "criticism_count": len(state["criticisms"]),
                "status": f"Received {len(state['criticisms'])} criticisms for improvement"
            }, agent="challenger")
        elif node_name == "orchestrator":
            decision = "unknown"
            if state.get("transcript") and len(state["transcript"]) > 0:
                latest_entry = state["transcript"][-1]
                if latest_entry.get("agent") == "Orchestrator":
                    decision = latest_entry.get("output", "unknown")
            
            self._emit_event("orchestrator_decision", {
                "decision": decision,
                "status": f"Orchestrator decided: {decision}"
            }, agent="orchestrator")
        elif node_name == "publisher" and state.get("final_answer"):
            self._research_completed_emitted = True
            self._emit_event("research_completed", {
                "final_answer": state["final_answer"],
                "status": "Research completed successfully"
            }, agent="publisher")
    
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
        
        print(f"🚀 UnifiedExecutor.execute_streaming called with question: {initial_state.question}")
        
        # Emit start event
        self._emit_event("research_started", {
            "question": initial_state.question,
            "task_id": config.get("configurable", {}).get("thread_id"),
            "status": "Starting research process..."
        }, agent="system")
        
        # Yield the start event  
        with self._events_lock:
            if self._recent_events:
                yield self._recent_events[-1]
        
        try:
            print(f"📝 Executing graph with async streaming...")
            
            # Track completion state  
            final_result = None
            
            # Use async graph streaming directly (no thread conflicts)
            async for event in self.graph.astream_events(initial_state, config=config, version="v1"):
                kind = event["event"]
                
                if kind == "on_chain_start":
                    # A new node is starting to execute
                    node_name = event["name"]
                    print(f"🚀 Starting node: {node_name}")
                
                elif kind == "on_chain_stream":
                    # A streaming node is yielding a chunk
                    chunk = event["data"]["chunk"]
                    node_name = event.get("name", "unknown")
                    
                    if not chunk:
                        continue
                        
                    # Check for our custom token keys and include agent name
                    if "draft_answer_token" in chunk:
                        self._emit_event("draft_answer_token", {"token": chunk["draft_answer_token"]}, agent="synthesizer")
                        # Yield immediately for real-time streaming
                        with self._events_lock:
                            if self._recent_events:
                                latest = self._recent_events[-1]
                                # Use content hash for better deduplication
                                content_hash = hash(json.dumps(latest, sort_keys=True))
                                if content_hash not in events_yielded:
                                    events_yielded.add(content_hash)
                                    yield latest
                    elif "criticism_token" in chunk:
                        self._emit_event("criticism_token", {"token": chunk["criticism_token"]}, agent="challenger")
                        # Yield immediately for real-time streaming
                        with self._events_lock:
                            if self._recent_events:
                                latest = self._recent_events[-1]
                                content_hash = hash(json.dumps(latest, sort_keys=True))
                                if content_hash not in events_yielded:
                                    events_yielded.add(content_hash)
                                    yield latest
                    elif "final_answer_token" in chunk:
                        self._emit_event("final_answer_token", {"token": chunk["final_answer_token"]}, agent="orchestrator")
                        # Yield immediately for real-time streaming
                        with self._events_lock:
                            if self._recent_events:
                                latest = self._recent_events[-1]
                                content_hash = hash(json.dumps(latest, sort_keys=True))
                                if content_hash not in events_yielded:
                                    events_yielded.add(content_hash)
                                    yield latest

                elif kind == "on_chain_end":
                    # A node has finished executing
                    node_name = event["name"]
                    state_update = event["data"]["output"]
                    print(f"🔄 Processing node completion: {node_name}")
                    self._emit_node_completion_event(node_name, state_update)
                    final_result = state_update # Store the last complete state
                    
                    # Yield events as they are stored
                    with self._events_lock:
                        if self._recent_events:
                            yield self._recent_events[-1]

            print(f"📝 Graph execution completed")
            
            # Final check for success
            if not final_result or not final_result.get("final_answer"):
                if not hasattr(self, '_research_completed_emitted') or not self._research_completed_emitted:
                    print(f"📝 Emitting research_failed event")
                    self._emit_event("research_failed", {
                        "error": "No final answer generated",
                        "status": "Research process failed to generate a final answer"
                    }, agent="system")
                    
                    # Yield the failure event
                    with self._events_lock:
                        if self._recent_events:
                            yield self._recent_events[-1]
            
        except Exception as e:
            print(f"❌ Error in execute_streaming: {e}")
            # Handle validation errors specifically
            if isinstance(e, ValueError):
                self._emit_event("validation_error", {
                    "error": str(e),
                    "status": "Question validation failed",
                    "suggestion": "Please rephrase your question to be more specific and research-worthy."
                }, agent="input_validator")
            else:
                self._emit_event("error", {
                    "error": str(e),
                    "status": "An error occurred during research"
                }, agent="system")
            
            # Yield the error event  
            with self._events_lock:
                if self._recent_events:
                    yield self._recent_events[-1]
            raise
        finally:
            self._stop_event.set()

# Create unified executor instance
unified_executor = UnifiedExecutor(kognys_graph) 