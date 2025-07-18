# api_main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import os
from contextlib import asynccontextmanager

# Load environment variables
from dotenv import load_dotenv
load_dotenv() 

# Your Kognys agent and state
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

# Import the new DA client and the agent registration function
from kognys.services.unibase_da_client import download_paper_from_da
from kognys.services.membase_client import register_agent_if_not_exists

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This startup logic can remain the same
    print("--- API STARTUP: REGISTERING AGENT ---")
    agent_id = os.getenv("MEMBASE_ID", "kognys-api-agent-001")
    is_registered = register_agent_if_not_exists(...)
    if not is_registered:
        print("!!! WARNING: Agent registration failed. !!!")
    else:
        print("--- AGENT REGISTRATION COMPLETE ---")
    yield
    print("--- API SHUTDOWN ---")

app = FastAPI(
    title="Kognys Research Agent API",
    description="An API to generate research papers and manage them with Unibase DA.",
    lifespan=lifespan
)

# --- API Models ---
class CreatePaperRequest(BaseModel):
    message: str
    user_id: str

class PaperResponse(BaseModel):
    paper_id: str
    paper_content: str

# --- API Endpoints ---
@app.get("/", summary="Health Check")
def health_check():
    return {"status": "ok"}

@app.post("/papers", response_model=PaperResponse)
def create_paper(request: CreatePaperRequest):
    print(f"Received request from user '{request.user_id}' to research: '{request.message}'")
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = KognysState(question=request.message)
    
    final_state_result = kognys_graph.invoke(initial_state, config=config)
    final_answer = final_state_result.get("final_answer")
    
    if not final_answer or final_state_result.get("retrieval_status") == "No documents found":
        raise HTTPException(status_code=400, detail="Agent could not generate an answer.")
        
    return PaperResponse(
        paper_id=config["configurable"]["thread_id"],
        paper_content=final_answer
    )

@app.get("/papers/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: str):
    """
    Retrieves a specific paper by its ID from the Unibase DA service.
    """
    print(f"Request to get paper with ID: {paper_id}")
    
    paper_data = download_paper_from_da(paper_id)
    
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found in Unibase DA.")
    
    return PaperResponse(
        paper_id=paper_data.get("id", paper_id),
        paper_content=paper_data.get("message", "Content not available.")
    )
