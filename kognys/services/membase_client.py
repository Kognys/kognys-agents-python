# kognys/services/membase_client.py
import os
import requests
import json
import time
import asyncio
import aiohttp
from typing import List, Dict, Any
from time import sleep
from kognys.utils.address import normalize_address

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
        response = requests.get(check_url, timeout=30)
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
        response = requests.post(register_url, json=payload, timeout=30)
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
            response = requests.post(task_url, json=payload, timeout=30)
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
        response = requests.get(check_url, timeout=30)
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
            response = requests.post(task_url, json=payload, timeout=30)
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

def finish_task(task_id: str, agent_id: str, max_retries: int = 3) -> dict:
    """Marks a task as finished on the blockchain and returns the transaction hash."""
    if not API_BASE_URL:
        print(f"  - ❌ FAILED: MEMBASE_API_URL is not set in environment")
        return {"success": False, "transaction_hash": None}
    if not agent_id:
        print(f"  - ❌ FAILED: MEMBASE_ID is not set in environment")
        return {"success": False, "transaction_hash": None}
        
    task_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}/finish"
    payload = {"agent_id": agent_id}
    
    print(f"\n--- ✅ Finishing On-Chain Task ---")
    print(f"  - Endpoint: POST {task_url}")
    print(f"  - Agent ID: {agent_id}")
    print(f"  - Task ID: {task_id}")

    for attempt in range(max_retries):
        try:
            response = requests.post(task_url, json=payload, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            tx_hash = response_data.get('transaction_hash', 'N/A')
            print(f"  - ✅ Success: Task '{task_id}' finished by agent '{agent_id}'.")
            print(f"  - 🔗 Transaction Hash: {tx_hash}")
            return {"success": True, "transaction_hash": tx_hash}
        except requests.exceptions.RequestException as e:
            is_nonce_error = (
                hasattr(e, 'response') and e.response is not None and 
                e.response.status_code == 500 and 
                'nonce too low' in str(e.response.text)
            )
            
            if is_nonce_error and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"  - ⚠️ Nonce error detected. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                sleep(wait_time)
                continue
            
            error_code, error_msg = _parse_error_response(e)
            print(f"  - ❌ FAILED ({error_code}): Could not finish task '{task_id}'")
            print(f"     Error: {error_msg}")
            return {"success": False, "transaction_hash": None}
    
    return {"success": False, "transaction_hash": None}

def store_final_answer_in_kb(paper_id: str, paper_content: str, original_question: str, user_id: str = None) -> dict:
    """Stores the final answer in the Membase Knowledge Base to make it searchable."""
    if not API_BASE_URL:
        return {"success": False, "error": "MEMBASE_API_URL not set"}
        
    kb_url = f"{API_BASE_URL}/api/v1/knowledge/documents"
    metadata = {"paper_id": paper_id, "original_question": original_question}
    if user_id:
        metadata["user_id"] = normalize_address(user_id) or user_id
    payload = {"documents": {"content": paper_content, "metadata": metadata}}
    
    print(f"\n--- 📤 Storing Final Answer in Membase KB ---")
    try:
        response = requests.post(kb_url, json=payload, timeout=30)
        response.raise_for_status()
        print(f"  - ✅ Success ({response.status_code})")
        return {"success": True, "ids": response.json().get("ids")}
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED | Error: {e}")
        return {"success": False, "error": str(e)}

def store_transcript_in_memory(paper_id: str, transcript: List[Dict[str, Any]]) -> dict:
    """Stores the debate transcript as a conversation in Membase."""
    if not API_BASE_URL:
        return {"success": False, "error": "MEMBASE_API_URL not set"}
        
    convo_url = f"{API_BASE_URL}/api/v1/memory/conversations/{paper_id}/messages"
    messages = [{"name": e.get("agent", "system"), "content": f"{e.get('action', '')}: {e.get('output', '')}", "role": "assistant"} for e in transcript]
    
    print(f"\n--- 📤 Storing Transcript in Membase Conversations ---")
    try:
        # First, ensure the conversation exists
        requests.post(f"{API_BASE_URL}/api/v1/memory/conversations", json={"conversation_id": paper_id}, timeout=30)
        # Then, add the messages
        response = requests.post(convo_url, json={"messages": messages}, timeout=30)
        response.raise_for_status()
        print(f"  - ✅ Success ({response.status_code})")
        return {"success": True}
    except requests.exceptions.RequestException as e:
        print(f"  - ❌ FAILED | Error: {e}")
        return {"success": False, "error": str(e)}

def get_paper_from_kb(paper_id: str) -> dict | None:
    """Retrieves a paper from the Membase Knowledge Base by its paper_id metadata."""
    search_url = f"{API_BASE_URL}/api/v1/knowledge/documents/search"
    metadata_filter = json.dumps({"paper_id": paper_id})
    params = {"query": paper_id, "metadata_filter": metadata_filter, "top_k": 1}
    try:
        print(f"--- MEMBASE CLIENT: Searching for paper '{paper_id}' in KB... ---")
        response = requests.get(search_url, params=params, timeout=30)
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
    # Normalize user_id to lowercase if it's an Ethereum address
    normalized_user_id = normalize_address(user_id) or user_id
    
    search_url = f"{API_BASE_URL}/api/v1/knowledge/documents/search"
    metadata_filter = json.dumps({"user_id": normalized_user_id})
    # Use empty query to get all papers for the user
    params = {"query": "", "metadata_filter": metadata_filter, "top_k": top_k}
    try:
        print(f"--- MEMBASE CLIENT: Searching for papers by user '{normalized_user_id}' in KB... ---")
        response = requests.get(search_url, params=params, timeout=30)
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
                "user_id": metadata.get("user_id", normalized_user_id)
            })
        print(f"--- MEMBASE CLIENT: Found {len(papers)} papers for user '{normalized_user_id}' ---")
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
        response = requests.post(create_url, json=payload, timeout=30)
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
        response = requests.post(query_url, json=payload, timeout=30)
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
        response = requests.post(message_url, json=payload, timeout=30)
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
            response = requests.post(auth_url, json=payload, timeout=30)
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
        response = requests.get(check_url, timeout=30)
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
        response = requests.post(route_url, json=payload, timeout=30)
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

# ========================================
# ASYNC BLOCKCHAIN OPERATIONS FOR PERFORMANCE
# ========================================

async def async_create_task(task_id: str, price: int = 1000, max_retries: int = 3) -> bool:
    """Async version of create_task for non-blocking blockchain operations."""
    if not API_BASE_URL:
        print(f"  - ❌ FAILED: MEMBASE_API_URL is not set in environment")
        return False
        
    task_url = f"{API_BASE_URL}/api/v1/tasks/create"
    payload = {"task_id": task_id, "price": price}
    headers = _get_headers()
    
    print(f"\n--- ⛓️ Creating On-Chain Task (Async) ---")
    print(f"  - Endpoint: POST {task_url}")
    print(f"  - Task ID: {task_id}")
    print(f"  - Price: {price}")

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(task_url, json=payload, headers=headers, timeout=30) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    tx_hash = response_data.get('transaction_hash', 'N/A')
                    print(f"  - ✅ Success: Task '{task_id}' created.")
                    print(f"  - 🔗 Transaction Hash: {tx_hash}")
                    return True
        except aiohttp.ClientError as e:
            # Handle nonce errors with retry logic
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"  - ⚠️ Request error. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
                continue
            
            print(f"  - ❌ FAILED: Could not create task '{task_id}'")
            print(f"     Error: {str(e)}")
            return False
    
    return False

async def async_check_task_exists(task_id: str) -> bool:
    """Async version of check_task_exists."""
    if not API_BASE_URL:
        return False
        
    check_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}"
    headers = _get_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(check_url, headers=headers, timeout=10) as response:
                return response.status == 200
    except:
        return False

async def async_join_task(task_id: str, agent_id: str, max_retries: int = 3) -> bool:
    """Async version of join_task for non-blocking blockchain operations."""
    if not API_BASE_URL:
        print(f"  - ❌ FAILED: MEMBASE_API_URL is not set in environment")
        return False
    if not agent_id:
        print(f"  - ❌ FAILED: MEMBASE_ID is not set in environment")
        return False
        
    task_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}/join"
    payload = {"agent_id": agent_id}
    headers = _get_headers()
    
    print(f"\n--- 🙋 Joining On-Chain Task (Async) ---")
    print(f"  - Endpoint: POST {task_url}")
    print(f"  - Agent ID: {agent_id}")
    print(f"  - Task ID: {task_id}")
    
    # Wait for task to exist on blockchain (up to 10 seconds)
    print(f"  - ⏳ Waiting for task to be confirmed on blockchain...")
    for i in range(10):
        if await async_check_task_exists(task_id):
            print(f"  - ✅ Task confirmed to exist (after {i+1}s)")
            break
        await asyncio.sleep(1)
    else:
        print(f"  - ❌ FAILED: Task '{task_id}' not found after 10 seconds")
        return False
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(task_url, json=payload, headers=headers, timeout=30) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    tx_hash = response_data.get('transaction_hash', 'N/A')
                    print(f"  - ✅ Success: Agent '{agent_id}' joined task '{task_id}'.")
                    print(f"  - 🔗 Transaction Hash: {tx_hash}")
                    return True
        except aiohttp.ClientError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"  - ⏳ Retry {attempt + 1}/{max_retries}: Request error, waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            
            print(f"  - ❌ FAILED: Agent '{agent_id}' could not join task '{task_id}'")
            print(f"     Error: {str(e)}")
            return False
    
    return False

async def async_finish_task(task_id: str, agent_id: str, max_retries: int = 3) -> bool:
    """Async version of finish_task for non-blocking blockchain operations."""
    if not API_BASE_URL:
        print(f"  - ❌ FAILED: MEMBASE_API_URL is not set in environment")
        return False
    if not agent_id:
        print(f"  - ❌ FAILED: MEMBASE_ID is not set in environment")
        return False
        
    task_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}/finish"
    payload = {"agent_id": agent_id}
    headers = _get_headers()
    
    print(f"\n--- ✅ Finishing On-Chain Task (Async) ---")
    print(f"  - Endpoint: POST {task_url}")
    print(f"  - Agent ID: {agent_id}")
    print(f"  - Task ID: {task_id}")
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(task_url, json=payload, headers=headers, timeout=30) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    tx_hash = response_data.get('transaction_hash', 'N/A')
                    print(f"  - ✅ Success: Task '{task_id}' finished by agent '{agent_id}'.")
                    print(f"  - 🔗 Transaction Hash: {tx_hash}")
                    return True
        except aiohttp.ClientError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Linear backoff: 2s, 4s, 6s
                print(f"  - ⚠️ Request error. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
                continue
            
            print(f"  - ❌ FAILED: Could not finish task '{task_id}'")
            print(f"     Error: {str(e)}")
            return False
    
    return False

async def async_blockchain_operations_background(task_id: str, agent_id: str):
    """Run all blockchain operations in the background without blocking research."""
    print(f"🚀 Starting background blockchain operations for task: {task_id}")
    
    # Create task
    create_success = await async_create_task(task_id)
    if not create_success:
        print(f"❌ Background blockchain: Failed to create task {task_id}")
        return
    
    # Join task
    join_success = await async_join_task(task_id, agent_id)
    if not join_success:
        print(f"❌ Background blockchain: Failed to join task {task_id}")
        return
    
    print(f"✅ Background blockchain: Task {task_id} created and joined successfully")

async def async_finish_blockchain_operations(task_id: str, agent_id: str, emit_callback=None):
    """Finish blockchain operations and emit transaction_confirmed event to frontend."""
    print(f"🏁 Finishing blockchain operations for task: {task_id}")
    
    # Use the dedicated async_finish_task function
    finish_success = await async_finish_task(task_id, agent_id)
    
    if finish_success:
        print(f"✅ Background blockchain: Task {task_id} finished successfully")
        
        # Get the actual transaction hash by querying the task
        try:
            if API_BASE_URL:
                task_url = f"{API_BASE_URL}/api/v1/tasks/{task_id}"
                headers = _get_headers()
                async with aiohttp.ClientSession() as session:
                    async with session.get(task_url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            task_data = await response.json()
                            actual_tx_hash = task_data.get('finish_transaction_hash') or task_data.get('transaction_hash', 'N/A')
                            
                            if actual_tx_hash and actual_tx_hash != 'N/A':
                                transaction_event = {
                                    "event_type": "transaction_confirmed",
                                    "data": {
                                        "task_id": task_id,
                                        "transaction_hash": actual_tx_hash,
                                        "operation": "task_finish",
                                        "status": "Blockchain transaction confirmed"
                                    },
                                    "timestamp": time.time(),
                                    "agent": "system"
                                }
                                
                                # Send to global transaction queue using shared system
                                try:
                                    from kognys.services.transaction_events import emit_transaction_confirmed
                                    emit_transaction_confirmed(task_id, actual_tx_hash, "task_finish")
                                except Exception as queue_e:
                                    print(f"⚠️ Could not emit transaction event: {queue_e}")
                                
                                # Also call callback if provided
                                if emit_callback:
                                    try:
                                        emit_callback(transaction_event)
                                        print(f"📡 Called transaction_confirmed callback with hash: {actual_tx_hash}")
                                    except Exception as cb_e:
                                        print(f"⚠️ Transaction callback error: {cb_e}")
        except Exception as get_hash_e:
            print(f"⚠️ Could not retrieve transaction hash: {get_hash_e}")
    else:
        print(f"❌ Background blockchain: Failed to finish task {task_id}")
        
        # Emit failure event
        transaction_failed_event = {
            "event_type": "transaction_failed",
            "data": {
                "task_id": task_id,
                "error": "Task finish operation failed",
                "operation": "task_finish",
                "status": "Blockchain transaction failed"
            },
            "timestamp": time.time(),
            "agent": "system"
        }
        
        try:
            from kognys.services.transaction_events import emit_transaction_failed
            emit_transaction_failed(task_id, "Task finish operation failed", "task_finish")
        except Exception as queue_e:
            print(f"⚠️ Could not emit transaction failure event: {queue_e}")
        
        if emit_callback:
            try:
                emit_callback(transaction_failed_event)
                print(f"📡 Called transaction_failed callback")
            except Exception as cb_e:
                print(f"⚠️ Transaction failure callback error: {cb_e}")
    
    return finish_success
