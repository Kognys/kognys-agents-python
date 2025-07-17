# api_main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Your Kognys agent and state
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

# Your Membase client to save/retrieve results
from kognys.services.membase_client import add_knowledge_document, search_knowledge_base, register_agent_if_not_exists

# --- Initialize the FastAPI app ---
app = FastAPI(
    title="Kognys Research Agent API",
    description="An API to generate research papers and retrieve them from Unibase Membase."
)

# --- Define API Models (for request and response bodies) ---
class CreatePaperRequest(BaseModel):
    message: str
    user_id: str

class PaperResponse(BaseModel):
    paper_id: str
    paper_content: str

# --- Agent Registration on Startup ---
# This ensures the agent has an identity before the API starts accepting requests
@app.on_event("startup")
def startup_event():
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

# --- API Endpoints ---

@app.post("/papers", response_model=PaperResponse)
def create_paper(request: CreatePaperRequest):
    """
    Runs the Kognys agent to generate a research paper based on the user's message.
    """
    print(f"Received request from user '{request.user_id}' to research: '{request.message}'")
    
    # Set up the graph configuration for a unique run
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = KognysState(question=request.message)
    
    # Run the Kognys agent graph
    final_state_result = kognys_graph.invoke(initial_state, config=config)
    final_answer = final_state_result.get("final_answer")
    
    # Check if the agent succeeded
    if not final_answer or final_state_result.get("retrieval_status") == "No documents found":
        raise HTTPException(
            status_code=400, 
            detail="Agent could not generate a sufficient answer based on the provided query."
        )
        
    # We don't save the paper here, as the agent's Publisher node already handles it.
    # We just need to return the final answer. For the paper_id, we can use the thread_id.
    return PaperResponse(
        paper_id=config["configurable"]["thread_id"], # Use the thread_id as a unique ID for the paper
        paper_content=final_answer
    )

# --- How to Run This Server ---
# In your terminal, run the following command:
# uvicorn api_main:app --reload
