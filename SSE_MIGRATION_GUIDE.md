# 🔄 SSE Migration Guide - WebSocket to Server-Sent Events

**Important**: This API has been updated to use **Server-Sent Events (SSE)** instead of WebSocket for better performance and simpler integration. This guide shows how to update your client code.

## 📋 Summary of Changes

### ✅ What's New

- **Token-by-token streaming** from LLM responses
- **SSE endpoint** as primary API (`/papers/stream`)
- **Simplified client integration** (no WebSocket complexity)
- **Better error handling** and automatic reconnection
- **Enhanced performance** with async architecture

### ❌ What's Removed

- **WebSocket endpoint** (`/ws/research`) - **DEPRECATED**
- **WebSocket connection management** complexity
- **Custom reconnection logic** (SSE handles this automatically)

---

## 🚀 Quick Migration Steps

### 1. Change Your Endpoint

**OLD (WebSocket):**

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/research");
```

**NEW (SSE):**

```javascript
const response = await fetch("http://localhost:8000/papers/stream", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: "Your research question",
    user_id: "your-user-id",
  }),
});
```

### 2. Update Event Handling

**OLD (WebSocket):**

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.type, data.data);
};
```

**NEW (SSE):**

```javascript
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split("\n");

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const event = JSON.parse(line.slice(6));
      console.log(event.event_type, event.data);
    }
  }
}
```

---

## 🔥 New Token-Based Streaming Events

Your client will now receive **token-level events** for real-time content generation:

### Token Events (NEW!)

```javascript
// These are new and provide word-by-word streaming
case 'draft_answer_token':
  currentDraft += event.data.token;
  break;

case 'criticism_token':
  criticisms.push(event.data.criticism);
  break;

case 'final_answer_token':
  finalAnswer += event.data.token;
  break;
```

### Node Events (Updated)

```javascript
// These existed before but now have consistent naming
case 'research_started':         // Was: connection_established
case 'question_validated':       // Same
case 'documents_retrieved':      // Same
case 'draft_generated':          // Same
case 'criticisms_received':      // Same
case 'orchestrator_decision':    // Same
case 'research_completed':       // Same
case 'paper_generated':          // NEW - includes paper_id and content
```

---

## 📝 Complete Migration Examples

### JavaScript/TypeScript Frontend

**OLD WebSocket Implementation:**

```javascript
class WebSocketClient {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
  }

  connect() {
    this.ws = new WebSocket("ws://localhost:8000/ws/research");

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.ws.send(
        JSON.stringify({
          message: this.question,
          user_id: this.userId,
        })
      );
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleEvent(data.type, data.data);
    };

    this.ws.onclose = () => {
      this.reconnect();
    };
  }

  reconnect() {
    if (this.reconnectAttempts < 5) {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, 1000 * this.reconnectAttempts);
    }
  }
}
```

**NEW SSE Implementation:**

```javascript
class SSEClient {
  async startResearch(question, userId) {
    try {
      const response = await fetch("http://localhost:8000/papers/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question, user_id: userId }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // State for building responses token by token
      this.currentDraft = "";
      this.criticisms = [];
      this.finalAnswer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        this.processChunk(chunk);
      }
    } catch (error) {
      console.error("Streaming error:", error);
      // SSE automatically handles reconnection
    }
  }

  processChunk(chunk) {
    const lines = chunk.split("\n");

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const event = JSON.parse(line.slice(6));
          this.handleEvent(event.event_type, event.data);
        } catch (e) {
          // Skip invalid JSON
        }
      }
    }
  }

  handleEvent(eventType, data) {
    switch (eventType) {
      case "research_started":
        this.updateStatus("🚀 Research started...");
        break;

      case "draft_answer_token":
        // NEW: Build answer token by token
        this.currentDraft += data.token || "";
        this.updateDraftDisplay(this.currentDraft);
        break;

      case "criticism_token":
        // NEW: Show criticisms as they arrive
        this.criticisms.push(data.criticism);
        this.updateCriticismsDisplay(this.criticisms);
        break;

      case "final_answer_token":
        // NEW: Build final answer token by token
        this.finalAnswer += data.token || "";
        this.updateFinalDisplay(this.finalAnswer);
        break;

      case "research_completed":
        this.updateStatus("✅ Research completed!");
        this.finalResult = data.final_answer;
        break;

      case "paper_generated":
        // NEW: Paper is ready with ID
        this.paperId = data.paper_id;
        this.paperContent = data.paper_content;
        this.showPaper(this.paperId, this.paperContent);
        break;

      case "error":
        this.handleError(data.error);
        break;
    }
  }

  // Helper methods for UI updates
  updateStatus(status) {
    document.getElementById("status").textContent = status;
  }

  updateDraftDisplay(draft) {
    document.getElementById("draft").textContent = draft;
  }

  updateCriticismsDisplay(criticisms) {
    const list = document.getElementById("criticisms");
    list.innerHTML = criticisms.map((c) => `<li>${c}</li>`).join("");
  }

  updateFinalDisplay(answer) {
    document.getElementById("final-answer").textContent = answer;
  }

  showPaper(paperId, content) {
    console.log(`Paper ${paperId} ready:`, content);
    // Display final paper to user
  }
}
```

### Python Client

**OLD WebSocket Implementation:**

```python
import asyncio
import websockets
import json

async def websocket_client():
    uri = "ws://localhost:8000/ws/research"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "message": "Research question",
            "user_id": "python-client"
        }))

        async for message in websocket:
            event = json.loads(message)
            print(f"Event: {event['type']}")

            if event['type'] == 'research_completed':
                return event['data']['final_answer']
```

**NEW SSE Implementation:**

```python
import requests
import json

def sse_client(question: str, user_id: str):
    """Stream research with real-time token updates."""

    url = "http://localhost:8000/papers/stream"
    payload = {"message": question, "user_id": user_id}

    # State for building responses
    current_draft = ""
    criticisms = []
    final_answer = ""

    response = requests.post(url, json=payload, stream=True)

    for line in response.iter_lines():
        if line and line.startswith(b'data: '):
            try:
                event = json.loads(line[6:])  # Remove "data: "
                event_type = event.get('event_type')
                data = event.get('data', {})

                if event_type == 'research_started':
                    print("🚀 Research started...")

                elif event_type == 'draft_answer_token':
                    # Build draft token by token
                    current_draft += data.get('token', '')
                    print(f"\rDraft: {current_draft}", end='', flush=True)

                elif event_type == 'criticism_token':
                    criticism = data.get('criticism')
                    criticisms.append(criticism)
                    print(f"\n💭 Criticism: {criticism}")

                elif event_type == 'final_answer_token':
                    final_answer += data.get('token', '')
                    print(f"\rFinal: {final_answer}", end='', flush=True)

                elif event_type == 'research_completed':
                    print("\n✅ Research completed!")
                    return data.get('final_answer')

                elif event_type == 'paper_generated':
                    paper_id = data.get('paper_id')
                    print(f"\n📄 Paper generated with ID: {paper_id}")
                    return data.get('paper_content')

                elif event_type == 'error':
                    print(f"\n❌ Error: {data.get('error')}")
                    break

            except json.JSONDecodeError:
                continue  # Skip invalid JSON

    return final_answer

# Usage
result = sse_client("What is quantum computing?", "python-client")
print(f"Final result: {result}")
```

### React/Next.js Component

**NEW React SSE Hook:**

```javascript
import { useState, useEffect } from "react";

export function useSSEResearch() {
  const [draft, setDraft] = useState("");
  const [criticisms, setCriticisms] = useState([]);
  const [finalAnswer, setFinalAnswer] = useState("");
  const [status, setStatus] = useState("");
  const [paperId, setPaperId] = useState(null);
  const [error, setError] = useState(null);

  const startResearch = async (question, userId) => {
    // Reset state
    setDraft("");
    setCriticisms([]);
    setFinalAnswer("");
    setError(null);

    try {
      const response = await fetch("/api/papers/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question, user_id: userId }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6));
              handleEvent(event.event_type, event.data);
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEvent = (eventType, data) => {
    switch (eventType) {
      case "research_started":
        setStatus("🚀 Research started...");
        break;

      case "draft_answer_token":
        setDraft((prev) => prev + (data.token || ""));
        break;

      case "criticism_token":
        setCriticisms((prev) => [...prev, data.criticism]);
        break;

      case "final_answer_token":
        setFinalAnswer((prev) => prev + (data.token || ""));
        break;

      case "research_completed":
        setStatus("✅ Research completed!");
        break;

      case "paper_generated":
        setPaperId(data.paper_id);
        setStatus(`📄 Paper ready: ${data.paper_id}`);
        break;

      case "error":
        setError(data.error);
        break;
    }
  };

  return {
    draft,
    criticisms,
    finalAnswer,
    status,
    paperId,
    error,
    startResearch,
  };
}

// Usage in component
export function ResearchComponent() {
  const {
    draft,
    criticisms,
    finalAnswer,
    status,
    paperId,
    error,
    startResearch,
  } = useSSEResearch();

  const handleSubmit = (e) => {
    e.preventDefault();
    const question = e.target.question.value;
    startResearch(question, "react-user");
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input name="question" placeholder="Ask a research question..." />
        <button type="submit">Start Research</button>
      </form>

      <div className="status">{status}</div>

      {error && <div className="error">Error: {error}</div>}

      {draft && (
        <div className="draft">
          <h3>Draft (Live):</h3>
          <p>{draft}</p>
        </div>
      )}

      {criticisms.length > 0 && (
        <div className="criticisms">
          <h3>Criticisms:</h3>
          <ul>
            {criticisms.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      {finalAnswer && (
        <div className="final">
          <h3>Final Answer:</h3>
          <p>{finalAnswer}</p>
        </div>
      )}

      {paperId && (
        <div className="paper">
          <h3>Paper Ready!</h3>
          <p>Paper ID: {paperId}</p>
          <button onClick={() => downloadPaper(paperId)}>Download Paper</button>
        </div>
      )}
    </div>
  );
}
```

---

## ⚡ Performance & Benefits

### Why SSE is Better

1. **🚀 Simpler Integration**: No WebSocket connection management
2. **📊 Token Streaming**: See content being generated word-by-word
3. **🔄 Auto Reconnection**: Built into browser SSE implementation
4. **⚡ Better Performance**: More efficient than WebSocket for one-way streaming
5. **🛡️ More Reliable**: Works better through proxies and firewalls
6. **📱 Mobile Friendly**: Better battery usage and connection handling

### Token-Level UX Benefits

- **Immediate Feedback**: Users see content being generated instantly
- **Progress Indication**: Visual progress without loading spinners
- **Early Termination**: Can stop generation if content isn't relevant
- **Better Engagement**: Users stay engaged watching content appear

---

## 🚨 Migration Checklist

### ✅ Required Changes

- [ ] **Replace WebSocket connection** with SSE fetch request
- [ ] **Update event handling** to use `event_type` instead of `type`
- [ ] **Add token event handlers** for `draft_answer_token`, `criticism_token`, `final_answer_token`
- [ ] **Remove reconnection logic** (SSE handles this automatically)
- [ ] **Update error handling** for fetch/stream errors

### ✅ Optional Enhancements

- [ ] **Add real-time UI updates** for token streaming
- [ ] **Implement progressive display** of draft content
- [ ] **Add typing indicators** based on token events
- [ ] **Store paper_id** from `paper_generated` event for later retrieval

### ✅ Testing

- [ ] **Test basic research flow** with new SSE endpoint
- [ ] **Verify token streaming** displays correctly
- [ ] **Test error scenarios** (network issues, invalid questions)
- [ ] **Check mobile compatibility** and battery usage

---

## 🆘 Troubleshooting

### Common Issues

**Q: SSE connection drops frequently**
A: Check your proxy/firewall settings. SSE uses standard HTTP and should work better than WebSocket.

**Q: Not receiving token events**
A: Ensure you're parsing the `data: ` prefix correctly and handling JSON parsing errors.

**Q: UI performance issues with token streaming**
A: Consider debouncing UI updates or using requestAnimationFrame for smooth rendering.

**Q: How to handle long-running research?**
A: SSE connections can run indefinitely. The API will complete naturally when research finishes.

### Debug Tips

```javascript
// Add debugging to see raw SSE events
const lines = chunk.split("\n");
for (const line of lines) {
  console.log("Raw line:", line); // Debug raw SSE data
  if (line.startsWith("data: ")) {
    const event = JSON.parse(line.slice(6));
    console.log("Parsed event:", event); // Debug parsed events
  }
}
```

---

## 📞 Support

If you need help migrating or encounter issues:

1. **Check the updated README.md** for latest documentation
2. **Run the test suite**: `python tests/test_token_streaming.py`
3. **Test with curl**: See README.md for curl examples
4. **Check server logs** for any backend issues

**The SSE approach provides better performance, simpler integration, and exciting new token-level streaming capabilities!** 🚀
