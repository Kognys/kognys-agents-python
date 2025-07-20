# Kognys: Membase API Consumption Guide

This document details how the Kognys research agent consumes the Membase API to enable on-chain identity, task management, and decentralized memory storage. All interactions are managed through our `kognys/services/membase_client.py`.

## 1. Agent On-Chain Identity

Before performing any action, the Kognys agent ensures it has a registered on-chain identity. This happens at startup.

- **API Endpoint Used**: `POST /api/v1/agents/register`
- **Trigger**: This is called by the `register_agent_if_not_exists` function in our `membase_client.py`, which is executed once when our FastAPI server starts (`api_main.py`) or when a local test script is run (`run_live.py`).
- **Logic**:
  1.  The agent's unique ID (from the `MEMBASE_ID` environment variable) is used.
  2.  The client first calls `GET /api/v1/agents/{agent_id}` to check if the agent is already registered.
  3.  If not, it sends a `POST` request to `/api/v1/agents/register` with the agent's ID.
- **Example Payload Sent**:
  ```json
  {
    "agent_id": "kognys_test"
  }
  ```

---

## 2. On-Chain Task Management

Each research request from a user is treated as a distinct, verifiable on-chain task.

### Task Creation & Joining

- **API Endpoints Used**: `POST /api/v1/tasks/create` and `POST /api/v1/tasks/{task_id}/join`
- **Trigger**: This is handled by the `InputValidatorAgent` (`kognys/agents/input_validator.py`) at the beginning of every research job, right after the user's question is approved.
- **Logic**:
  1.  A unique, random ID is generated using `uuid.uuid4()`. This ID serves as the `task_id`.
  2.  The `create_task` function is called, sending a `POST` request to `/api/v1/tasks/create`.
  3.  Immediately after, the `join_task` function is called, sending a `POST` request to `/api/v1/tasks/{task_id}/join`.
- **Example Payloads Sent**:

  ```json
  // To /api/v1/tasks/create
  {
    "task_id": "1d13378a-2597-42c4-a2bf-4cf56e968c2b",
    "price": 1000
  }

  // To /api/v1/tasks/1d13378a-2597-42c4-a2bf-4cf56e968c2b/join
  {
    "agent_id": "kognys_test"
  }
  ```

### Task Finishing

- **API Endpoint Used**: `POST /api/v1/tasks/{task_id}/finish`
- **Trigger**: This is handled by the `PublisherAgent` (`kognys/agents/publisher.py`) at the very end of a successful research job, after all data has been stored.
- **Logic**: The `finish_task` function is called using the `task_id` that was created at the start of the process.
- **Example Payload Sent**:
  ```json
  // To /api/v1/tasks/1d13378a-2597-42c4-a2bf-4cf56e968c2b/finish
  {
    "agent_id": "kognys_test"
  }
  ```

---

## 3. Decentralized Memory Storage

At the end of a research task, the results are stored in Membase's active memory layer for different purposes.

### Storing the Final Answer (Knowledge Base)

- **API Endpoint Used**: `POST /api/v1/knowledge/documents`
- **Trigger**: Handled by the `PublisherAgent` via the `store_final_answer_in_kb` function.
- **Purpose**: To make the final, refined research paper **searchable** for future Kognys agents.
- **Logic**: A JSON object is constructed containing the final answer as `content` and key details in `metadata`. The API expects the document to be inside a list.
- **Example Payload Sent**:
  ```json
  {
    "documents": [
      {
        "content": "Based solely on the provided documents, generative AI presents several promising applications...",
        "metadata": {
          "paper_id": "1d13378a-2597-42c4-a2bf-4cf56e968c2b",
          "original_question": "What are the most promising applications of generative AI in software development?"
        }
      }
    ]
  }
  ```

### Storing the Debate Transcript (Conversation History)

- **API Endpoint Used**: `POST /api/v1/memory/conversations/{conversation_id}/messages`
- **Trigger**: Handled by the `PublisherAgent` via the `store_transcript_in_memory` function.
- **Purpose**: To store the agent's step-by-step **reasoning process** as an operational log.
- **Logic**: The Kognys internal transcript (a list of dictionaries with keys like `agent`, `action`) is transformed into the message format expected by the Membase API (a list of dictionaries with keys `name`, `content`, `role`).
- **Example Payload Sent**:
  ```json
  {
    "messages": [
      {
        "name": "InputValidator",
        "content": "Validated question & created on-chain task: Task ID: 1d13378a-2597-42c4-a2bf-4cf56e968c2b",
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
