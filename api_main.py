# api_main.py
from dotenv import load_dotenv
load_dotenv() 

import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState
from kognys.services.membase_client import register_agent_if_not_exists
from kognys.services.unibase_da_client import download_paper_from_da

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    print("--- API STARTUP: REGISTERING AGENT ---")
    agent_id = os.getenv("MEMBASE_ID", "kognys-api-agent-001")
    
    # This is the corrected function call with all required arguments
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

app = FastAPI(
    title="Kognys Research Agent API",
    description="An API to generate research papers and manage them with Unibase DA.",
    lifespan=lifespan
)

class CreatePaperRequest(BaseModel):
    message: str
    user_id: str

class PaperResponse(BaseModel):
    paper_id: str
    paper_content: str

@app.get("/", summary="Health Check")
def health_check():
    return {"status": "ok"}

@app.post("/papers", response_model=PaperResponse)
def create_paper(request: CreatePaperRequest):
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
    paper_data = download_paper_from_da(paper_id)
    
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found in Unibase DA.")
    
    return PaperResponse(
        paper_id=paper_data.get("id", paper_id),
        paper_content=paper_data.get("message", "Content not available.")
    )
