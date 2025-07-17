# api_main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import os
from contextlib import asynccontextmanager

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv() 

# Your Kognys agent and state
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

# Your Membase client to save/retrieve results, including the new function
from kognys.services.membase_client import (
    add_knowledge_document, 
    search_knowledge_base, 
    register_agent_if_not_exists,
    get_paper_by_title
)

# This context manager handles startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    print("--- API STARTUP: REGISTERING AGENT ---")
    agent_id = os.getenv("MEMBASE_ID", "kognys-api-agent-001")
    is_registered = register_agent_if_not_exists(
        agent_id=agent_id,
        name="Kognys API Research Agent",
        description="An autonomous agent that performs research via a REST API."
    )
    if not is_registered:
        print("!!! WARNING: Agent registration failed. API might not function correctly. !!!")
    else:
        print("--- AGENT REGISTRATION COMPLETE ---")
    
    yield
    # This code runs on shutdown
    print("--- API SHUTDOWN ---")

# Initialize the FastAPI app with the new lifespan manager
app = FastAPI(
    title="Kognys Research Agent API",
    description="An API to generate research papers and retrieve them from Unibase Membase.",
    lifespan=lifespan
)

# --- Define API Models ---
class CreatePaperRequest(BaseModel):
    message: str
    user_id: str

class PaperResponse(BaseModel):
    paper_id: str
    paper_content: str
    user_id: str | None = None

# --- API Endpoints ---

@app.post("/papers", response_model=PaperResponse)
def create_paper(request: CreatePaperRequest):
    """
    Runs the Kognys agent to generate a research paper based on the user's message.
    The result is automatically saved to Membase by the agent's Publisher node.
    """
    print(f"Received request from user '{request.user_id}' to research: '{request.message}'")
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = KognysState(question=request.message)
    
    final_state_result = kognys_graph.invoke(initial_state, config=config)
    final_answer = final_state_result.get("final_answer")
    
    if not final_answer or final_state_result.get("retrieval_status") == "No documents found":
        raise HTTPException(
            status_code=400, 
            detail="Agent could not generate a sufficient answer based on the provided query."
        )
        
    return PaperResponse(
        paper_id=config["configurable"]["thread_id"], # Use the thread_id as a unique ID for this run
        paper_content=final_answer
    )

@app.get("/papers/{paper_title}", response_model=PaperResponse)
def get_paper(paper_title: str):
    """
    Retrieves a specific paper by its title from the Membase Knowledge Base.
    """
    print(f"Received request to get paper with title: {paper_title}")
    
    paper = get_paper_by_title(paper_title)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found in the knowledge base.")
    
    return PaperResponse(
        paper_id=paper.get("source", paper_title),
        paper_content=paper.get("content", "Content not available.")
    )

# To run this server, use the command:
# python -m uvicorn api_main:app --reload
