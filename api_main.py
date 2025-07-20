# api_main.py
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
from kognys.graph.unified_executor import unified_executor
from kognys.services.membase_client import register_agent_if_not_exists, get_paper_from_kb, get_papers_by_user_id
from kognys.services.error_handler import generate_error_response
from kognys.utils.aip_init import initialize_aip_agents

# Import time for timestamps
import time

def generate_paper_id(question: str, content: str) -> str:
    """Generates a consistent, unique ID for a paper."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, question + content))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- API STARTUP: REGISTERING AGENT ---")
    agent_id = os.getenv("MEMBASE_ID", "kognys_starter")
    is_registered = register_agent_if_not_exists(agent_id=agent_id)
    
    if os.getenv("ENABLE_AIP_AGENTS", "false").lower() == "true":
        initialize_aip_agents()

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
    user_id: str

class UserPapersResponse(BaseModel):
    user_id: str
    papers: list[UserPaper]

class StreamEvent(BaseModel):
    event_type: str
    data: dict
    timestamp: float

async def generate_sse_stream(question: str, user_id: str) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events stream for the research process."""
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = KognysState(question=question, user_id=user_id)
    
    # Store final result and paper ID
    final_result = None
    paper_id = None
    
    # Use the unified executor
    async for event in unified_executor.execute_streaming(initial_state, config):
        # Add paper_id to event data if we have one
        if paper_id:
            event["data"]["paper_id"] = paper_id
        
        # Check if this is the research_completed event to capture final result
        if event.get("event_type") == "research_completed" and event.get("data", {}).get("final_answer"):
            final_result = event["data"]["final_answer"]
            paper_id = generate_paper_id(question, final_result)
            event["data"]["paper_id"] = paper_id
        
        # Format as SSE with proper JSON serialization
        sse_data = f"data: {json.dumps(event)}\n\n"
        yield sse_data
    
    # Send final paper summary if we have a result
    if final_result and paper_id:
        final_event = {
            "event_type": "paper_generated",
            "data": {
                "paper_id": paper_id,
                "paper_content": final_result,
                "message": "Research paper successfully generated",
                "status": "completed"
            },
            "timestamp": time.time()
        }
        sse_data = f"data: {json.dumps(final_event)}\n\n"
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
    print(f"Request to get papers for user: {user_id}")

    papers_data = get_papers_by_user_id(user_id, top_k=limit)

    if not papers_data:
        raise HTTPException(status_code=404, detail=f"No papers found for user {user_id}.")

    user_papers = [
        UserPaper(
            paper_id=paper["paper_id"],
            original_question=paper["original_question"],
            user_id=paper["user_id"]
        ) for paper in papers_data
    ]
    
    return UserPapersResponse(user_id=user_id, papers=user_papers)