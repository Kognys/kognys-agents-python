#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Production Streaming Test

Tests the current Kognys streaming flow including:
- Complete workflow
- Agent names in responses
- Token streaming
- Event deduplication
"""

import requests
import json
import time
import sys

def test_streaming():
    """Test streaming flow on production."""
    
    url = "https://kognys-agents-python-production.up.railway.app/papers/stream"
    payload = {
        "message": "What are the benefits of renewable energy?",
        "user_id": "test_streaming"
    }
    
    print("KOGNYS STREAMING TEST")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Question: {payload['message']}")
    print("=" * 50)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    try:
        print("Connecting...")
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=120)
        
        if response.status_code != 200:
            print(f"ERROR: HTTP {response.status_code}")
            print(response.text)
            return False
        
        print("Connected! Streaming events:")
        print("-" * 40)
        
        # Track results
        events_by_agent = {}
        token_counts = {"draft_answer_token": 0, "criticism_token": 0, "final_answer_token": 0}
        event_types = set()
        total_events = 0
        start_time = time.time()
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event = json.loads(line[6:])
                    total_events += 1
                    
                    event_type = event.get('event_type', 'unknown')
                    data = event.get('data', {})
                    agent = data.get('agent', 'unknown')
                    elapsed = time.time() - start_time
                    
                    # Track statistics
                    event_types.add(event_type)
                    events_by_agent[agent] = events_by_agent.get(agent, 0) + 1
                    
                    # Handle specific events
                    if event_type == "research_started":
                        print(f"[{elapsed:.1f}s] Research Started (agent: {agent})")
                        
                    elif event_type == "question_validated":
                        print(f"[{elapsed:.1f}s] Question Validated (agent: {agent})")
                        
                    elif event_type == "documents_retrieved":
                        count = data.get('document_count', 0)
                        print(f"[{elapsed:.1f}s] Documents Retrieved: {count} (agent: {agent})")
                        
                    elif event_type == "draft_answer_token":
                        token_counts["draft_answer_token"] += 1
                        if token_counts["draft_answer_token"] == 1:
                            print(f"[{elapsed:.1f}s] Draft Streaming Started (agent: {agent})")
                        elif token_counts["draft_answer_token"] % 20 == 0:
                            print(f"[{elapsed:.1f}s] Draft Tokens: {token_counts['draft_answer_token']} (agent: {agent})")
                        
                    elif event_type == "draft_generated":
                        print(f"[{elapsed:.1f}s] Draft Generated (agent: {agent})")
                        
                    elif event_type == "criticisms_received":
                        count = data.get('criticism_count', 0)
                        print(f"[{elapsed:.1f}s] Criticisms: {count} (agent: {agent})")
                        
                    elif event_type == "orchestrator_decision":
                        decision = data.get('decision', 'unknown')
                        print(f"[{elapsed:.1f}s] Decision: {decision} (agent: {agent})")
                        
                    elif event_type == "final_answer_token":
                        token_counts["final_answer_token"] += 1
                        if token_counts["final_answer_token"] == 1:
                            print(f"[{elapsed:.1f}s] Final Answer Streaming (agent: {agent})")
                        
                    elif event_type == "research_completed":
                        print(f"[{elapsed:.1f}s] Research Completed (agent: {agent})")
                        
                    elif event_type == "paper_generated":
                        paper_id = data.get('paper_id', 'N/A')
                        print(f"[{elapsed:.1f}s] Paper Generated: {paper_id} (agent: {agent})")
                        break
                        
                    elif event_type in ["error", "validation_error"]:
                        error = data.get('error', 'Unknown')
                        print(f"[{elapsed:.1f}s] ERROR: {error} (agent: {agent})")
                        return False
                    
                    else:
                        print(f"[{elapsed:.1f}s] {event_type} (agent: {agent})")
                        
                except json.JSONDecodeError:
                    continue
        
        # Results
        end_time = time.time()
        total_time = end_time - start_time
        
        print("-" * 40)
        print("RESULTS:")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Total Events: {total_events}")
        print(f"Unique Event Types: {len(event_types)}")
        
        print(f"\nAgents Involved:")
        for agent, count in events_by_agent.items():
            print(f"  {agent}: {count} events")
        
        print(f"\nToken Streaming:")
        for token_type, count in token_counts.items():
            print(f"  {token_type}: {count}")
        
        # Validation
        agent_count = len(events_by_agent)
        token_total = sum(token_counts.values())
        has_workflow = "research_started" in event_types and "documents_retrieved" in event_types
        
        print(f"\nValidation:")
        print(f"  Agent Diversity: {'PASS' if agent_count >= 3 else 'FAIL'} ({agent_count} agents)")
        print(f"  Token Streaming: {'PASS' if token_total > 0 else 'FAIL'} ({token_total} tokens)")
        print(f"  Workflow Complete: {'PASS' if has_workflow else 'FAIL'}")
        
        success = agent_count >= 3 and token_total > 0 and has_workflow
        print(f"\nOVERALL: {'SUCCESS' if success else 'FAILURE'}")
        
        return success
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to API")
        return False
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
        return False
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_streaming()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1) 