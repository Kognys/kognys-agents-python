# kognys/services/openalex_client.py
import os
import requests
import asyncio
from typing import List, Dict, Optional
from kognys.services.cache_manager import cache_manager
from kognys.services.rate_limiter import rate_limit_manager, Priority
from kognys.services.sync_cache import sync_cache_manager

MAILTO = os.getenv("API_MAILTO", "hello@kognys.com")
OPENALEX_API_URL = "https://api.openalex.org/works"

def _search_works_api(query: str, k: int = 5) -> list[dict]:
    """Internal function to make the actual API call"""
    params = {"search": query, "per-page": k, "mailto": MAILTO}
    try:
        response = requests.get(OPENALEX_API_URL, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        
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

async def search_works_async(query: str, k: int = 5, use_cache: bool = True, priority: Priority = Priority.NORMAL) -> list[dict]:
    """Async version with caching and rate limiting"""
    
    # Check cache first
    if use_cache:
        cached_results = await cache_manager.get("openalex", query, k)
        if cached_results is not None:
            return cached_results
    
    # Apply rate limiting
    await rate_limit_manager.acquire("openalex", priority)
    
    # Make the API call in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _search_works_api, query, k)
    
    # Cache the results if we got any
    if results and use_cache:
        await cache_manager.set("openalex", query, k, results)
    
    return results

def search_works(query: str, k: int = 5) -> list[dict]:
    """
    Synchronous wrapper with caching support.
    """
    # Check cache first
    cached_results = sync_cache_manager.get("openalex", query, k)
    if cached_results is not None:
        return cached_results
    
    # Make API call
    results = _search_works_api(query, k)
    
    # Cache results
    if results:
        sync_cache_manager.set("openalex", query, k, results)
    
    return results