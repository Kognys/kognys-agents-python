#!/usr/bin/env python3
"""
Test: Live Kognys Research Agent using the Streaming API

This test uses the /papers/stream endpoint to demonstrate real-time
streaming functionality via the API rather than direct graph execution.
Located in tests folder as requested.
"""

import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_live_streaming():
    """
    Run a live research session using the streaming API endpoint.
    This demonstrates the real-time streaming capabilities of the Kognys API.
    """
    
    # Configuration
    api_url = "http://localhost:8000/papers/stream"
    research_question = "What are the most promising applications of generative AI in software development?"
    user_id = "live_streaming_test"
    
    print("=" * 80)
    print("🚀 KOGNYS LIVE STREAMING RESEARCH AGENT 🚀")
    print("=" * 80)
    print(f"📡 API Endpoint: {api_url}")
    print(f"❓ Research Question: {research_question}")
    print(f"👤 User ID: {user_id}")
    print("=" * 80)
    print()
    
    # Prepare the request
    payload = {
        "message": research_question,
        "user_id": user_id
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    print("📡 Connecting to streaming endpoint...")
    print("⏳ Waiting for research to begin...\n")
    
    try:
        # Make the streaming request
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            stream=True,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        print("✅ Connected to streaming API!")
        print("📺 Live streaming events:\n")
        print("-" * 60)
        
        # Track research progress
        step_counter = 1
        events_received = 0
        paper_id = None
        final_content = None
        start_time = time.time()
        
        # Process streaming events
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    # Parse the event data
                    event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                    events_received += 1
                    
                    event_type = event_data.get('event_type', 'unknown')
                    data = event_data.get('data', {})
                    timestamp = event_data.get('timestamp', time.time())
                    
                    # Format timestamp
                    elapsed = timestamp - start_time
                    time_str = f"[{elapsed:.1f}s]"
                    
                    print(f"📨 {time_str} Step {step_counter}: {event_type.upper()}")
                    
                    # Handle different event types
                    if event_type == "research_started":
                        print(f"   🚀 Status: {data.get('status', 'Started')}")
                        
                    elif event_type == "question_validated":
                        validated_q = data.get('validated_question', 'N/A')
                        print(f"   ✅ Validated: \"{validated_q}\"")
                        
                    elif event_type == "documents_retrieved":
                        doc_count = data.get('document_count', 0)
                        print(f"   📚 Retrieved: {doc_count} documents")
                        
                    elif event_type == "draft_generated":
                        draft_length = data.get('draft_length', 0)
                        print(f"   ✍️  Draft: {draft_length} characters generated")
                        
                    elif event_type == "criticisms_received":
                        crit_count = data.get('criticism_count', 0)
                        print(f"   🤔 Criticisms: {crit_count} feedback points")
                        
                    elif event_type == "orchestrator_decision":
                        decision = data.get('decision', 'unknown')
                        print(f"   ⚙️  Decision: {decision}")
                        if decision in ["RESEARCH_AGAIN", "FINALIZE", "REVISE"]:
                            print(f"       Next step: {'Research with new query' if decision == 'RESEARCH_AGAIN' else 'Generate final answer' if decision == 'FINALIZE' else 'Revise current draft'}")
                        
                    elif event_type == "research_completed":
                        print(f"   🎉 Research completed!")
                        if 'paper_id' in data:
                            paper_id = data['paper_id']
                            print(f"   📄 Paper ID: {paper_id}")
                            
                    elif event_type == "paper_generated":
                        paper_id = data.get('paper_id', 'N/A')
                        final_content = data.get('paper_content', '')
                        print(f"   📄 Paper ID: {paper_id}")
                        print(f"   📝 Content Length: {len(final_content)} characters")
                        print(f"   ✅ Status: {data.get('status', 'completed')}")
                        break  # Final event
                        
                    elif event_type == "validation_error":
                        error_msg = data.get('error', 'Unknown error')
                        suggestion = data.get('suggestion', 'Please try again')
                        print(f"   ❌ Error: {error_msg}")
                        print(f"   💡 Suggestion: {suggestion}")
                        break
                        
                    elif event_type == "error":
                        error_msg = data.get('error', 'Unknown error')
                        print(f"   ❌ Error: {error_msg}")
                        break
                    
                    else:
                        # Generic event handling
                        status = data.get('status', 'Event received')
                        print(f"   ℹ️  Status: {status}")
                    
                    step_counter += 1
                    print()
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    continue
                    
        print("-" * 60)
        
        # Summary
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n📊 RESEARCH SUMMARY")
        print("=" * 40)
        print(f"⏱️  Total Time: {total_time:.1f} seconds")
        print(f"📨 Events Received: {events_received}")
        print(f"📄 Paper ID: {paper_id or 'Not generated'}")
        
        if final_content:
            print(f"📝 Final Paper Length: {len(final_content)} characters")
            print("\n" + "=" * 80)
            print("📄 FINAL RESEARCH PAPER")
            print("=" * 80)
            print(final_content)
        else:
            print("❌ No final paper content received")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot connect to the API server")
        print("💡 Make sure the server is running:")
        print("   uvicorn api_main:app --host 0.0.0.0 --port 8000 --reload")
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: Research took too long to complete")
        
    except KeyboardInterrupt:
        print("\n⏹️  Research interrupted by user")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main entry point for the live streaming research demo."""
    run_live_streaming()

if __name__ == "__main__":
    main() 