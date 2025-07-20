# Kognys: A Decentralized Research Framework

[![Hackathon Project](https://img.shields.io/badge/BNB%20Chain-AI%20Hackathon-yellow)](https://bnbchain.org)
[![Track](https://img.shields.io/badge/Track-Unibase-blue)](https://unibase.xyz)

**Kognys** is a decentralized research framework powered by autonomous agents and verifiable memory. Built on the BNB Chain for the Unibase track of the BNB AI Hackathon, it enables collaborative knowledge creation across any research domain. By combining persistent memory, real-time collaboration, and on-chain verifiability, Kognys offers a powerful open-source infrastructure for researchers, analysts, and developers to build, share, and explore structured knowledge at scale.

## ✨ Core Features

- **Chain-of-Debate Reasoning**: Inspired by Microsoft’s MAI-DxO, Kognys uses a panel of specialized AI agents (`Retriever`, `Synthesizer`, `Challenger`) who debate and refine findings to produce high-quality, nuanced answers.
- **Intelligent Orchestration**: A central `OrchestratorAgent` manages the research flow, deciding when to revise a draft, conduct further research with new queries, or finalize the answer to prevent unproductive loops.
- **Multi-Source Research**: The `RetrieverAgent` automatically queries major academic databases, including **OpenAlex**, **arXiv**, and **Semantic Scholar**, to gather a broad and diverse set of source materials.
- **Verifiable Decentralized Memory**: Kognys utilizes a hybrid storage model:
  - **Unibase DA Layer**: The final research packet (answer, sources, and full debate transcript) is permanently archived for on-chain verification.
  - **Membase**: The final answer is stored in a searchable Knowledge Base, and the transcript is stored as a conversation history, creating an active, operational memory for the agent system.
- **On-Chain Verification**: A hash of the final research packet is published to a smart contract on the **BNB Chain Testnet**, creating a permanent, tamper-proof record of the agent's findings.

## 🛠️ Tech Stack

- **Orchestration**: Python with LangGraph
- **AI Models**: Google Gemini (`gemini-1.5-pro` & `gemini-1.5-flash`)
- **Backend**: FastAPI
- **Blockchain**: BNB Chain (Testnet) with `web3.py`
- **Decentralized Memory**: Unibase (Membase API & DA Layer)

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- An active `.env` file with the required API keys and environment variables.

### 1. Create a `.env` File

Copy the `env-example` file to a new file named `.env` and fill in the required values:

```bash
cp env-example .env
```

Your `.env` file should contain:

```dotenv
# Kognys Agent Identity (used for on-chain registration)
MEMBASE_ID="kognys-research-agent-001"
MEMBASE_ACCOUNT="YOUR_BNB_CHAIN_WALLET_ADDRESS"
MEMBASE_SECRET_KEY="YOUR_WALLET_PRIVATE_KEY"

# API Keys
GOOGLE_API_KEY="YOUR_GOOGLE_AI_STUDIO_API_KEY"
MEMBASE_API_URL="YOUR_PARTNER'S_MEMBASE_API_URL"
MEMBASE_API_KEY="YOUR_PARTNER'S_MEMBASE_API_KEY"
DA_SERVICE_URL="YOUR_DA_SERVICE_API_URL"

# LLM Configuration
FAST_LLM_MODEL="gemini-1.5-flash-latest"
POWERFUL_LLM_MODEL="gemini-1.5-pro-latest"

# API Configuration
ALLOWED_ORIGINS="http://localhost:8080,[https://www.kognys.xyz](https://www.kognys.xyz)"
```

### 2. Install Dependencies

Create a virtual environment and install the required packages:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the API Server

To start the FastAPI server for the Kognys agent:

```bash
uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload
```

The API documentation will be available at `http://localhost:8000/docs`.

### 4. Run a Live Local Test

To run a full research task directly from your terminal and see the agent's step-by-step reasoning, use the `run_live.py` script:

```bash
python3 run_live.py
```

---

## 📖 API Reference

The Kognys API provides endpoints to generate and retrieve research papers.

**Base URL**: `http://localhost:8000` (or your deployment URL)

### Health Check

- **Endpoint**: `GET /`
- **Description**: Checks if the API server is running.
- **Success Response** (`200 OK`):
  ```json
  { "status": "ok" }
  ```

### Create a Research Paper

- **Endpoint**: `POST /papers`
- **Description**: Initiates a new research task. The agent will perform its full Chain-of-Debate process and store the result.
- **Request Body**:
  ```json
  {
    "message": "What are the latest advancements in quantum computing?",
    "user_id": "user-12345"
  }
  ```
- **Success Response** (`200 OK`):
  ```json
  {
    "paper_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "paper_content": "Quantum computing has seen significant advancements..."
  }
  ```
- **Error Responses**:
  - `400 Bad Request`: If the input question is rejected by the `InputValidatorAgent` or if no sources are found. The response body will contain a helpful, AI-generated message.
  - `500 Internal Server Error`: If an unexpected error occurs during the agent's run.

### Retrieve a Research Paper

- **Endpoint**: `GET /papers/{paper_id}`
- **Description**: Retrieves a previously generated research paper from the Membase Knowledge Base.
- **Path Parameter**:
  - `paper_id` (string, required): The unique ID of the paper returned by the `POST /papers` endpoint.
- **Success Response** (`200 OK`):
  ```json
  {
    "paper_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "paper_content": "Quantum computing has seen significant advancements..."
  }
  ```
- **Error Response**:
  - `404 Not Found`: If no paper with the specified ID can be found in the Membase Knowledge Base.
