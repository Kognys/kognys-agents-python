import os
import requests

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

def search_semantic_scholar(query: str, k: int = 3) -> list[dict]:
    """
    Searches the Semantic Scholar API for papers related to the query.
    """
    params = {
        "query": query,
        "limit": k,
        "fields": "title,abstract,url"
    }
    
    try:
        # The 'headers' parameter is removed from this call
        response = requests.get(SEMANTIC_SCHOLAR_API_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("data", [])
        
        formatted_docs = []
        for paper in results:
            content = f"{paper.get('title', 'No title available.')}\n\nAbstract: {paper.get('abstract', '')}"
            formatted_docs.append({
                "source": paper.get('url', paper.get('paperId', 'No ID')),
                "content": content,
                "score": 1.0 # Relevance score is not directly provided in bulk search
            })
            
        return formatted_docs

    except requests.exceptions.RequestException as e:
        print(f"Error calling Semantic Scholar API: {e}")
        return []
