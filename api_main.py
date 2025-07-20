# api_main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
from contextlib import asynccontextmanager
from kognys.services.membase_client import register_agent_if_not_exists, get_paper_from_kb

# Load environment variables
from dotenv import load_dotenv
load_dotenv() 

# Your Kognys agent and state
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

# Your service clients
from kognys.services.membase_client import register_agent_if_not_exists
from kognys.services.unibase_da_client import download_paper_from_da
from kognys.services.error_handler import generate_error_response

def generate_paper_id(question: str, content: str) -> str:
    """Generates a consistent, unique ID for a paper."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, question + content))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- API STARTUP: REGISTERING AGENT ---")
    agent_id = os.getenv("MEMBASE_ID", "kognys-api-agent-001")
    is_registered = register_agent_if_not_exists(
        agent_id=agent_id,
        name="Kognys API Research Agent",
        description="An autonomous agent that performs research via a REST API."
    )
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

# ── CORS ───────────────────────────────────────────────────────────────
# Allow your teammate’s local Vue/React dev server (port 8080) to hit this API.
# Add other origins (comma-separated) to ALLOWED_ORIGINS env var if needed.
origins = (
    os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    
    try:
        final_state_result = kognys_graph.invoke(initial_state, config=config)
    except ValueError as e:
        # --- THIS IS THE UPDATED LOGIC ---
        if "Question rejected by validator" in str(e):
            # Now, we call your custom error handler
            error_message = generate_error_response(
                error_type="VALIDATION_FAILED",
                original_question=request.message
            )
            raise HTTPException(status_code=400, detail=error_message)
        else:
            print(f"An unexpected ValueError occurred: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred in the agent.")

    final_answer = final_state_result.get("final_answer")
    
    if not final_answer or final_state_result.get("retrieval_status") == "No documents found":
        # We can also use the error handler here for consistency
        error_message = generate_error_response(
            error_type="NO_DOCUMENTS_FOUND",
            original_question=request.message
        )
        raise HTTPException(status_code=400, detail=error_message)
        
    paper_id = generate_paper_id(request.message, final_answer)

    from kognys.services.unibase_da_client import upload_paper_to_da
    upload_paper_to_da(
        paper_id=paper_id,
        paper_content=final_answer,
        original_question=request.message,
        transcript=final_state_result.get("transcript", []),
        source_documents=final_state_result.get("documents", [])
    )

    return PaperResponse(
        paper_id=paper_id,
        paper_content=final_answer
    )

@app.get("/papers/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: str):
    print(f"Request to get paper with ID: {paper_id}")
    
    paper_data = get_paper_from_kb(paper_id)
    
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found in Membase Knowledge Base.")
    
    return PaperResponse(
        paper_id=paper_data.get("id", paper_id),
        paper_content=paper_data.get("message", "Content not available.")
    )