# kognys/services/openalex_client.py
import os
import requests

# It's good practice to identify your requests with an email
# See: https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication#the-polite-pool
MAILTO = os.getenv("API_MAILTO", "hello@kognys.com")
OPENALEX_API_URL = "https://api.openalex.org/works"

def search_works(query: str, k: int = 5) -> list[dict]:
    """
    Searches the OpenAlex API for works related to the query and returns
    them in the format expected by the Kognys agent.
    """
    params = {
        "search": query,
        "per-page": k,
        "mailto": MAILTO
    }
    
    try:
        response = requests.get(OPENALEX_API_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        results = data.get("results", [])
        
        # Format the results to match the structure our retriever expects
        formatted_docs = []
        for work in results:
            # For simplicity, we'll use the title as the main content.
            # The full abstract is available as an 'abstract_inverted_index'.
            content = work.get("title", "No title available.")
            
            formatted_docs.append({
                "source": work.get("id", "No ID"), # The OpenAlex ID
                "content": content,
                "score": work.get("relevance_score", 0.0)
            })
            
        return formatted_docs

    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenAlex API: {e}")
        return []
