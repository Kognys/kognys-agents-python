# Kognys: AI Research Agent API

A multi-agent AI research system with real-time streaming capabilities. Built for the BNB AI Hackathon (Unibase Track).

## 🚀 Quick Start

### Setup

```bash
git clone <your-repo-url>
cd kognys-agents-python-2
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env-example .env  # Fill in your API keys
```

### Start Server

```bash
uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload
```

Server runs at `http://localhost:8000`

---

## 📡 API Reference

### 1. Standard Research

**POST** `/papers`

```json
{
  "message": "What are the latest developments in AI?",
  "user_id": "user123"
}
```

Response:

```json
{
  "paper_id": "unique-id",
  "paper_content": "Complete research paper..."
}
```

### 2. Server-Sent Events (SSE)

**POST** `/papers/stream`

```bash
curl -X POST http://localhost:8000/papers/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Your question", "user_id": "user123"}' \
  --no-buffer
```

Returns real-time events as they occur during research. Includes paper ID in events once research completes.

**Stream Events Include:**

- Real-time progress updates
- Paper ID when research completes
- Final `paper_generated` event with complete paper content and ID

### 3. WebSocket (Real-Time)

**WebSocket** `/ws/research`

Connect and send:

```json
{
  "message": "Your research question",
  "user_id": "user123"
}
```

Receive real-time events:

- `connection_established` - Connected successfully
- `research_started` - Research begins
- `question_validated` - Question processed/reformulated
- `documents_retrieved` - Found X documents
- `draft_generated` - Research draft created
- `criticisms_received` - Critical feedback received
- `orchestrator_decision` - Next step decided
- `research_completed` - Final result ready
- `paper_generated` - Paper ID and full content available (SSE only)
- `validation_error` - Question needs improvement

---

## 🔧 WebSocket Integration

### JavaScript Example

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/research");

ws.onopen = () => {
  ws.send(
    JSON.stringify({
      message: "What are the latest AI developments?",
      user_id: "frontend-user",
    })
  );
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Event: ${data.type}`, data.data);

  switch (data.type) {
    case "question_validated":
      console.log("Question approved:", data.data.status);
      break;
    case "documents_retrieved":
      console.log(`Found ${data.data.document_count} documents`);
      break;
    case "research_completed":
      console.log("Research done:", data.data.final_answer);
      break;
    case "paper_generated":
      console.log("Paper ID:", data.data.paper_id);
      console.log("Paper ready:", data.data.paper_content);
      break;
    case "validation_error":
      console.log("Error:", data.data.error);
      break;
  }
};
```

### Python Client Example

```python
import asyncio
import websockets
import json

async def research_client():
    uri = "ws://localhost:8000/ws/research"
    async with websockets.connect(uri) as websocket:
        # Send research request
        await websocket.send(json.dumps({
            "message": "What are quantum computers?",
            "user_id": "python-client"
        }))

        # Listen for events
        async for message in websocket:
            event = json.loads(message)
            print(f"Received: {event['type']}")

            if event['type'] == 'research_completed':
                print("Final answer:", event['data']['final_answer'])
                break

asyncio.run(research_client())
```

---

## 🎯 Key Features

### Smart Question Processing

The system automatically validates and reformulates questions:

- **Input**: "Tell me about AI"
- **Reformulated**: "What are the current state-of-the-art developments in artificial intelligence research?"

### Multi-Agent Research

1. **Validator** - Improves question quality
2. **Retriever** - Searches academic sources
3. **Synthesizer** - Creates research drafts
4. **Challenger** - Provides critical feedback
5. **Orchestrator** - Decides next steps
6. **Publisher** - Finalizes results

## 🏗️ System Architecture

### **Research Graph Flow**

````
Input Validator → Retriever → Synthesizer → Challenger → Orchestrator
                     ↑            ↑            ↑            ↓
                     └────────────┴────────────┴─────── Decision:
                                                        - Research Again
                                                        - Revise Draft
                                                        - Finalize → Publisher

### Real-Time Streaming

All agent actions stream live via WebSocket or SSE, enabling:

- Progress tracking
- Live research visualization
- Error handling
- User experience optimization


---

## 🧪 Testing

### Frontend Test Interface

```bash
open tests/websocket_test.html
````

Interactive web interface for testing WebSocket functionality.

### Quick API Test

```bash
# Health check
curl http://localhost:8000/

# Standard research
curl -X POST http://localhost:8000/papers \
  -H "Content-Type: application/json" \
  -d '{"message": "AI ethics", "user_id": "test"}'
```

---

## ⚙️ Environment Variables

Required in `.env`:

```env
GOOGLE_API_KEY=...
POWERFUL_LLM_MODEL=gpt-4
MONGODB_URI=mongodb://...
MEMBASE_API_KEY=...
MEMBASE_ID=kognys_starter
```

---

## 🚨 Error Handling

### Validation Errors

Questions that are too broad, unclear, or non-research-worthy return:

```json
{
  "type": "validation_error",
  "data": {
    "error": "Question rejected by validator",
    "suggestion": "Please rephrase your question..."
  }
}
```

### Common Issues

- **WebSocket disconnects**: Check server logs and network connectivity
- **No streaming events**: Verify unified_executor callbacks are working
- **Validation failures**: Ensure questions are research-oriented

---

## 📦 Deployment

### Local Development

```bash
uvicorn api_main:app --reload
```

### Production

```bash
uvicorn api_main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

**Built for BNB AI Hackathon - Real-time AI research at scale**
