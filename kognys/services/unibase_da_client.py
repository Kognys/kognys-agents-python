# kognys/services/unibase_da_client.py
import os
import requests
import uuid

# The new Base URL for your partner's DA service
DA_SERVICE_URL = os.getenv("DA_SERVICE_URL")

def upload_paper_to_da(paper_content: str, original_question: str) -> dict:
    """
    Uploads the generated research paper directly to the new Unibase DA service.
    """
    owner_address = os.getenv("MEMBASE_ACCOUNT")
    if not owner_address:
        print("--- DA CLIENT: ERROR - MEMBASE_ACCOUNT environment variable not set. Cannot upload. ---")
        return {}

    upload_url = f"{DA_SERVICE_URL}/api/upload"
    
    # Use a unique identifier for the paper, like a hash of the content
    paper_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, original_question + paper_content))

    payload = {
        "id": paper_id,
        "owner": owner_address,
        "message": paper_content,
        "original_question": original_question
    }

    try:
        print(f"--- DA CLIENT: Uploading paper '{paper_id}' to the DA service... ---")
        response = requests.post(upload_url, json=payload)
        response.raise_for_status()

        response_data = response.json()
        print(f"--- DA CLIENT: Successfully uploaded paper to DA. Response: {response_data} ---")
        return response_data

    except requests.exceptions.RequestException as e:
        print(f"--- DA CLIENT: Error uploading to DA service: {e} ---")
        return {}

def download_paper_from_da(paper_id: str) -> dict | None:
    """
    Downloads a specific paper by its ID from the Unibase DA service.
    """
    owner_address = os.getenv("MEMBASE_ACCOUNT", "anonymous")
    download_url = f"{DA_SERVICE_URL}/api/download"
    
    params = {
        "name": paper_id,
        "owner": owner_address
    }

    try:
        print(f"--- DA CLIENT: Downloading paper '{paper_id}' from the DA service... ---")
        response = requests.get(download_url, params=params)
        response.raise_for_status()
        
        response_data = response.json().get("data", {})
        print(f"--- DA CLIENT: Successfully downloaded paper. ---")
        return response_data
        
    except requests.exceptions.RequestException as e:
        print(f"--- DA CLIENT: Error downloading from DA service: {e} ---")
        return None
