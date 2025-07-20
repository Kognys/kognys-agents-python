# kognys/services/unibase_da_client.py
import os
import requests
import json
import time
from typing import List, Dict, Any
from kognys.utils.address import normalize_address

DA_SERVICE_URL = os.getenv("DA_SERVICE_URL")
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
    source_documents: List[Dict[str, Any]],
    user_id: str = None
) -> dict:
    """Uploads the complete research packet to the Unibase DA layer for archival."""
    if not DA_SERVICE_URL:
        print("--- DA CLIENT: ERROR - DA_SERVICE_URL not set. Skipping archival. ---")
        return {}

    upload_url = f"{DA_SERVICE_URL}/api/upload" 
    payload = {
        "id": paper_id,
        "owner": os.getenv("MEMBASE_ACCOUNT"),
        "final_answer": paper_content,
        "original_question": original_question,
        "debate_transcript": transcript,
        "source_documents": source_documents
    }
    
    # Add user_id to payload if provided
    if user_id:
        # Normalize user_id to lowercase if it's an Ethereum address
        normalized_user_id = normalize_address(user_id) or user_id
        payload["user_id"] = normalized_user_id

    start_time = time.time()
    payload_size = len(json.dumps(payload).encode('utf-8'))

    print(f"\n--- 🗄️ Archiving Research Packet to Unibase DA ---")
    print(f"  - Endpoint: POST {upload_url}")
    print(f"  - Data Size: {payload_size / 1024:.2f} KB")

    try:
        response = requests.post(upload_url, headers=_get_headers(), json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        duration = time.time() - start_time
        print(f"  - ✅ Success ({response.status_code}) | Took {duration:.2f} seconds")
        return response_data
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        print(f"  - ❌ FAILED | Took {duration:.2f} seconds | Error: {e}")
        return {}

def retrieve_archived_packet(paper_id: str) -> dict | None:
    # Your existing download logic can go here if needed for the API
    pass
