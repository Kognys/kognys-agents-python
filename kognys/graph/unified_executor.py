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
                        if not chunk:
                            continue
                            
                        # Check for our custom token keys
                        if "draft_answer_token" in chunk:
                            self._emit_event("draft_answer_token", {"token": chunk["draft_answer_token"]})
                        elif "criticism_token" in chunk:
                            self._emit_event("criticism_token", {"token": chunk["criticism_token"]})
                        elif "final_answer_token" in chunk:
                            self._emit_event("final_answer_token", {"token": chunk["final_answer_token"]})

                    elif kind == "on_chain_end":
                        # A node has finished executing
                        node_name = event["name"]
                        state_update = event["data"]["output"]
                        print(f"🔄 Processing node completion: {node_name}")
                        self._emit_node_completion_event(node_name, state_update)
                        final_result = state_update # Store the last complete state
            
            # Run the async generator from our synchronous context
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
                    })
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
                })
            else:
                self._emit_event("error", {
                    "error": str(e),
                    "status": "An error occurred during research"
                })
            raise
        finally:
            self._stop_event.set()

    def _emit_node_completion_event(self, node_name: str, state: Dict[str, Any]):
        """Emits a single event summarizing the completion of a node's work."""
        if not state:
            return

        if node_name == "input_validator" and state.get("validated_question"):
            self._emit_event("question_validated", {
                "validated_question": state["validated_question"],
                "status": "Question validated and refined"
            })
        elif node_name == "retriever" and state.get("documents"):
            self._emit_event("documents_retrieved", {
                "document_count": len(state["documents"]),
                "status": f"Retrieved {len(state['documents'])} relevant documents"
            })
        elif node_name == "synthesizer" and state.get("draft_answer"):
            self._emit_event("draft_generated", {
                "draft_length": len(state["draft_answer"]),
                "status": "Initial draft generated"
            })
        elif node_name == "challenger" and state.get("criticisms"):
            self._emit_event("criticisms_received", {
                "criticism_count": len(state["criticisms"]),
                "status": f"Received {len(state['criticisms'])} criticisms for improvement"
            })
        elif node_name == "orchestrator":
            decision = "unknown"
            if state.get("transcript") and len(state["transcript"]) > 0:
                latest_entry = state["transcript"][-1]
                if latest_entry.get("agent") == "Orchestrator":
                    decision = latest_entry.get("output", "unknown")
            
            self._emit_event("orchestrator_decision", {
                "decision": decision,
                "status": f"Orchestrator decided: {decision}"
            })
        elif node_name == "publisher" and state.get("final_answer"):
            self._research_completed_emitted = True
            self._emit_event("research_completed", {
                "final_answer": state["final_answer"],
                "status": "Research completed successfully"
            })
    
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
        yield {
            "event_type": "research_started",
            "data": {
                "question": initial_state.question,
                "task_id": config.get("configurable", {}).get("thread_id"),
                "status": "Starting research process..."
            },
            "timestamp": time.time()
        }
        
        try:
            print(f"📝 Executing graph with async streaming...")
            
            final_result = None
            
            # Use astream_events directly in the async context (no new event loop)
            async for event in self.graph.astream_events(initial_state, config=config, version="v1"):
                kind = event["event"]
                
                if kind == "on_chain_start":
                    # A new node is starting to execute
                    node_name = event["name"]
                    print(f"🚀 Starting node: {node_name}")
                
                elif kind == "on_chain_stream":
                    # A streaming node is yielding a chunk
                    chunk = event["data"]["chunk"]
                    if not chunk:
                        continue
                        
                    # Check for our custom token keys and stream them
                    if "draft_answer_token" in chunk:
                        yield {
                            "event_type": "draft_answer_token",
                            "data": {"token": chunk["draft_answer_token"]},
                            "timestamp": time.time()
                        }
                    elif "criticism_token" in chunk:
                        yield {
                            "event_type": "criticism_token", 
                            "data": {"token": chunk["criticism_token"]},
                            "timestamp": time.time()
                        }
                    elif "final_answer_token" in chunk:
                        yield {
                            "event_type": "final_answer_token",
                            "data": {"token": chunk["final_answer_token"]}, 
                            "timestamp": time.time()
                        }

                elif kind == "on_chain_end":
                    # A node has finished executing
                    node_name = event["name"]
                    state_update = event["data"]["output"]
                    print(f"🔄 Processing node completion: {node_name}")
                    
                    # Emit node completion events
                    completion_event = self._get_node_completion_event(node_name, state_update)
                    if completion_event:
                        yield completion_event
                    
                    final_result = state_update # Store the last complete state
            
            print(f"📝 Async graph execution completed")
            
            # Final check for success
            if not final_result or not final_result.get("final_answer"):
                yield {
                    "event_type": "research_failed",
                    "data": {
                        "error": "No final answer generated",
                        "status": "Research process failed to generate a final answer"
                    },
                    "timestamp": time.time()
                }
            
        except Exception as e:
            print(f"❌ Error in execute_streaming: {e}")
            # Handle validation errors specifically
            if isinstance(e, ValueError):
                yield {
                    "event_type": "validation_error",
                    "data": {
                        "error": str(e),
                        "status": "Question validation failed",
                        "suggestion": "Please rephrase your question to be more specific and research-worthy."
                    },
                    "timestamp": time.time()
                }
            else:
                yield {
                    "event_type": "error",
                    "data": {
                        "error": str(e),
                        "status": "An error occurred during research"
                    },
                    "timestamp": time.time()
                }
                
    def _get_node_completion_event(self, node_name: str, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the appropriate completion event for a node."""
        if not state:
            return None

        event_data = {"timestamp": time.time()}

        if node_name == "input_validator" and state.get("validated_question"):
            event_data.update({
                "event_type": "question_validated",
                "data": {
                    "validated_question": state["validated_question"],
                    "status": "Question validated and refined"
                }
            })
        elif node_name == "retriever" and state.get("documents"):
            event_data.update({
                "event_type": "documents_retrieved",
                "data": {
                    "document_count": len(state["documents"]),
                    "status": f"Retrieved {len(state['documents'])} relevant documents"
                }
            })
        elif node_name == "synthesizer" and state.get("draft_answer"):
            event_data.update({
                "event_type": "draft_generated",
                "data": {
                    "draft_length": len(state["draft_answer"]),
                    "status": "Initial draft generated"
                }
            })
        elif node_name == "challenger" and state.get("criticisms"):
            event_data.update({
                "event_type": "criticisms_received",
                "data": {
                    "criticism_count": len(state["criticisms"]),
                    "status": f"Received {len(state['criticisms'])} criticisms for improvement"
                }
            })
        elif node_name == "orchestrator":
            decision = "unknown"
            if state.get("transcript") and len(state["transcript"]) > 0:
                latest_entry = state["transcript"][-1]
                if latest_entry.get("agent") == "Orchestrator":
                    decision = latest_entry.get("output", "unknown")
            
            event_data.update({
                "event_type": "orchestrator_decision",
                "data": {
                    "decision": decision,
                    "status": f"Orchestrator decided: {decision}"
                }
            })
        elif node_name == "publisher" and state.get("final_answer"):
            event_data.update({
                "event_type": "research_completed",
                "data": {
                    "final_answer": state["final_answer"],
                    "status": "Research completed successfully"
                }
            })
        else:
            return None
            
        return event_data

# Create unified executor instance
unified_executor = UnifiedExecutor(kognys_graph) 