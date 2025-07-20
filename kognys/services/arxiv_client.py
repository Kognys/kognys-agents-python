# kognys/services/arxiv_client.py
import requests
import xml.etree.ElementTree as ET

ARXIV_API_URL = "http://export.arxiv.org/api/query"

def search_arxiv(query: str, k: int = 5) -> list[dict]:
    """Searches the arXiv API and returns documents in a standardized format."""
    params = {"search_query": f'all:"{query}"', "start": 0, "max_results": k, "sortBy": "relevance"}
    try:
        response = requests.get(ARXIV_API_URL, params=params)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        # --- FIX: Standardize the output keys ---
        formatted_docs = []
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip()
            summary = entry.find('atom:summary', ns).text.strip()
            # The 'id' tag often contains the URL to the abstract page
            url = entry.find('atom:id', ns).text
            
            formatted_docs.append({
                "title": title,
                "url": url,
                "content": f"{title}\n\nAbstract: {summary}",
                "source": "arXiv"
            })
        return formatted_docs
    except requests.exceptions.RequestException as e:
        print(f"Error calling arXiv API: {e}")
        return []
