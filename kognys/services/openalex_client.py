# kognys/services/openalex_client.py
import os
import requests

MAILTO = os.getenv("API_MAILTO", "hello@kognys.com")
OPENALEX_API_URL = "https://api.openalex.org/works"

def search_works(query: str, k: int = 5) -> list[dict]:
    """Searches OpenAlex and returns documents in a standardized format."""
    params = {"search": query, "per-page": k, "mailto": MAILTO}
    try:
        response = requests.get(OPENALEX_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        
        # --- FIX: Standardize the output keys ---
        formatted_docs = []
        for work in results:
            formatted_docs.append({
                "title": work.get("title", "No Title Available"),
                "url": work.get("doi", work.get("id")),
                "content": work.get("title", ""),
                "source": "OpenAlex"
            })
        return formatted_docs
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenAlex API: {e}")
        return []
