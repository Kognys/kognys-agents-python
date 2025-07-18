import requests
import xml.etree.ElementTree as ET

ARXIV_API_URL = "http://export.arxiv.org/api/query"

def search_arxiv(query: str, k: int = 3) -> list[dict]:
    """
    Searches the arXiv API for papers related to the query.
    """
    params = {
        "search_query": f'all:"{query}"',
        "start": 0,
        "max_results": k,
        "sortBy": "relevance"
    }
    
    try:
        response = requests.get(ARXIV_API_URL, params=params)
        response.raise_for_status()
        
        # Parse the XML response
        root = ET.fromstring(response.content)
        formatted_docs = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
            summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
            arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text
            
            formatted_docs.append({
                "source": arxiv_id,
                "content": f"{title}\n\nAbstract: {summary}",
                "score": 1.0 # arXiv API does not provide a relevance score
            })
            
        return formatted_docs

    except requests.exceptions.RequestException as e:
        print(f"Error calling arXiv API: {e}")
        return []
