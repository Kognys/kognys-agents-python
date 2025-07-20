# Kognys: AI Research Agent API

A multi-agent AI research system with **real-time token-based streaming** capabilities. Built for the BNB AI Hackathon (Unibase Track).

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

### 1. Standard Research (Synchronous)

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

### 2. 🔥 Real-Time Streaming (Server-Sent Events)

**POST** `/papers/stream` - **Primary API Endpoint**

```bash
curl -X POST http://localhost:8000/papers/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Your question", "user_id": "user123"}' \
  --no-buffer
```

**✨ Key Features:**

- **Token-by-token streaming** from LLM responses
- **Real-time progress updates** as research happens
- **Immediate feedback** - see text being generated live
- **Complete research workflow** with live agent interactions

### 3. Retrieve Papers

**GET** `/papers/{paper_id}` - Get specific paper
**GET** `/users/{user_id}/papers` - Get all user papers

---

## 🎯 Token-Based Streaming Events

The SSE endpoint provides granular, real-time events:

### **Research Progress Events:**

```json
{"event_type": "research_started", "data": {"status": "Starting research process..."}}
{"event_type": "question_validated", "data": {"status": "Question validated and refined"}}
{"event_type": "documents_retrieved", "data": {"document_count": 5, "status": "Retrieved 5 relevant documents"}}
```

### **🔥 Token-Level Streaming Events:**

```json
{"event_type": "draft_answer_token", "data": {"token": "The"}}
{"event_type": "draft_answer_token", "data": {"token": " importance"}}
{"event_type": "draft_answer_token", "data": {"token": " of"}}
{"event_type": "criticism_token", "data": {"criticism": "Needs more specific examples"}}
{"event_type": "final_answer_token", "data": {"token": "In"}}
{"event_type": "final_answer_token", "data": {"token": " conclusion"}}
```

### **Completion Events:**

```json
{"event_type": "draft_generated", "data": {"status": "Initial draft generated"}}
{"event_type": "criticisms_received", "data": {"criticism_count": 2, "status": "Received 2 criticisms"}}
{"event_type": "orchestrator_decision", "data": {"decision": "FINALIZE", "status": "Orchestrator decided: FINALIZE"}}
{"event_type": "research_completed", "data": {"final_answer": "...", "status": "Research completed successfully"}}
{"event_type": "paper_generated", "data": {"paper_id": "uuid", "paper_content": "...", "status": "completed"}}
```

---

## 🔧 SSE Integration Guide

### JavaScript Example

```javascript
const eventSource = new EventSource("http://localhost:8000/papers/stream", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "What are the latest AI developments?",
    user_id: "frontend-user",
  }),
});

// Real-time token streaming
let currentDraft = "";
let currentCriticisms = [];
let finalAnswer = "";

eventSource.onmessage = function (event) {
  const data = JSON.parse(event.data);

  switch (data.event_type) {
    case "research_started":
      console.log("🚀 Research started");
      break;

    case "draft_answer_token":
      // Build draft token by token
      currentDraft += data.data.token || "";
      updateUI("draft", currentDraft);
      break;

    case "criticism_token":
      // Collect criticisms as they arrive
      currentCriticisms.push(data.data.criticism);
      updateUI("criticisms", currentCriticisms);
      break;

    case "final_answer_token":
      // Build final answer token by token
      finalAnswer += data.data.token || "";
      updateUI("final", finalAnswer);
      break;

    case "research_completed":
      console.log("✅ Research completed!");
      console.log("Final answer:", data.data.final_answer);
      break;

    case "paper_generated":
      console.log("📄 Paper generated with ID:", data.data.paper_id);
      // Paper is ready for download/display
      break;

    case "error":
      console.error("❌ Error:", data.data.error);
      break;
  }
};

function updateUI(section, content) {
  // Update your UI components with streaming content
  document.getElementById(section).textContent = content;
}
```

### Python Client Example

```python
import requests
import json

def stream_research(question: str, user_id: str):
    """Stream research with real-time token updates."""

    url = "http://localhost:8000/papers/stream"
    payload = {"message": question, "user_id": user_id}

    response = requests.post(url, json=payload, stream=True)

    current_draft = ""
    current_criticisms = []
    final_answer = ""

    for line in response.iter_lines():
        if line:
            # SSE format: "data: {json}\n\n"
            if line.startswith(b'data: '):
                json_data = line[6:]  # Remove "data: "
                event = json.loads(json_data)

                event_type = event.get('event_type')
                data = event.get('data', {})

                if event_type == 'draft_answer_token':
                    current_draft += data.get('token', '')
                    print(f"Draft: {current_draft}")

                elif event_type == 'criticism_token':
                    criticism = data.get('criticism')
                    current_criticisms.append(criticism)
                    print(f"Criticism: {criticism}")

                elif event_type == 'final_answer_token':
                    final_answer += data.get('token', '')
                    print(f"Final: {final_answer}")

                elif event_type == 'research_completed':
                    print("✅ Research completed!")
                    return data.get('final_answer')

                elif event_type == 'error':
                    print(f"❌ Error: {data.get('error')}")
                    break

# Usage
final_result = stream_research(
    "What is token-based streaming in LLMs?",
    "python-client"
)
```

---

## 🎯 Multi-Agent Research Workflow

### Smart Question Processing

The system automatically validates and reformulates questions:

- **Input**: "Tell me about AI"
- **Reformulated**: "What are the current state-of-the-art developments in artificial intelligence research?"

### Real-Time Agent Pipeline

1. **🔍 Validator** - Improves question quality
2. **📚 Retriever** - Searches academic sources
3. **✍️ Synthesizer** - Creates research drafts (token streaming)
4. **🤔 Challenger** - Provides critical feedback (token streaming)
5. **🎯 Orchestrator** - Decides next steps + final answer (token streaming)
6. **📤 Publisher** - Finalizes and stores results

### **Research Graph Flow**

```
Input Validator → Retriever → Synthesizer → Challenger → Orchestrator
                     ↑            ↑            ↑            ↓
                     └────────────┴────────────┴─────── Decision:
                                                        - Research Again
                                                        - Revise Draft
                                                        - Finalize → Publisher
```

**🔥 All agents stream tokens in real-time for immediate UI feedback!**

---

## 🧪 Testing

### Test Token Streaming

```bash
# Run the comprehensive streaming test
python tests/test_token_streaming.py
```

This test validates:

- ✅ Token-by-token streaming from all agents
- ✅ Real-time progress events
- ✅ Complete research workflow
- ✅ Error handling and recovery

### Quick API Tests

```bash
# Health check
curl http://localhost:8000/

# Standard research
curl -X POST http://localhost:8000/papers \
  -H "Content-Type: application/json" \
  -d '{"message": "AI ethics", "user_id": "test"}'

# Streaming research
curl -X POST http://localhost:8000/papers/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "AI ethics", "user_id": "test"}' \
  --no-buffer
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
MEMBASE_API_URL=...
UNIBASE_DA_API_URL=...
```

---

## 🚨 Error Handling

### Validation Errors

Questions that are too broad, unclear, or non-research-worthy return:

```json
{
  "event_type": "validation_error",
  "data": {
    "error": "Question rejected by validator",
    "suggestion": "Please rephrase your question..."
  }
}
```

### Streaming Error Recovery

- **Blockchain failures**: Research continues gracefully
- **API rate limits**: Automatic retry with backoff
- **Connection issues**: Clear error events sent via SSE
- **Token overflow**: Handles partial responses elegantly

---

## 🏗️ Architecture Highlights

### **Token-Based Streaming Benefits**

1. **🚀 Immediate Response**: Users see content being generated in real-time
2. **📊 Progress Tracking**: Live visibility into research process
3. **⚡ Better UX**: No waiting for complete responses
4. **🔄 Interactive**: Can process partial responses as they arrive
5. **💪 Robust**: Graceful handling of interruptions

### **SSE vs WebSocket Choice**

- **SSE**: Simpler, more reliable, better for one-way streaming
- **No WebSocket complexity**: Easier integration and debugging
- **Better browser support**: Works with standard HTTP infrastructure
- **Automatic reconnection**: Built-in resilience

---

## 📦 Deployment

### Local Development

```bash
uvicorn api_main:app --reload
```

### Production

```bash
uvicorn api_main:app --host 0.0.0.0 --port 8000 --workers 1
```

**Note**: Use single worker for SSE streaming to maintain connection state.

---

## 🔥 What's New in This Version

- ✅ **Full SSE implementation** - Removed WebSocket complexity
- ✅ **Token-by-token streaming** - Real-time content generation
- ✅ **Async agent architecture** - Better performance and streaming
- ✅ **Enhanced error handling** - Graceful degradation for all failures
- ✅ **Improved efficiency** - Reduced research cycles from 25+ to 3-4
- ✅ **Better blockchain integration** - Robust retry logic and task validation

**Built for BNB AI Hackathon - Real-time AI research with live token streaming** 🚀
