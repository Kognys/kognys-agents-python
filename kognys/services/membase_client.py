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
    if not API_BASE_URL:
        print(f"  - ❌ FAILED: MEMBASE_API_URL is not set in environment")
        return False
        
    task_url = f"{API_BASE_URL}/api/v1/tasks/create"
    payload = {"task_id": task_id, "price": price}
    
    print(f"\n--- ⛓️ Creating On-Chain Task ---")
    print(f"  - Endpoint: POST {task_url}")
    print(f"  - Task ID: {task_id}")
    print(f"  - Price: {price}")

    try:
        response = requests.post(task_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        response_data = response.json()
        tx_hash = response_data.get('transaction_hash', 'N/A')
        print(f"  - ✅ Success: Task '{task_id}' created.")
        print(f"  - 🔗 Transaction Hash: {tx_hash}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not create task '{task_id}'. Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  - Response Status: {e.response.status_code}")
            print(f"  - Response Body: {e.response.text}")
        return False

def join_task(task_id: str, agent_id: str, max_retries: int = 3) -> bool:
    """Joins an existing task on the blockchain with retry logic for race conditions."""
    if not API_BASE_URL:
        print(f"  - ❌ FAILED: MEMBASE_API_URL is not set in environment")
        return False
    if not agent_id:
        print(f"  - ❌ FAILED: MEMBASE_ID is not set in environment")
        return False
        
    task_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}/join"
    payload = {"agent_id": agent_id}
    
    print(f"\n--- 🙋 Joining On-Chain Task ---")
    print(f"  - Endpoint: POST {task_url}")
    print(f"  - Agent ID: {agent_id}")
    print(f"  - Task ID: {task_id}")
    
    for attempt in range(max_retries):
        try:
            response = requests.post(task_url, headers=_get_headers(), json=payload)
            response.raise_for_status()
            response_data = response.json()
            tx_hash = response_data.get('transaction_hash', 'N/A')
            print(f"  - ✅ Success: Agent '{agent_id}' joined task '{task_id}'.")
            print(f"  - 🔗 Transaction Hash: {tx_hash}")
            return True
        except requests.exceptions.RequestException as e:
            # Check if this is a 404 "task does not exist" error that might be resolved with retry
            is_retry_worthy = (
                hasattr(e, 'response') and 
                e.response is not None and 
                (e.response.status_code == 404 or e.response.status_code == 500) and
                "does not exist" in e.response.text
            )
            
            if is_retry_worthy and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"  - ⏳ Retry {attempt + 1}/{max_retries}: Task not found, waiting {wait_time}s for sync...")
                time.sleep(wait_time)
                continue
            else:
                # Final attempt or non-retryable error
                print(f"  - ❌ FAILED: Agent '{agent_id}' could not join task '{task_id}'. Error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"  - Response Status: {e.response.status_code}")
                    print(f"  - Response Body: {e.response.text}")
                return False
    
    return False

def finish_task(task_id: str, agent_id: str) -> bool:
    """Marks a task as finished on the blockchain."""
    if not API_BASE_URL:
        print(f"  - ❌ FAILED: MEMBASE_API_URL is not set in environment")
        return False
    if not agent_id:
        print(f"  - ❌ FAILED: MEMBASE_ID is not set in environment")
        return False
        
    task_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}/finish"
    payload = {"agent_id": agent_id}
    
    print(f"\n--- ✅ Finishing On-Chain Task ---")
    print(f"  - Endpoint: POST {task_url}")
    print(f"  - Agent ID: {agent_id}")
    print(f"  - Task ID: {task_id}")

    try:
        response = requests.post(task_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        response_data = response.json()
        tx_hash = response_data.get('transaction_hash', 'N/A')
        print(f"  - ✅ Success: Task '{task_id}' finished by agent '{agent_id}'.")
        print(f"  - 🔗 Transaction Hash: {tx_hash}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not finish task '{task_id}'. Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  - Response Status: {e.response.status_code}")
            print(f"  - Response Body: {e.response.text}")
        return False

def store_final_answer_in_kb(paper_id: str, paper_content: str, original_question: str, user_id: str = None) -> bool:
    """Stores the final answer in the Membase Knowledge Base to make it searchable."""
    kb_url = f"{API_BASE_URL}/api/v1/knowledge/documents"
    metadata = {"paper_id": paper_id, "original_question": original_question}
    if user_id:
        metadata["user_id"] = user_id
    document = {"content": paper_content, "metadata": metadata}
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

def get_papers_by_user_id(user_id: str, top_k: int = 10) -> list:
    """Retrieves all papers from the Membase Knowledge Base for a specific user."""
    search_url = f"{API_BASE_URL}/api/v1/knowledge/documents/search"
    metadata_filter = json.dumps({"user_id": user_id})
    # Use empty query to get all papers for the user
    params = {"query": "", "metadata_filter": metadata_filter, "top_k": top_k}
    try:
        print(f"--- MEMBASE CLIENT: Searching for papers by user '{user_id}' in KB... ---")
        response = requests.get(search_url, headers=_get_headers(), params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        papers = []
        for result in results:
            document = result.get("document", {})
            metadata = document.get("metadata", {})
            papers.append({
                "paper_id": metadata.get("paper_id", ""),
                "original_question": metadata.get("original_question", ""),
                "content": document.get("content", ""),
                "user_id": metadata.get("user_id", user_id)
            })
        print(f"--- MEMBASE CLIENT: Found {len(papers)} papers for user '{user_id}' ---")
        return papers
    except requests.exceptions.RequestException as e:
        print(f"--- MEMBASE CLIENT: Error searching for papers by user: {e} ---")
        return []

def create_aip_agent(agent_id: str, description: str = "", conversation_id: str = None) -> dict:
    """Creates an AIP agent with LLM capabilities."""
    create_url = f"{API_BASE_URL}/api/v1/agents/create"
    payload = {
        "agent_id": agent_id,
        "description": description,
        "default_conversation_id": conversation_id or f"{agent_id}-conv"
    }
    
    print(f"\n--- 🤖 Creating AIP Agent ---")
    print(f"  - Agent ID: {agent_id}")
    
    try:
        response = requests.post(create_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print(f"  - ✅ Success: AIP Agent '{agent_id}' created.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not create AIP agent '{agent_id}'. Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"     Response: {e.response.text}")
        return {}

def query_aip_agent(agent_id: str, query: str, conversation_id: str = None, 
                   use_history: bool = True, recent_n_messages: int = 10) -> dict:
    """Queries an AIP agent for intelligent responses."""
    query_url = f"{API_BASE_URL}/api/v1/agents/{agent_id}/query"
    payload = {
        "query": query,
        "conversation_id": conversation_id or f"{agent_id}-conv",
        "use_history": use_history,
        "use_tool_call": True,
        "recent_n_messages": recent_n_messages
    }
    
    print(f"\n--- 💬 Querying AIP Agent ---")
    print(f"  - Agent: {agent_id}")
    print(f"  - Query: {query[:100]}...")
    
    try:
        response = requests.post(query_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"  - ✅ Success: Received response from agent.")
        return result
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not query agent '{agent_id}'. Error: {e}")
        return {"response": "", "error": str(e)}

def send_agent_message(from_agent_id: str, to_agent_id: str, action: str, message: str) -> dict:
    """Sends a message from one agent to another."""
    message_url = f"{API_BASE_URL}/api/v1/agents/{from_agent_id}/message"
    payload = {
        "target_agent_id": to_agent_id,
        "action": action,
        "message": message
    }
    
    print(f"\n--- 📨 Sending Inter-Agent Message ---")
    print(f"  - From: {from_agent_id} → To: {to_agent_id}")
    print(f"  - Action: {action}")
    
    try:
        response = requests.post(message_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print(f"  - ✅ Success: Message sent.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not send message. Error: {e}")
        return {"error": str(e)}

def buy_agent_auth(buyer_id: str, seller_id: str) -> bool:
    """Authorizes one agent to access another agent's data."""
    auth_url = f"{API_BASE_URL}/api/v1/agents/buy-auth"
    payload = {
        "buyer_id": buyer_id,
        "seller_id": seller_id
    }
    
    print(f"\n--- 🔐 Buying Agent Authorization ---")
    print(f"  - Buyer: {buyer_id} → Seller: {seller_id}")
    
    try:
        response = requests.post(auth_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        print(f"  - ✅ Success: Authorization granted.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not buy authorization. Error: {e}")
        return False

def check_agent_auth(agent_id: str, target_id: str) -> bool:
    """Checks if an agent has authorization to access another agent's data."""
    check_url = f"{API_BASE_URL}/api/v1/agents/{agent_id}/has-auth/{target_id}"
    
    try:
        response = requests.get(check_url, headers=_get_headers())
        response.raise_for_status()
        result = response.json()
        return result.get("has_auth", False)
    except requests.exceptions.RequestException:
        return False

def route_request(request_text: str, top_k: int = 3) -> list:
    """Uses intelligent routing to find the best handler for a request."""
    route_url = f"{API_BASE_URL}/api/v1/route"
    payload = {
        "request": request_text,
        "top_k": top_k
    }
    
    print(f"\n--- 🚦 Routing Request ---")
    print(f"  - Request: {request_text[:100]}...")
    
    try:
        response = requests.post(route_url, headers=_get_headers(), json=payload)
        response.raise_for_status()
        result = response.json()
        routes = result.get("routes", [])
        print(f"  - ✅ Found {len(routes)} potential routes.")
        for route in routes:
            print(f"     → {route['category_name']} (score: {route['score']:.2f})")
        return routes
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not route request. Error: {e}")
        return []
