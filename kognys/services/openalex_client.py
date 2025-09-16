# kognys/services/openalex_client.py
import os
import requests
import asyncio
from typing import List, Dict, Optional
from kognys.services.cache_manager import cache_manager
from kognys.services.rate_limiter import rate_limit_manager, Priority

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
    Synchronous wrapper for backward compatibility.
    Creates a new event loop if needed.
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're in an async context, create a task
        future = asyncio.ensure_future(search_works_async(query, k))
        # This will block until complete, but that's okay for backward compatibility
        return loop.run_until_complete(future)
    except RuntimeError:
        # No event loop running, create one
        return asyncio.run(search_works_async(query, k))