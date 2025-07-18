# kognys/services/unibase_da_client.py
import os
import requests
import uuid

# The public Unibase Hub URL from the documentation
DA_HUB_URL = "http://54.151.130.2:8080"

def upload_paper_to_da(paper_content: str, original_question: str) -> dict:
    """
    Uploads the generated research paper directly to the Unibase DA Hub.
    """
    # The Unibase docs specify an 'owner'. We'll use the MEMBASE_ACCOUNT
    # from your environment, which represents your agent's on-chain identity.
    owner_address = os.getenv("MEMBASE_ACCOUNT")
    if not owner_address:
        print("--- UNIBASE DA CLIENT: ERROR - MEMBASE_ACCOUNT environment variable not set. Cannot upload. ---")
        return {}

    upload_url = f"{DA_HUB_URL}/api/upload"
    
    # Generate a unique ID for this piece of content
    content_id = str(uuid.uuid4())

    # Construct the payload according to the Unibase documentation
    payload = {
        "id": content_id,
        "owner": owner_address,
        "message": paper_content
    }

    try:
        print(f"--- UNIBASE DA CLIENT: Uploading paper '{content_id}' to the DA Hub... ---")
        response = requests.post(upload_url, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes

        response_data = response.json()
        print(f"--- UNIBASE DA CLIENT: Successfully uploaded paper to DA. Response: {response_data} ---")
        return response_data

    except requests.exceptions.RequestException as e:
        print(f"--- UNIBASE DA CLIENT: Error uploading to DA Hub: {e} ---")
        return {}
