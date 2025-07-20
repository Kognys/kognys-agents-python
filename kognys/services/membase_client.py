# kognys/services/membase_client.py
import os
import requests
import json
import time
from typing import List, Dict, Any
from time import sleep

API_BASE_URL = os.getenv("MEMBASE_API_URL")
API_KEY = os.getenv("MEMBASE_API_KEY")

def _get_headers() -> dict:
    if not API_KEY:
        raise ValueError("MEMBASE_API_KEY is not set in the environment.")
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def _parse_error_response(e: requests.exceptions.RequestException) -> tuple[str, str]:
    """Parse error response to extract actual error code and message."""
    if hasattr(e, 'response') and e.response is not None:
        try:
            error_data = json.loads(e.response.text)
            detail = error_data.get('detail', '')
            
            # Extract actual error code from detail if in format "CODE: message"
            if ': ' in detail and detail.split(': ')[0].isdigit():
                actual_code = detail.split(': ')[0]
                error_msg = detail.split(': ', 1)[1] if len(detail.split(': ', 1)) > 1 else detail
                return actual_code, error_msg
            else:
                return str(e.response.status_code), detail
                
        except (json.JSONDecodeError, KeyError):
            return str(e.response.status_code), e.response.text
    
    return "Unknown", str(e)

def register_agent_if_not_exists(agent_id: str) -> bool:
    """Registers an agent on the blockchain via the Membase API."""
    if not API_BASE_URL:
        print(f"❌ FAILED: MEMBASE_API_URL is not set in environment")
        return False
    if not agent_id:
        print(f"❌ FAILED: Agent ID is not provided")
        return False
        
    print(f"\n--- 🤖 Registering Agent on Blockchain ---")
    print(f"  - Agent ID: {agent_id}")
    
    try:
        check_url = f"{API_BASE_URL}/api/v1/agents/{agent_id}"
        response = requests.get(check_url)
        if response.status_code == 200:
            print(f"  - ✅ Agent '{agent_id}' is already registered.")
            return True
    except requests.exceptions.RequestException:
        pass

    register_url = f"{API_BASE_URL}/api/v1/agents/register"
    payload = {"agent_id": agent_id}
    
    print(f"  - Endpoint: POST {register_url}")
    print(f"  - Payload: {payload}")
    
    try:
        response = requests.post(register_url, json=payload)
        response.raise_for_status()
        response_data = response.json()
        tx_hash = response_data.get('transaction_hash', 'N/A')
        print(f"  - ✅ Successfully registered agent '{agent_id}' on-chain.")
        print(f"  - 🔗 Transaction Hash: {tx_hash}")
        return True
    except requests.exceptions.RequestException as e:
        error_code, error_msg = _parse_error_response(e)
        print(f"  - ❌ FAILED ({error_code}): Failed to register agent '{agent_id}'")
        print(f"     Error: {error_msg}")
        return False

def create_task(task_id: str, price: int = 1000, max_retries: int = 3) -> bool:
    """Creates a new task on the blockchain via the Membase API with retry logic for nonce errors."""
    if not API_BASE_URL:
        print(f"  - ❌ FAILED: MEMBASE_API_URL is not set in environment")
        return False
        
    task_url = f"{API_BASE_URL}/api/v1/tasks/create"
    payload = {"task_id": task_id, "price": price}
    
    print(f"\n--- ⛓️ Creating On-Chain Task ---")
    print(f"  - Endpoint: POST {task_url}")
    print(f"  - Task ID: {task_id}")
    print(f"  - Price: {price}")

    for attempt in range(max_retries):
        try:
            response = requests.post(task_url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            tx_hash = response_data.get('transaction_hash', 'N/A')
            print(f"  - ✅ Success: Task '{task_id}' created.")
            print(f"  - 🔗 Transaction Hash: {tx_hash}")
            return True
        except requests.exceptions.RequestException as e:
            is_nonce_error = (
                hasattr(e, 'response') and e.response is not None and 
                e.response.status_code == 500 and 
                'nonce too low' in str(e.response.text)
            )
            
            if is_nonce_error and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"  - ⚠️ Nonce error detected. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                sleep(wait_time)
                continue
            
            error_code, error_msg = _parse_error_response(e)
            print(f"  - ❌ FAILED ({error_code}): Could not create task '{task_id}'")
            print(f"     Error: {error_msg}")
            return False
    
    return False

def check_task_exists(task_id: str) -> bool:
    """Checks if a task exists on the blockchain."""
    if not API_BASE_URL:
        return False
    
    check_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}"
    try:
        response = requests.get(check_url)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def join_task(task_id: str, agent_id: str, max_retries: int = 3) -> bool:
    """Joins an existing task on the blockchain with retry logic for nonce errors and race conditions."""
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
    
    # Wait for task to exist on blockchain (up to 10 seconds)
    print(f"  - ⏳ Waiting for task to be confirmed on blockchain...")
    for i in range(10):
        if check_task_exists(task_id):
            print(f"  - ✅ Task confirmed to exist (after {i+1}s)")
            break
        sleep(1)
    else:
        print(f"  - ❌ FAILED: Task '{task_id}' not found after 10 seconds")
        return False
    
    for attempt in range(max_retries):
        try:
            response = requests.post(task_url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            tx_hash = response_data.get('transaction_hash', 'N/A')
            print(f"  - ✅ Success: Agent '{agent_id}' joined task '{task_id}'.")
            print(f"  - 🔗 Transaction Hash: {tx_hash}")
            return True
        except requests.exceptions.RequestException as e:
            # Check for nonce errors (partner's fix)
            is_nonce_error = (
                hasattr(e, 'response') and e.response is not None and 
                e.response.status_code == 500 and 
                'nonce too low' in str(e.response.text)
            )
            
            # Check for race condition errors (our fix)
            is_race_condition_error = (
                hasattr(e, 'response') and 
                e.response is not None and 
                (e.response.status_code == 404 or e.response.status_code == 500) and
                "does not exist" in e.response.text
            )
            
            # Retry for both types of errors
            if (is_nonce_error or is_race_condition_error) and attempt < max_retries - 1:
                if is_nonce_error:
                    wait_time = (attempt + 1) * 2  # Linear backoff for nonce: 2s, 4s, 6s
                    print(f"  - ⚠️ Nonce error detected. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                else:
                    wait_time = 2 ** attempt  # Exponential backoff for race condition: 1s, 2s, 4s
                    print(f"  - ⏳ Retry {attempt + 1}/{max_retries}: Task not found, waiting {wait_time}s for sync...")
                
                time.sleep(wait_time)
                continue
            
            # Final attempt or non-retryable error
            error_code, error_msg = _parse_error_response(e)
            print(f"  - ❌ FAILED ({error_code}): Agent '{agent_id}' could not join task '{task_id}'")
            print(f"     Error: {error_msg}")
            return False
    
    return False

def finish_task(task_id: str, agent_id: str, max_retries: int = 3) -> bool:
    """Marks a task as finished on the blockchain with retry logic for nonce errors."""
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

    for attempt in range(max_retries):
        try:
            response = requests.post(task_url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            tx_hash = response_data.get('transaction_hash', 'N/A')
            print(f"  - ✅ Success: Task '{task_id}' finished by agent '{agent_id}'.")
            print(f"  - 🔗 Transaction Hash: {tx_hash}")
            return True
        except requests.exceptions.RequestException as e:
            is_nonce_error = (
                hasattr(e, 'response') and e.response is not None and 
                e.response.status_code == 500 and 
                'nonce too low' in str(e.response.text)
            )
            
            if is_nonce_error and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"  - ⚠️ Nonce error detected. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                sleep(wait_time)
                continue
            
            error_code, error_msg = _parse_error_response(e)
            print(f"  - ❌ FAILED ({error_code}): Could not finish task '{task_id}'")
            print(f"     Error: {error_msg}")
            return False
    
    return False

def store_final_answer_in_kb(paper_id: str, paper_content: str, original_question: str, user_id: str = None) -> bool:
    """Stores the final answer in the Membase Knowledge Base to make it searchable."""
    kb_url = f"{API_BASE_URL}/api/v1/knowledge/documents"
    metadata = {"paper_id": paper_id, "original_question": original_question}
    if user_id:
        metadata["user_id"] = user_id
    document = {"content": paper_content, "metadata": metadata}
    payload = {"documents": document, "strict": True}
    
    start_time = time.time()
    payload_size = len(json.dumps(payload).encode('utf-8'))
    
    print(f"\n--- 📤 Storing Final Answer in Membase KB ---")
    print(f"  - Endpoint: POST {kb_url}")
    print(f"  - Data Size: {payload_size / 1024:.2f} KB")
    print(f"  - User ID in metadata: {metadata.get('user_id', 'None')}")
    print(f"  - Payload structure: documents={'content': '...', 'metadata': {metadata}}")

    try:
        response = requests.post(kb_url, json=payload)
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
        requests.post(f"{API_BASE_URL}/api/v1/memory/conversations", json={"conversation_id": paper_id})
        # Then, add the messages
        response = requests.post(convo_url, json=payload)
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
        response = requests.get(search_url, params=params)
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
        response = requests.get(search_url, params=params)
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
        response = requests.post(create_url, json=payload)
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
        response = requests.post(query_url, json=payload)
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
        response = requests.post(message_url, json=payload)
        response.raise_for_status()
        print(f"  - ✅ Success: Message sent.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED: Could not send message. Error: {e}")
        return {"error": str(e)}

def buy_agent_auth(buyer_id: str, seller_id: str, max_retries: int = 3) -> bool:
    """Authorizes one agent to access another agent's data with retry logic."""
    if not API_BASE_URL:
        print(f"  - ❌ FAILED: MEMBASE_API_URL is not set in environment")
        return False
    if not buyer_id or not seller_id:
        print(f"  - ❌ FAILED: Both buyer_id and seller_id must be provided")
        return False
    if buyer_id == seller_id:
        print(f"  - ⚠️ SKIPPED: Cannot authorize agent to itself ({buyer_id})")
        return True  # Not a failure, just unnecessary
        
    auth_url = f"{API_BASE_URL}/api/v1/agents/buy-auth"
    payload = {
        "buyer_id": buyer_id,
        "seller_id": seller_id
    }
    
    print(f"\n--- 🔐 Buying Agent Authorization ---")
    print(f"  - Buyer: {buyer_id} → Seller: {seller_id}")
    print(f"  - Endpoint: POST {auth_url}")
    
    for attempt in range(max_retries):
        try:
            response = requests.post(auth_url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            tx_hash = response_data.get('transaction_hash', 'N/A')
            print(f"  - ✅ Success: Authorization granted.")
            print(f"  - 🔗 Transaction Hash: {tx_hash}")
            return True
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                response_text = e.response.text
                
                # Parse the actual error from response body
                try:
                    error_data = json.loads(response_text)
                    detail = error_data.get('detail', '')
                    
                    # Check if it's an "already authorized" error
                    if '409' in detail and 'already has authorization' in detail:
                        print(f"  - ✅ Already authorized: {buyer_id} → {seller_id}")
                        return True
                    
                    # Check for nonce errors
                    is_nonce_error = (
                        e.response.status_code == 500 and 
                        ('nonce too low' in detail.lower() or 'nonce' in detail.lower())
                    )
                    
                    if is_nonce_error and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3  # Longer wait for auth: 3s, 6s, 9s
                        print(f"  - ⚠️ Nonce/blockchain error detected. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        sleep(wait_time)
                        continue
                    
                    # Use the helper to parse error
                    error_code, error_msg = _parse_error_response(e)
                    print(f"  - ❌ FAILED ({error_code}): {error_msg}")
                        
                except (json.JSONDecodeError, KeyError):
                    # Fallback to original error display
                    print(f"  - ❌ FAILED ({e.response.status_code}): {response_text}")
            else:
                print(f"  - ❌ FAILED: Could not buy authorization. Error: {e}")
            
            return False
    
    return False

def check_agent_auth(agent_id: str, target_id: str) -> bool:
    """Checks if an agent has authorization to access another agent's data."""
    check_url = f"{API_BASE_URL}/api/v1/agents/{agent_id}/has-auth/{target_id}"
    
    try:
        response = requests.get(check_url)
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
        response = requests.post(route_url, json=payload)
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
