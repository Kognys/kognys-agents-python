# kognys/services/membase_client.py
import os
import requests

# Load config from environment variables
API_BASE_URL = os.getenv("MEMBASE_API_URL", "https://kognys-membase-production.up.railway.app")
API_KEY = os.getenv("MEMBASE_API_KEY")

def search_knowledge_base(query: str, k: int = 5) -> list[dict]:
    """
    Searches the Membase Knowledge Base API and returns documents
    in the format expected by the Kognys agent.
    """
    if not API_KEY:
        raise ValueError("MEMBASE_API_KEY is not set in the environment.")

    search_url = f"{API_BASE_URL}/api/v1/knowledge/search"
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "limit": k
    }

    try:
        response = requests.post(search_url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        
        # Adapt the API response to the format our graph expects
        formatted_docs = []
        for res in results:
            doc = res.get("document", {})
            formatted_docs.append({
                "source": doc.get("document_id", "No ID"),
                "content": doc.get("title", "No title") + "\n" + doc.get("content_preview", ""),
                "score": res.get("score", 0.0)
            })
            
        return formatted_docs

    except requests.exceptions.RequestException as e:
        print(f"Error calling Membase Knowledge API: {e}")
        return []

# You can also add a function here to use the POST /documents endpoint for seeding
