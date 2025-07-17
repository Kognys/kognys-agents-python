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

def add_knowledge_document(title: str, content: str, source_id: str) -> dict:
    """
    Adds a new document to the Membase Knowledge Base via the API.
    """
    if not API_KEY:
        raise ValueError("MEMBASE_API_KEY is not set in the environment.")

    add_url = f"{API_BASE_URL}/api/v1/knowledge/documents"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    
    # --- Start of Changes ---
    # Let's simplify the payload to only include the required fields,
    # matching our successful manual test.
    payload = {
        "title": title,
        "content": content
        # "category": "Generated Research",          # Temporarily commented out
        # "tags": ["kognys-agent"],                 # Temporarily commented out
        # "metadata": {"source_agent": "KognysResearchAgent", "original_source": source_id} # Temporarily commented out
    }
    # --- End of Changes ---

    try:
        response = requests.post(add_url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"---MEMBASE CLIENT: Successfully sent document '{title}' to API.---")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Membase Add Document API: {e}")
        return {}

def register_agent_if_not_exists(agent_id: str, name: str, description: str) -> bool:
    """
    Checks if an agent exists in Membase and registers it if it doesn't.
    Returns True if the agent exists or was created successfully, False otherwise.
    """
    if not API_KEY:
        raise ValueError("MEMBASE_API_KEY is not set in the environment.")

    agent_url = f"{API_BASE_URL}/api/v1/agents/{agent_id}"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    try:
        response = requests.get(agent_url, headers=headers)
        if response.status_code == 200:
            print(f"✅ Agent '{agent_id}' is already registered.")
            return True
    except requests.exceptions.RequestException as e:
        print(f"Could not check for agent, proceeding to create. Error: {e}")

    print(f"Agent '{agent_id}' not found. Attempting to register now...")
    create_url = f"{API_BASE_URL}/api/v1/agents/"
    payload = {
        "agent_id": agent_id,
        "name": name,
        "description": description,
        "capabilities": ["research", "synthesis", "debate"]
    }

    try:
        response = requests.post(create_url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"✅ Successfully registered new agent: '{agent_id}'")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to register agent '{agent_id}'. Error: {e}")
        print(f"   Response body: {response.text}")
        return False

def get_paper_by_title(title: str) -> dict | None:
    """
    Searches for a specific document by its title.
    Assumes the title is unique enough for a targeted search.
    """
    # Use the existing search function to find the paper
    results = search_knowledge_base(query=title, k=1)
    
    if results:
        # Return the first and most relevant result
        return results[0]
    
    return None
