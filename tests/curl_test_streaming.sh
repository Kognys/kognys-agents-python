#!/bin/bash

# Test script for enhanced streaming endpoint with paper ID
# This demonstrates the /papers/stream endpoint that now includes paper_id

echo "🚀 Testing Enhanced Streaming API with Paper ID"
echo "=============================================="
echo ""
echo "Endpoint: POST /papers/stream"
echo "Expected: Real-time events + paper_id + paper_generated event"
echo ""

# Make sure server is running
echo "📡 Sending streaming request..."
echo ""

curl -X POST http://localhost:8000/papers/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "What are the key benefits of renewable energy?",
    "user_id": "curl_test_user"
  }' \
  --no-buffer \
  -w "\n\n📊 Response Status: %{http_code}\n" \
  | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
      # Parse the JSON data after "data: "
      json_data="${line#data: }"
      
      # Extract event type and paper_id if present
      event_type=$(echo "$json_data" | grep -o '"event_type":"[^"]*"' | cut -d'"' -f4)
      paper_id=$(echo "$json_data" | grep -o '"paper_id":"[^"]*"' | cut -d'"' -f4)
      
      if [[ -n "$event_type" ]]; then
        printf "📨 Event: %-20s" "$event_type"
        if [[ -n "$paper_id" ]]; then
          echo " | 📄 Paper ID: $paper_id"
        else
          echo ""
        fi
        
        # Special handling for paper_generated event
        if [[ "$event_type" == "paper_generated" ]]; then
          echo "🎉 PAPER GENERATED EVENT RECEIVED!"
          echo "   This event contains the paper_id and full paper content"
          break
        fi
      fi
    fi
  done

echo ""
echo "✅ Test completed! Check above for paper_id in events."
echo ""
echo "Expected events with paper_id:"
echo "  - research_completed (should have paper_id)"
echo "  - paper_generated (final event with paper_id + content)" 