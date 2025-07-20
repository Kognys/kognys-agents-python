# api_main.py
import uuid
import os
import json
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables FIRST, before any other imports
load_dotenv()

from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState
from kognys.graph.unified_executor import unified_executor
from kognys.services.membase_client import register_agent_if_not_exists, get_paper_from_kb, get_papers_by_user_id
from kognys.services.error_handler import generate_error_response

# Import time for timestamps
import time

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

def generate_paper_id(question: str, content: str) -> str:
    """Generates a consistent, unique ID for a paper."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, question + content))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- API STARTUP: REGISTERING AGENT ---")
    agent_id = os.getenv("MEMBASE_ID", "kognys_starter")
    is_registered = register_agent_if_not_exists(agent_id=agent_id)
    
    if not is_registered:
        print("!!! WARNING: Agent registration failed. !!!")
    else:
        print("--- AGENT REGISTRATION COMPLETE ---")
    yield
    print("--- API SHUTDOWN ---")

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
    content: str
    user_id: str

class UserPapersResponse(BaseModel):
    user_id: str
    papers: list[UserPaper]
    total_count: int

class StreamEvent(BaseModel):
    event_type: str
    data: dict
    timestamp: float

async def generate_sse_stream(question: str, user_id: str) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events stream for the research process."""
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = KognysState(question=question, user_id=user_id)
    
    # Use the unified executor
    async for event in unified_executor.execute_streaming(initial_state, config):
        # Format as SSE with proper JSON serialization
        sse_data = f"data: {json.dumps(event)}\n\n"
        yield sse_data

# API Endpoints

@app.get("/", summary="Health Check")
def health_check():
    """Provides a simple health check endpoint."""
    return {"status": "ok"}

@app.post("/papers", response_model=PaperResponse)
def create_paper(request: CreatePaperRequest):
    """Initiates a new research task."""
    print(f"Received request from user '{request.user_id}' to research: '{request.message}'")
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = KognysState(question=request.message, user_id=request.user_id)
    
    final_state_result = None
    try:
        final_state_result = kognys_graph.invoke(initial_state, config=config)
    except ValueError as e:
        if "Question rejected by validator" in str(e):
            error_message = generate_error_response(
                error_type="VALIDATION_FAILED",
                original_question=request.message
            )
            raise HTTPException(status_code=400, detail=error_message)
        else:
            print(f"An unexpected ValueError occurred: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred in the agent.")

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
    print(f"Received streaming request from user '{request.user_id}' to research: '{request.message}'")
    
    return StreamingResponse(
        generate_sse_stream(request.message, request.user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.websocket("/ws/research")
async def websocket_research(websocket: WebSocket):
    """WebSocket endpoint for real-time research streaming with queue-based event handling."""
    await manager.connect(websocket)
    
    try:
        # Wait for the initial message with research parameters
        data = await websocket.receive_text()
        request_data = json.loads(data)
        
        question = request_data.get("message", "")
        user_id = request_data.get("user_id", "anonymous")
        
        print(f"WebSocket: Received research request from user '{user_id}' to research: '{question}'")
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to Kognys Research WebSocket",
                "question": question,
                "user_id": user_id
            },
            "timestamp": time.time()
        }))
        
        # Create thread-safe queue for events
        import queue
        event_queue = queue.Queue()
        
        # Set up event callback that puts events in queue
        def queue_event_callback(event_type: str, data: Dict[str, Any]):
            print(f"🔔 Queueing event: {event_type}")
            event_queue.put({
                "event_type": event_type,
                "data": data,
                "timestamp": time.time()
            })
        
        # Add callback to unified executor
        print(f"📝 Adding queue callback to unified executor")
        unified_executor.add_event_callback(queue_event_callback)
        print(f"📝 Callback added, total callbacks: {len(unified_executor.event_callbacks)}")
        
        # Execute research using unified executor in background
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        initial_state = KognysState(question=question, user_id=user_id)
        
        # Start research in background thread
        import threading
        research_result = {"final_result": None, "error": None}
        
        def run_research():
            try:
                print(f"🔧 Background thread: Starting research execution")
                result = unified_executor.execute_sync(initial_state, config)
                research_result["final_result"] = result
                print(f"🔧 Background thread: Research completed")
            except Exception as e:
                print(f"🔧 Background thread: Research failed: {e}")
                research_result["error"] = str(e)
                # Queue error event
                event_queue.put({
                    "event_type": "validation_error" if isinstance(e, ValueError) else "error",
                    "data": {
                        "error": str(e),
                        "status": "Research execution failed",
                        "suggestion": "Please try again or rephrase your question."
                    },
                    "timestamp": time.time()
                })
        
        research_thread = threading.Thread(target=run_research)
        research_thread.start()
        
        # Stream events to client as they arrive
        print(f"🚀 Starting event streaming loop...")
        while True:
            try:
                # Get event from queue with timeout
                event = event_queue.get(timeout=1.0)
                print(f"📤 Sending event to client: {event['event_type']}")
                
                # Send event to WebSocket client
                await websocket.send_text(json.dumps(event))
                
                # If this is a final event, break
                if event["event_type"] in ["research_completed", "research_failed", "error", "validation_error"]:
                    print(f"🏁 Final event sent: {event['event_type']}")
                    break
                    
            except queue.Empty:
                # Check if research thread is still running
                if not research_thread.is_alive():
                    print(f"🔚 Research thread finished, breaking event loop")
                    break
                continue
        
        # Wait for research thread to finish
        research_thread.join(timeout=5.0)
        
        # Send final completion message
        await websocket.send_text(json.dumps({
            "type": "research_completed",
            "data": {
                "message": "Research process completed",
                "status": "success"
            },
            "timestamp": time.time()
        }))
        
        print(f"✅ WebSocket research completed successfully")
        
    except WebSocketDisconnect:
        print("WebSocket: Client disconnected")
        manager.disconnect(websocket)
    except json.JSONDecodeError:
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {
                "error": "Invalid JSON format in request",
                "status": "error"
            },
            "timestamp": time.time()
        }))
    except Exception as e:
        print(f"WebSocket: Error during research: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {
                "error": str(e),
                "status": "error"
            },
            "timestamp": time.time()
        }))
        manager.disconnect(websocket)

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
    """Retrieves all research papers for a specific user."""
    print(f"Request to get papers for user: {user_id}")
    
    papers_data = get_papers_by_user_id(user_id, top_k=limit)
    
    # Convert to UserPaper models
    papers = [
        UserPaper(
            paper_id=paper["paper_id"],
            original_question=paper["original_question"],
            content=paper["content"],
            user_id=paper["user_id"]
        )
        for paper in papers_data
    ]
    
    return UserPapersResponse(
        user_id=user_id,
        papers=papers,
        total_count=len(papers)
    )