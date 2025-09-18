# api_main.py
# Force rebuild - removed unused import
import uuid
import os
import json
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables FIRST, before any other imports
load_dotenv()

from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

# Import transaction event system
from kognys.services.transaction_events import get_transaction_queue, get_transaction_event
from kognys.graph.unified_executor import unified_executor
from kognys.services.membase_client import register_agent_if_not_exists, get_paper_from_kb, get_papers_by_user_id
from kognys.services.error_handler import generate_error_response
from kognys.services.cache_manager import cache_manager
from kognys.utils.aip_init import initialize_aip_agents
from kognys.utils.address import normalize_address

# Import time for timestamps
import time

def generate_paper_id(question: str, content: str) -> str:
    """Generates a consistent, unique ID for a paper."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, question + content))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- API STARTUP: INITIALIZING SERVICES ---")
    
    # Initialize cache manager
    await cache_manager.connect()
    
    # Register agent
    agent_id = os.getenv("MEMBASE_ID", "kognys_starter")
    is_registered = register_agent_if_not_exists(agent_id=agent_id)
    
    if os.getenv("ENABLE_AIP_AGENTS", "false").lower() == "true":
        initialize_aip_agents()

    if not is_registered:
        print("!!! WARNING: Agent registration failed. !!!")
    else:
        print("--- AGENT REGISTRATION COMPLETE ---")
    
    print("--- ALL SERVICES INITIALIZED ---")
    yield
    
    # Cleanup on shutdown
    print("--- API SHUTDOWN: CLEANING UP ---")
    await cache_manager.disconnect()
    print("--- API SHUTDOWN COMPLETE ---")

app = FastAPI(
    title="Kognys Research Agent API",
    description="An API to generate research papers and manage them with Membase and Unibase DA.",
    lifespan=lifespan
)

# CORS Configuration
origins = (os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(","))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Models
class CreatePaperRequest(BaseModel):
    message: str
    user_id: str

class PaperResponse(BaseModel):
    paper_id: str
    paper_content: str

class UserPaper(BaseModel):
    paper_id: str
    original_question: str
    user_id: str

class UserPapersResponse(BaseModel):
    user_id: str
    papers: list[UserPaper]

class StreamEvent(BaseModel):
    event_type: str
    data: dict
    timestamp: float
    agent: str = None

class LogEvent(BaseModel):
    event_type: str
    data: dict
    timestamp: float
    agent: str

async def generate_sse_stream(question: str, user_id: str) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events stream for the research process with a heartbeat."""
    
    queue = asyncio.Queue()
    
    async def stream_executor():
        """Task to run the graph and put events into the queue."""
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        initial_state = KognysState(question=question, user_id=user_id)
        
        try:
            async for event in unified_executor.execute_streaming(initial_state, config):
                await queue.put(event)
        except Exception as e:
            # Put the exception in the queue to be handled by the main generator
            await queue.put(e)
        finally:
            # Signal completion
            await queue.put(None)

    async def heartbeat():
        """Task to send a heartbeat event every 15 seconds."""
        while True:
            try:
                await asyncio.sleep(15)
                heartbeat_event = {
                    "event_type": "heartbeat",
                    "data": {"status": "alive", "timestamp": time.time()},
                    "agent": "system"
                }
                await queue.put(heartbeat_event)
            except asyncio.CancelledError:
                break

    executor_task = asyncio.create_task(stream_executor())
    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            # Wait for an item from either task
            item = await queue.get()
            
            if item is None: # End of executor stream
                break
            
            if isinstance(item, Exception):
                # If the executor had an error, re-raise it
                raise item

            # Format and yield the event as SSE
            sse_data = f"data: {json.dumps(item)}\n\n"
            yield sse_data

    finally:
        # Clean up tasks
        executor_task.cancel()
        heartbeat_task.cancel()
        await asyncio.gather(executor_task, heartbeat_task, return_exceptions=True)

# API Endpoints

@app.get("/", summary="Health Check")
def health_check():
    """Provides a simple health check endpoint."""
    return {"status": "ok"}

@app.post("/papers", response_model=PaperResponse)
async def create_paper(request: CreatePaperRequest):
    """Initiates a new research task."""
    # Normalize user_id to lowercase if it's an Ethereum address
    normalized_user_id = normalize_address(request.user_id) or request.user_id
    print(f"Received request from user '{normalized_user_id}' to research: '{request.message}'")
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = KognysState(question=request.message, user_id=normalized_user_id)
    
    final_state_result = None
    try:
        final_state_result = await kognys_graph.ainvoke(initial_state, config=config)
    except ValueError as e:
        if "Question rejected by validator" in str(e):
            error_message = generate_error_response(
                error_type="VALIDATION_FAILED",
                original_question=request.message
            )
            raise HTTPException(status_code=400, detail=error_message)
        else:
            print(f"❌ Unexpected ValueError occurred: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            print(f"❌ Full error details: {repr(e)}")
            # For debugging: show the actual error in development
            error_detail = f"ValueError in agent processing: {str(e)}" if os.getenv("DEBUG_MODE", "false").lower() == "true" else "An unexpected error occurred in the agent."
            raise HTTPException(status_code=500, detail=error_detail)
    except Exception as e:
        print(f"❌ Unexpected exception occurred: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Full error details: {repr(e)}")
        # For debugging: show the actual error in development
        error_detail = f"Exception in agent processing: {str(e)}" if os.getenv("DEBUG_MODE", "false").lower() == "true" else "An unexpected error occurred in the agent."
        raise HTTPException(status_code=500, detail=error_detail)

    final_answer = final_state_result.get("final_answer")
    
    if not final_answer:
        error_message = generate_error_response(
            error_type="NO_DOCUMENTS_FOUND",
            original_question=request.message
        )
        raise HTTPException(status_code=400, detail=error_message)
        
    paper_id = generate_paper_id(request.message, final_answer)

    return PaperResponse(
        paper_id=paper_id,
        paper_content=final_answer
    )

@app.post("/papers/stream")
async def create_paper_stream(request: CreatePaperRequest):
    """Initiates a new research task with streaming updates via Server-Sent Events."""
    # Normalize user_id to lowercase if it's an Ethereum address
    normalized_user_id = normalize_address(request.user_id) or request.user_id
    print(f"Received streaming request from user '{normalized_user_id}' to research: '{request.message}'")
    
    return StreamingResponse(
        generate_sse_stream(request.message, normalized_user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/papers/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: str):
    """Retrieves a previously generated research paper."""
    print(f"Request to get paper with ID: {paper_id}")
    
    paper_data = get_paper_from_kb(paper_id)
    
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found in Membase Knowledge Base.")
    
    return PaperResponse(
        paper_id=paper_data.get("id", paper_id),
        paper_content=paper_data.get("message", "Content not available.")
    )

@app.get("/users/{user_id}/papers", response_model=UserPapersResponse)
def get_user_papers(user_id: str, limit: int = 10):
    """Retrieves all papers generated by a specific user."""
    # Normalize user_id to lowercase if it's an Ethereum address
    normalized_user_id = normalize_address(user_id) or user_id
    print(f"Request to get papers for user: {normalized_user_id}")

    papers_data = get_papers_by_user_id(normalized_user_id, top_k=limit)

    if not papers_data:
        raise HTTPException(status_code=404, detail=f"No papers found for user {normalized_user_id}.")

    user_papers = [
        UserPaper(
            paper_id=paper["paper_id"],
            original_question=paper["original_question"],
            user_id=paper["user_id"]  # This will already be normalized from the database
        ) for paper in papers_data
    ]
    
    return UserPapersResponse(user_id=normalized_user_id, papers=user_papers)

@app.get("/logs", response_model=list[LogEvent])
def get_recent_logs(limit: int = 50):
    """Retrieves recent system logs for debugging and monitoring."""
    print(f"Request for recent logs (limit: {limit})")
    
    try:
        recent_events = unified_executor.get_recent_events(limit)
        return recent_events
    except Exception as e:
        print(f"Error retrieving logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system logs")

@app.get("/logs/stream")
async def stream_system_logs():
    """Streams real-time system logs via Server-Sent Events."""
    print("Starting real-time log streaming...")
    
    async def generate_log_stream():
        """Generate SSE stream for system logs."""
        try:
            async for event in unified_executor.stream_recent_events():
                # Format as SSE with proper JSON serialization
                sse_data = f"data: {json.dumps(event)}\n\n"
                yield sse_data
        except Exception as e:
            print(f"Error in log streaming: {e}")
            error_event = {
                "event_type": "stream_error",
                "data": {"error": str(e)},
                "timestamp": time.time(),
                "agent": "system"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_log_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

# Transaction stream endpoint - DEPRECATED
# Transactions now come through the main /papers/stream endpoint via transaction_updated event
# Keeping this endpoint for backward compatibility but it won't receive events
@app.get("/transactions/stream")
async def stream_transaction_events(task_id: str = None):
    """[DEPRECATED] Streams blockchain transaction events via Server-Sent Events.

    Note: Transaction events are now sent through the main /papers/stream endpoint.
    This endpoint is kept for backward compatibility but won't receive new events.
    """
    print(f"[DEPRECATED] Transaction stream endpoint called (task_id: {task_id})")

    async def generate_transaction_stream():
        """Generate SSE stream for blockchain transaction events."""

        # Use the shared transaction event system

        try:
            # Send initial connection confirmation
            initial_event = {
                "event_type": "transaction_stream_connected",
                "data": {"status": "Transaction stream ready", "timestamp": time.time(), "task_id": task_id},
                "timestamp": time.time(),
                "agent": "system"
            }
            yield f"data: {json.dumps(initial_event)}\n\n"

            # Keep stream alive and listen for transaction events
            while True:
                try:
                    # Wait for transaction events with timeout
                    event = await get_transaction_event(timeout=30.0)
                    if event is None:
                        # Timeout occurred, send heartbeat
                        raise asyncio.TimeoutError()

                    print(f"📥 Received event from queue: {event.get('event_type')} for task: {event.get('data', {}).get('task_id')}")

                    # If task_id is specified, only send events for that task
                    if task_id:
                        event_task_id = event.get("data", {}).get("task_id")
                        if event_task_id != task_id:
                            # Skip events for other tasks
                            print(f"⏭️ Skipping event for different task. Expected: {task_id}, Got: {event_task_id}")
                            continue

                    # Format and yield the transaction event
                    sse_data = f"data: {json.dumps(event)}\n\n"
                    yield sse_data
                    print(f"📤 Sent transaction event: {event.get('event_type')} for task: {event.get('data', {}).get('task_id')}")
                    
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    heartbeat_event = {
                        "event_type": "transaction_heartbeat",
                        "data": {"status": "alive", "timestamp": time.time()},
                        "timestamp": time.time(),
                        "agent": "system"
                    }
                    yield f"data: {json.dumps(heartbeat_event)}\n\n"
                    
        except Exception as e:
            print(f"Error in transaction streaming: {e}")
            error_event = {
                "event_type": "transaction_stream_error",
                "data": {"error": str(e), "timestamp": time.time()},
                "timestamp": time.time(),
                "agent": "system"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
        finally:
            print(f"Transaction stream closed for task_id: {task_id}")
    
    return StreamingResponse(
        generate_transaction_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

