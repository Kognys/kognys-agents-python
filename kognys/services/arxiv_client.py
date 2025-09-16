# kognys/services/arxiv_client.py
import requests
import xml.etree.ElementTree as ET
import asyncio
from typing import List, Dict, Optional
from kognys.services.cache_manager import cache_manager
from kognys.services.rate_limiter import rate_limit_manager, Priority
from kognys.services.sync_cache import sync_cache_manager

ARXIV_API_URL = "http://export.arxiv.org/api/query"

def _search_arxiv_api(query: str, k: int = 5) -> list[dict]:
    """Internal function to make the actual API call"""
    params = {"search_query": f'all:"{query}"', "start": 0, "max_results": k, "sortBy": "relevance"}
    try:
        response = requests.get(ARXIV_API_URL, params=params, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        formatted_docs = []
        ns = {'atom': 'http://www.w3.org/2005/Atom'} # Namespace for Atom feeds
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip()
            summary = entry.find('atom:summary', ns).text.strip()
            # The 'id' tag in arXiv's feed is the permalink URL
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

async def search_arxiv_async(query: str, k: int = 5, use_cache: bool = True, priority: Priority = Priority.NORMAL) -> list[dict]:
    """Async version with caching and rate limiting"""
    
    # Check cache first
    if use_cache:
        cached_results = await cache_manager.get("arxiv", query, k)
        if cached_results is not None:
            return cached_results
    
    # Apply rate limiting
    await rate_limit_manager.acquire("arxiv", priority)
    
    # Make the API call in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _search_arxiv_api, query, k)
    
    # Cache the results if we got any
    if results and use_cache:
        await cache_manager.set("arxiv", query, k, results)
    
    return results

def search_arxiv(query: str, k: int = 5) -> list[dict]:
    """
    Synchronous wrapper with caching support.
    """
    # Check cache first
    cached_results = sync_cache_manager.get("arxiv", query, k)
    if cached_results is not None:
        return cached_results
    
    # Make API call
    results = _search_arxiv_api(query, k)
    
    # Cache results
    if results:
        sync_cache_manager.set("arxiv", query, k, results)
    
    return results