# kognys/services/unibase_da_client.py
import os
import requests
from typing import List, Dict, Any

DA_SERVICE_URL = os.getenv("DA_SERVICE_URL")
# Assuming the DA service uses the same API key, otherwise it needs its own env var
API_KEY = os.getenv("MEMBASE_API_KEY") 

def _get_headers() -> dict:
    if not API_KEY:
        raise ValueError("API key for DA service not set.")
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def archive_research_packet(
    paper_id: str,
    paper_content: str,
    original_question: str,
    transcript: List[Dict[str, Any]],
    source_documents: List[Dict[str, Any]]
) -> dict:
    """Uploads the complete research packet to the Unibase DA layer for archival."""
    if not DA_SERVICE_URL:
        print("--- DA CLIENT: ERROR - DA_SERVICE_URL not set. Skipping archival. ---")
        return {}

    # This assumes a simple upload endpoint. Change if your DA service API is different.
    upload_url = f"{DA_SERVICE_URL}/api/upload" 
    payload = {
        "id": paper_id,
        "owner": os.getenv("MEMBASE_ACCOUNT"),
        "final_answer": paper_content,
        "original_question": original_question,
        "debate_transcript": transcript,
        "source_documents": source_documents
    }
    try:
        print(f"--- DA CLIENT: Archiving research packet '{paper_id}'... ---")
        response = requests.post(upload_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        response_data = response.json()
        print(f"--- DA CLIENT: Successfully archived packet. Response: {response_data} ---")
        return response_data
    except requests.exceptions.RequestException as e:
        print(f"--- DA CLIENT: Error archiving to DA service: {e}")
        return {}

def retrieve_archived_packet(paper_id: str) -> dict | None:
    # Your existing download logic can go here if needed for the API
    pass
