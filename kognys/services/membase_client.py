# kognys/services/membase_client.py
import os
import requests
import json
from typing import List, Dict, Any

API_BASE_URL = os.getenv("MEMBASE_API_URL")
API_KEY = os.getenv("MEMBASE_API_KEY")

def _get_headers() -> dict:
    if not API_KEY:
        raise ValueError("MEMBASE_API_KEY is not set in the environment.")
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def register_agent_if_not_exists(agent_id: str) -> bool:
    """Registers an agent on the blockchain via the Membase API."""
    try:
        check_url = f"{API_BASE_URL}/api/v1/agents/{agent_id}"
        response = requests.get(check_url, headers=_get_headers())
        if response.status_code == 200:
            print(f"✅ Agent '{agent_id}' is already registered.")
            return True
    except requests.exceptions.RequestException:
        pass

    register_url = f"{API_BASE_URL}/api/v1/agents/register"
    payload = {"agent_id": agent_id}
    try:
        response = requests.post(register_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print(f"✅ Successfully registered agent '{agent_id}' on-chain.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to register agent '{agent_id}'. Error: {e}")
        return False

def store_final_answer_in_kb(paper_id: str, paper_content: str, original_question: str) -> bool:
    """Stores the final answer in the Membase Knowledge Base to make it searchable."""
    kb_url = f"{API_BASE_URL}/api/v1/knowledge/documents"
    
    document = {
        "content": paper_content, 
        "metadata": {"paper_id": paper_id, "original_question": original_question}
    }
    
    # --- THIS IS THE FIX ---
    # Reverting to the list-based payload. The server error "'NoneType' is not iterable"
    # strongly implies it is designed to loop through a list of documents.
    payload = {"documents": [document]} 
    
    try:
        print(f"--- MEMBASE CLIENT: Storing final answer for paper '{paper_id}' in KB... ---")
        response = requests.post(kb_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print("--- MEMBASE CLIENT: Successfully stored in KB. ---")
        return True
    except requests.exceptions.RequestException as e:
        print(f"--- MEMBASE CLIENT: ERROR storing in KB: {e} ---")
        # Added more detailed error logging to help debug if it fails again
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"   Response Body: {response.text}")
        return False
    
def store_transcript_in_memory(paper_id: str, transcript: List[Dict[str, Any]]) -> bool:
    """Stores the debate transcript as a conversation in Membase."""
    convo_url = f"{API_BASE_URL}/api/v1/memory/conversations/{paper_id}/messages"
    
    # --- FIX: Transform our internal transcript to the Membase message format ---
    membase_messages = []
    for entry in transcript:
        membase_messages.append({
            "name": entry.get("agent", "system"),
            "content": f"{entry.get('action', '')}: {entry.get('details', '') or entry.get('output', '')}",
            "role": "assistant" # Use a consistent role for agent actions
        })
        
    payload = {"messages": membase_messages}
    
    try:
        print(f"--- MEMBASE CLIENT: Storing transcript for paper '{paper_id}'... ---")
        requests.post(f"{API_BASE_URL}/api/v1/memory/conversations", json={"conversation_id": paper_id}, headers=_get_headers())
        response = requests.post(convo_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print("--- MEMBASE CLIENT: Successfully stored transcript. ---")
        return True
    except requests.exceptions.RequestException as e:
        print(f"--- MEMBASE CLIENT: ERROR storing transcript: {e} ---")
        print(f"   Response Body: {response.text if 'response' in locals() else 'No Response'}")
        return False

def get_paper_from_kb(paper_id: str) -> dict | None:
    """Retrieves a paper from the Membase Knowledge Base by its paper_id metadata."""
    search_url = f"{API_BASE_URL}/api/v1/knowledge/documents/search"
    metadata_filter = json.dumps({"paper_id": paper_id})
    params = {"query": paper_id, "metadata_filter": metadata_filter, "top_k": 1}
    try:
        print(f"--- MEMBASE CLIENT: Searching for paper '{paper_id}' in KB... ---")
        response = requests.get(search_url, headers=_get_headers(), params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return None
        document = results[0].get("document", {})
        return {
            "id": document.get("metadata", {}).get("paper_id", paper_id),
            "message": document.get("content", "Content not available.")
        }
    except requests.exceptions.RequestException as e:
        print(f"--- MEMBASE CLIENT: Error searching for paper: {e} ---")
        return None
