# Kognys Streaming API

This document describes the streaming implementation for the Kognys Research Agent API, which provides real-time updates during the research process.

## Overview

The streaming API allows clients to receive real-time updates as the research process progresses through different stages. Instead of waiting for the entire process to complete, clients can see progress updates and intermediate results as they happen.

## API Endpoints

### Streaming Research Endpoint

**POST** `/papers/stream`

Initiates a research task with streaming updates via Server-Sent Events (SSE).

#### Request Body

```json
{
  "message": "What are the latest developments in quantum computing?",
  "user_id": "user123"
}
```

#### Response

The response is a Server-Sent Events stream with the following format:

```
data: {"event_type": "research_started", "data": {...}, "timestamp": 1234567890.123}

data: {"event_type": "question_validated", "data": {...}, "timestamp": 1234567890.456}

data: {"event_type": "documents_retrieved", "data": {...}, "timestamp": 1234567890.789}

...

data: {"event_type": "research_completed", "data": {...}, "timestamp": 1234567891.012}
```

## Event Types

### 1. `research_started`

Emitted when the research process begins.

```json
{
  "event_type": "research_started",
  "data": {
    "question": "What are the latest developments in quantum computing?",
    "task_id": "uuid-here",
    "status": "Starting research process..."
  },
  "timestamp": 1234567890.123
}
```

### 2. `question_validated`

Emitted when the input validator has processed and refined the question.

```json
{
  "event_type": "question_validated",
  "data": {
    "validated_question": "What are the latest developments in quantum computing technology?",
    "status": "Question validated and refined"
  },
  "timestamp": 1234567890.456
}
```

### 3. `documents_retrieved`

Emitted when relevant documents have been found and retrieved.

```json
{
  "event_type": "documents_retrieved",
  "data": {
    "document_count": 5,
    "status": "Retrieved 5 relevant documents"
  },
  "timestamp": 1234567890.789
}
```

### 4. `draft_generated`

Emitted when the initial draft answer has been generated.

```json
{
  "event_type": "draft_generated",
  "data": {
    "draft_length": 1250,
    "status": "Initial draft generated"
  },
  "timestamp": 1234567891.012
}
```

### 5. `criticisms_received`

Emitted when criticisms have been received for the draft.

```json
{
  "event_type": "criticisms_received",
  "data": {
    "criticism_count": 3,
    "status": "Received 3 criticisms for improvement"
  },
  "timestamp": 1234567891.345
}
```

### 6. `research_completed`

Emitted when the research process has completed successfully.

```json
{
  "event_type": "research_completed",
  "data": {
    "final_answer": "Based on recent research, quantum computing has made significant progress...",
    "status": "Research completed successfully"
  },
  "timestamp": 1234567891.678
}
```

### 7. `research_failed`

Emitted when the research process fails to generate a final answer.

```json
{
  "event_type": "research_failed",
  "data": {
    "error": "No final answer generated",
    "status": "Research process failed to generate a final answer"
  },
  "timestamp": 1234567891.901
}
```

### 8. `error`

Emitted when an error occurs during the research process.

```json
{
  "event_type": "error",
  "data": {
    "error": "Connection timeout",
    "status": "An error occurred during research"
  },
  "timestamp": 1234567892.012
}
```

## Client Examples

### JavaScript/HTML

```javascript
const response = await fetch("/papers/stream", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: "What are the latest developments in quantum computing?",
    user_id: "user123",
  }),
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
      const eventData = JSON.parse(line.slice(6));
      console.log("Received event:", eventData);

      // Handle different event types
      switch (eventData.event_type) {
        case "research_started":
          console.log("Research started!");
          break;
        case "research_completed":
          console.log("Research completed!");
          break;
        // ... handle other events
      }
    }
  }
}
```

### Python

```python
import asyncio
import aiohttp
import json

async def stream_research():
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8000/papers/stream',
            json={
                'message': 'What are the latest developments in quantum computing?',
                'user_id': 'user123'
            }
        ) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    event_data = json.loads(line[6:])
                    print(f"Event: {event_data['event_type']}")

asyncio.run(stream_research())
```

## Benefits

1. **Better User Experience**: Users can see progress in real-time instead of waiting for the entire process to complete.

2. **Transparency**: Users can understand what's happening at each stage of the research process.

3. **Debugging**: Developers can see exactly where the process might be taking time or failing.

4. **Interactive UI**: Frontend applications can update their UI based on the current stage of the research.

## Implementation Details

The streaming implementation uses:

- **Server-Sent Events (SSE)**: A standard web technology for real-time updates
- **Asynchronous Processing**: The research graph runs in a separate thread to avoid blocking
- **Event Queue**: Events are queued and streamed as they occur
- **Threading**: The main graph execution runs in a background thread

## Error Handling

- Network errors are caught and reported as `error` events
- Invalid questions are caught early and reported as `research_failed` events
- Timeouts and other issues are handled gracefully

## Performance Considerations

- The streaming adds minimal overhead to the research process
- Events are emitted asynchronously to avoid blocking the main research flow
- The SSE connection is kept alive until the research process completes
- Memory usage is minimal as events are streamed rather than buffered
