# kognys/services/semantic_scholar_client.py
import requests

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

def search_semantic_scholar(query: str, k: int = 5) -> list[dict]:
    params = {"query": query, "limit": k, "fields": "title,abstract,url"}
    try:
        response = requests.get(SEMANTIC_SCHOLAR_API_URL, params=params)
        response.raise_for_status()
        results = response.json().get("data", [])
        
        # --- FIX: Standardize the output keys ---
        formatted_docs = []
        for paper in results:
            formatted_docs.append({
                "title": paper.get("title", "No Title Available"),
                "url": paper.get("url", "No URL Available"),
                "content": f"{paper.get('title', '')}\n\nAbstract: {paper.get('abstract', '')}",
                "source": "Semantic Scholar"
            })
        return formatted_docs
    except requests.exceptions.RequestException as e:
        print(f"Error calling Semantic Scholar API: {e}")
        return []