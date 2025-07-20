# Kognys: Membase API Consumption Guide

This document details how the Kognys research agent consumes the Membase API to enable on-chain identity, task management, decentralized memory storage, and AIP agent capabilities. All interactions are managed through our `kognys/services/membase_client.py`.

## API Configuration

- **Base URL**: Set via `MEMBASE_API_URL` environment variable (e.g., `https://kognys-membaseaip-api-production.up.railway.app`)
- **Authentication**: All requests include `X-API-Key` header with the value from `MEMBASE_API_KEY` environment variable

## 1. Agent On-Chain Identity

Before performing any action, the Kognys agent ensures it has a registered on-chain identity. This happens at startup.

### Check Agent Registration
- **API Endpoint Used**: `GET /api/v1/agents/{agent_id}`
- **Function**: `register_agent_if_not_exists()` (first checks if agent exists)
- **Purpose**: Verify if an agent is already registered on the blockchain

### Register Agent
- **API Endpoint Used**: `POST /api/v1/agents/register`
- **Function**: `register_agent_if_not_exists()`
- **Trigger**: Called once when FastAPI server starts (`api_main.py`) or when a local test script is run
- **Example Payload**:
  ```json
  {
    "agent_id": "kognys_test"
  }
  ```

---

## 2. On-Chain Task Management

Each research request from a user is treated as a distinct, verifiable on-chain task.

### Task Creation
- **API Endpoint Used**: `POST /api/v1/tasks/create`
- **Function**: `create_task(task_id, price)`
- **Trigger**: Called by `InputValidatorAgent` at the beginning of every research job
- **Example Payload**:
  ```json
  {
    "task_id": "1d13378a-2597-42c4-a2bf-4cf56e968c2b",
    "price": 1000
  }
  ```

### Task Joining
- **API Endpoint Used**: `POST /api/v1/tasks/{task_id}/join`
- **Function**: `join_task(task_id, agent_id)`
- **Trigger**: Called immediately after task creation
- **Example Payload**:
  ```json
  {
    "agent_id": "kognys_test"
  }
  ```

### Task Completion
- **API Endpoint Used**: `POST /api/v1/tasks/{task_id}/finish`
- **Function**: `finish_task(task_id, agent_id)`
- **Trigger**: Called by `PublisherAgent` after successful research completion
- **Example Payload**:
  ```json
  {
    "agent_id": "kognys_test"
  }
  ```

---

## 3. Decentralized Memory Storage

### Knowledge Base Storage
- **API Endpoint Used**: `POST /api/v1/knowledge/documents`
- **Function**: `store_final_answer_in_kb(paper_id, paper_content, original_question)`
- **Trigger**: Called by `PublisherAgent` to store final research results
- **Purpose**: Make research results searchable for future queries
- **Example Payload**:
  ```json
  {
    "documents": [
      {
        "content": "Based solely on the provided documents, generative AI presents...",
        "metadata": {
          "paper_id": "1d13378a-2597-42c4-a2bf-4cf56e968c2b",
          "original_question": "What are the most promising applications of generative AI?"
        }
      }
    ]
  }
  ```

### Knowledge Base Search
- **API Endpoint Used**: `GET /api/v1/knowledge/documents/search`
- **Function**: `get_paper_from_kb(paper_id)`
- **Purpose**: Retrieve previously stored research papers
- **Query Parameters**:
  - `query`: The paper_id to search for
  - `metadata_filter`: JSON string filtering by paper_id
  - `top_k`: Number of results (usually 1)

### Conversation Storage
- **API Endpoint Used**: `POST /api/v1/memory/conversations`
- **Function**: Called within `store_transcript_in_memory()` to ensure conversation exists
- **Example Payload**:
  ```json
  {
    "conversation_id": "1d13378a-2597-42c4-a2bf-4cf56e968c2b"
  }
  ```

### Transcript Storage
- **API Endpoint Used**: `POST /api/v1/memory/conversations/{conversation_id}/messages`
- **Function**: `store_transcript_in_memory(paper_id, transcript)`
- **Purpose**: Store the agent's reasoning process and debate transcript
- **Example Payload**:
  ```json
  {
    "messages": [
      {
        "name": "InputValidator",
        "content": "Validated question & created on-chain task: Task ID: 1d13378a...",
        "role": "assistant"
      },
      {
        "name": "Retriever",
        "content": "Retrieved documents: 5 docs",
        "role": "assistant"
      }
    ]
  }
  ```

---

## 4. AIP Agent Integration (When ENABLE_AIP_AGENTS=true)

### Create AIP Agent
- **API Endpoint Used**: `POST /api/v1/agents/create`
- **Function**: `create_aip_agent(agent_id, description, conversation_id)`
- **Purpose**: Create AI-powered agents with LLM capabilities
- **Trigger**: Called during initialization if AIP is enabled
- **Example Payload**:
  ```json
  {
    "agent_id": "kognys-retriever",
    "description": "Specialized in finding and evaluating academic sources",
    "default_conversation_id": "kognys-retriever-conv"
  }
  ```

### Query AIP Agent
- **API Endpoint Used**: `POST /api/v1/agents/{agent_id}/query`
- **Function**: `query_aip_agent(agent_id, query, conversation_id, use_history, recent_n_messages)`
- **Purpose**: Get intelligent responses from AIP agents
- **Trigger**: Called by Retriever and Synthesizer agents for enhanced capabilities
- **Example Payload**:
  ```json
  {
    "query": "What search terms should I use for quantum computing research?",
    "conversation_id": "research-123",
    "use_history": true,
    "use_tool_call": true,
    "recent_n_messages": 10
  }
  ```

### Inter-Agent Messaging
- **API Endpoint Used**: `POST /api/v1/agents/{agent_id}/message`
- **Function**: `send_agent_message(from_agent_id, to_agent_id, action, message)`
- **Purpose**: Enable communication between AIP agents
- **Example Payload**:
  ```json
  {
    "target_agent_id": "kognys-challenger",
    "action": "inform",
    "message": "Synthesized revision 2 addressing criticisms"
  }
  ```

### Agent Authorization
- **API Endpoint Used**: `POST /api/v1/agents/buy-auth`
- **Function**: `buy_agent_auth(buyer_id, seller_id)`
- **Purpose**: Grant one agent permission to access another's data
- **Example Payload**:
  ```json
  {
    "buyer_id": "kognys-synthesizer",
    "seller_id": "kognys-retriever"
  }
  ```

### Check Authorization
- **API Endpoint Used**: `GET /api/v1/agents/{agent_id}/has-auth/{target_id}`
- **Function**: `check_agent_auth(agent_id, target_id)`
- **Purpose**: Verify if an agent has authorization to access another agent's data
- **Returns**: JSON with `has_auth` boolean field

### Intelligent Routing
- **API Endpoint Used**: `POST /api/v1/route`
- **Function**: `route_request(request_text, top_k)`
- **Purpose**: Find the best handler/approach for a given request
- **Example Payload**:
  ```json
  {
    "request": "I need to analyze the latest machine learning papers on transformers",
    "top_k": 3
  }
  ```
- **Example Response**:
  ```json
  {
    "routes": [
      {
        "category_name": "MLPaperAnalyzer",
        "category_type": "agent",
        "confidence": "high",
        "reasoning": "Request involves ML paper analysis",
        "score": 0.95
      }
    ]
  }
  ```

---

## Summary of All Endpoints Used

1. **Agent Management**
   - `GET /api/v1/agents/{agent_id}` - Check agent registration
   - `POST /api/v1/agents/register` - Register agent on blockchain
   - `POST /api/v1/agents/create` - Create AIP agent (optional)
   - `POST /api/v1/agents/{agent_id}/query` - Query AIP agent (optional)
   - `POST /api/v1/agents/{agent_id}/message` - Inter-agent messaging (optional)
   - `POST /api/v1/agents/buy-auth` - Grant agent authorization (optional)
   - `GET /api/v1/agents/{agent_id}/has-auth/{target_id}` - Check authorization (optional)

2. **Task Management**
   - `POST /api/v1/tasks/create` - Create on-chain task
   - `POST /api/v1/tasks/{task_id}/join` - Join task
   - `POST /api/v1/tasks/{task_id}/finish` - Complete task

3. **Knowledge Base**
   - `POST /api/v1/knowledge/documents` - Store documents
   - `GET /api/v1/knowledge/documents/search` - Search documents

4. **Conversation Memory**
   - `POST /api/v1/memory/conversations` - Create conversation
   - `POST /api/v1/memory/conversations/{conversation_id}/messages` - Add messages

5. **Routing** (optional)
   - `POST /api/v1/route` - Intelligent request routing

Note: Endpoints marked as (optional) are only used when `ENABLE_AIP_AGENTS=true` in the environment configuration.