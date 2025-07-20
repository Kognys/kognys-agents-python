# kognys/services/membase_client.py
import os
import requests
import json
import time
from typing import List, Dict, Any

API_BASE_URL = os.getenv("MEMBASE_API_URL")
API_KEY = os.getenv("MEMBASE_API_KEY")

def _get_headers() -> dict:
    if not API_KEY:
        raise ValueError("MEMBASE_API_KEY is not set in the environment.")
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def register_agent_if_not_exists(agent_id: str) -> bool:
    """Registers an agent on the blockchain via the Membase API."""
    try:
        check_url = f"{API_BASE_URL}/api/v1/agents/{agent_id}"
        response = requests.get(check_url, headers=_get_headers())
        if response.status_code == 200:
            print(f"✅ Agent '{agent_id}' is already registered.")
            return True
    except requests.exceptions.RequestException:
        pass

    register_url = f"{API_BASE_URL}/api/v1/agents/register"
    payload = {"agent_id": agent_id}
    try:
        response = requests.post(register_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print(f"✅ Successfully registered agent '{agent_id}' on-chain.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to register agent '{agent_id}'. Error: {e}")
        return False

def create_task(task_id: str, price: int = 1000) -> bool:
    """Creates a new task on the blockchain via the Membase API."""
    task_url = f"{API_BASE_URL}/api/v1/tasks/create"
    payload = {"task_id": task_id, "price": price}
    
    print(f"\n--- ⛓️ Creating On-Chain Task ---")
    print(f"  - Endpoint: POST {task_url}")

    try:
        response = requests.post(task_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print(f"  - ✅ Success: Task '{task_id}' created.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not create task '{task_id}'. Error: {e}")
        return False

def join_task(task_id: str, agent_id: str) -> bool:
    """Joins an existing task on the blockchain."""
    task_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}/join"
    payload = {"agent_id": agent_id}
    
    print(f"\n--- 🙋 Joining On-Chain Task ---")
    print(f"  - Endpoint: POST {task_url}")
    
    try:
        response = requests.post(task_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print(f"  - ✅ Success: Agent '{agent_id}' joined task '{task_id}'.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Agent '{agent_id}' could not join task '{task_id}'. Error: {e}")
        return False

def finish_task(task_id: str, agent_id: str) -> bool:
    """Marks a task as finished on the blockchain."""
    task_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}/finish"
    payload = {"agent_id": agent_id}
    
    print(f"\n--- ✅ Finishing On-Chain Task ---")
    print(f"  - Endpoint: POST {task_url}")

    try:
        response = requests.post(task_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print(f"  - ✅ Success: Task '{task_id}' finished by agent '{agent_id}'.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not finish task '{task_id}'. Error: {e}")
        return False

def store_final_answer_in_kb(paper_id: str, paper_content: str, original_question: str) -> bool:
    """Stores the final answer in the Membase Knowledge Base to make it searchable."""
    kb_url = f"{API_BASE_URL}/api/v1/knowledge/documents"
    document = {"content": paper_content, "metadata": {"paper_id": paper_id, "original_question": original_question}}
    payload = {"documents": [document]}
    
    start_time = time.time()
    payload_size = len(json.dumps(payload).encode('utf-8'))
    
    print(f"\n--- 📤 Storing Final Answer in Membase KB ---")
    print(f"  - Endpoint: POST {kb_url}")
    print(f"  - Data Size: {payload_size / 1024:.2f} KB")

    try:
        response = requests.post(kb_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        duration = time.time() - start_time
        print(f"  - ✅ Success ({response.status_code}) | Took {duration:.2f} seconds")
        return True
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        print(f"  - ❌ FAILED | Took {duration:.2f} seconds | Error: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"     Response Body: {response.text}")
        return False

def store_transcript_in_memory(paper_id: str, transcript: List[Dict[str, Any]]) -> bool:
    """Stores the debate transcript as a conversation in Membase."""
    convo_url = f"{API_BASE_URL}/api/v1/memory/conversations/{paper_id}/messages"
    membase_messages = [{"name": e.get("agent", "system"), "content": f"{e.get('action', '')}: {e.get('details', '') or e.get('output', '')}", "role": "assistant"} for e in transcript]
    payload = {"messages": membase_messages}
    
    start_time = time.time()
    payload_size = len(json.dumps(payload).encode('utf-8'))

    print(f"\n--- 📤 Storing Transcript in Membase Conversations ---")
    print(f"  - Endpoint: POST {convo_url}")
    print(f"  - Data Size: {payload_size / 1024:.2f} KB")

    try:
        # First, ensure the conversation exists
        requests.post(f"{API_BASE_URL}/api/v1/memory/conversations", json={"conversation_id": paper_id}, headers=_get_headers())
        # Then, add the messages
        response = requests.post(convo_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        duration = time.time() - start_time
        print(f"  - ✅ Success ({response.status_code}) | Took {duration:.2f} seconds")
        return True
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        print(f"  - ❌ FAILED | Took {duration:.2f} seconds | Error: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"     Response Body: {response.text}")
        return False

def get_paper_from_kb(paper_id: str) -> dict | None:
    """Retrieves a paper from the Membase Knowledge Base by its paper_id metadata."""
    search_url = f"{API_BASE_URL}/api/v1/knowledge/documents/search"
    metadata_filter = json.dumps({"paper_id": paper_id})
    params = {"query": paper_id, "metadata_filter": metadata_filter, "top_k": 1}
    try:
        print(f"--- MEMBASE CLIENT: Searching for paper '{paper_id}' in KB... ---")
        response = requests.get(search_url, headers=_get_headers(), params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return None
        document = results[0].get("document", {})
        return {
            "id": document.get("metadata", {}).get("paper_id", paper_id),
            "message": document.get("content", "Content not available.")
        }
    except requests.exceptions.RequestException as e:
        print(f"--- MEMBASE CLIENT: Error searching for paper: {e} ---")
        return None
