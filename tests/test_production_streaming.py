#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production Streaming Test - Test the current Kognys streaming flow with agent names.

This test connects to the production API and validates:
1. Complete streaming workflow (question -> documents -> draft -> completion)
2. Agent names in all responses 
3. Token-level streaming for real-time updates
4. Event deduplication (no 4x duplicates)
5. Proper error handling
"""

import requests
import json
import time
import sys

def test_production_streaming():
    """Test the complete streaming flow on production."""
    
    # Production configuration
    url = "https://kognys-agents-python-production.up.railway.app/papers/stream"
    payload = {
        "message": "What are the latest breakthroughs in quantum computing and their potential applications?",
        "user_id": "streaming_test_user"
    }
    
    print("KOGNYS PRODUCTION STREAMING TEST")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Question: {payload['message']}")
    print(f"User ID: {payload['user_id']}")
    print("=" * 60)
    print()
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    try:
        print("Connecting to production streaming endpoint...")
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=180)
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print("Connected successfully!")
        print("Live streaming events with agent tracking:\n")
        
        # Tracking variables
        events_by_type = {}
        events_by_agent = {}
        token_counts = {"draft_answer_token": 0, "criticism_token": 0, "final_answer_token": 0}
        duplicate_check = set()
        start_time = time.time()
        total_events = 0
        
        draft_content = ""
        criticism_content = ""
        final_content = ""
        
        print("Event Flow:")
        print("-" * 50)
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])
                    total_events += 1
                    
                    event_type = event_data.get('event_type', 'unknown')
                    data = event_data.get('data', {})
                    timestamp = event_data.get('timestamp', time.time())
                    agent = data.get('agent', 'unknown')
                    
                    # Track event types and agents
                    events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
                    events_by_agent[agent] = events_by_agent.get(agent, 0) + 1
                    
                    # Check for duplicates
                    event_id = f"{event_type}_{timestamp}"
                    if event_id in duplicate_check:
                        print(f"⚠️  DUPLICATE detected: {event_type} (agent: {agent})")
                    else:
                        duplicate_check.add(event_id)
                    
                    elapsed = time.time() - start_time
                    
                    # Handle different event types
                    if event_type == "research_started":
                        print(f"[{elapsed:.1f}s] 🚀 Research Started (agent: {agent})")
                        print(f"         Status: {data.get('status', 'N/A')}")
                        
                    elif event_type == "question_validated":
                        print(f"[{elapsed:.1f}s] ✅ Question Validated (agent: {agent})")
                        validated = data.get('validated_question', 'N/A')
                        print(f"         Validated: {validated[:100]}...")
                        
                    elif event_type == "documents_retrieved":
                        print(f"[{elapsed:.1f}s] 📚 Documents Retrieved (agent: {agent})")
                        doc_count = data.get('document_count', 0)
                        print(f"         Found: {doc_count} documents")
                        
                    elif event_type == "draft_answer_token":
                        token_counts["draft_answer_token"] += 1
                        token = data.get('token', '')
                        draft_content += token
                        if token_counts["draft_answer_token"] == 1:
                            print(f"[{elapsed:.1f}s] ✍️  Draft Streaming Started (agent: {agent})")
                        # Show progress every 10 tokens
                        if token_counts["draft_answer_token"] % 10 == 0:
                            print(f"         Token #{token_counts['draft_answer_token']}: '{token}'")
                        
                    elif event_type == "draft_generated":
                        print(f"[{elapsed:.1f}s] ✍️  Draft Generated (agent: {agent})")
                        draft_length = data.get('draft_length', 0)
                        print(f"         Length: {draft_length} chars, Tokens received: {token_counts['draft_answer_token']}")
                        
                    elif event_type == "criticism_token":
                        token_counts["criticism_token"] += 1
                        token = data.get('token', '')
                        criticism_content += token
                        if token_counts["criticism_token"] == 1:
                            print(f"[{elapsed:.1f}s] 🤔 Criticism Streaming Started (agent: {agent})")
                        
                    elif event_type == "criticisms_received":
                        print(f"[{elapsed:.1f}s] 🤔 Criticisms Received (agent: {agent})")
                        crit_count = data.get('criticism_count', 0)
                        print(f"         Count: {crit_count}, Tokens received: {token_counts['criticism_token']}")
                        
                    elif event_type == "orchestrator_decision":
                        print(f"[{elapsed:.1f}s] ⚙️  Orchestrator Decision (agent: {agent})")
                        decision = data.get('decision', 'unknown')
                        print(f"         Decision: {decision}")
                        
                    elif event_type == "final_answer_token":
                        token_counts["final_answer_token"] += 1
                        token = data.get('token', '')
                        final_content += token
                        if token_counts["final_answer_token"] == 1:
                            print(f"[{elapsed:.1f}s] 🎯 Final Answer Streaming Started (agent: {agent})")
                        
                    elif event_type == "research_completed":
                        print(f"[{elapsed:.1f}s] 🎉 Research Completed (agent: {agent})")
                        final_answer = data.get('final_answer', '')
                        print(f"         Final answer length: {len(final_answer)} chars")
                        print(f"         Tokens received: {token_counts['final_answer_token']}")
                        
                    elif event_type == "paper_generated":
                        print(f"[{elapsed:.1f}s] 📄 Paper Generated (agent: {agent})")
                        paper_id = data.get('paper_id', 'N/A')
                        content = data.get('paper_content', '')
                        print(f"         Paper ID: {paper_id}")
                        print(f"         Content length: {len(content)} chars")
                        break  # End of stream
                        
                    elif event_type in ["validation_error", "error"]:
                        print(f"[{elapsed:.1f}s] ❌ Error (agent: {agent})")
                        error = data.get('error', 'Unknown error')
                        print(f"         Error: {error}")
                        return False
                        
                    else:
                        print(f"[{elapsed:.1f}s] 📨 {event_type.title()} (agent: {agent})")
                        status = data.get('status', 'N/A')
                        print(f"         Status: {status}")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    continue
        
        # Results summary
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 STREAMING TEST RESULTS")
        print("=" * 60)
        
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"📨 Total Events: {total_events}")
        print(f"🔄 Unique Events: {len(duplicate_check)}")
        
        if total_events != len(duplicate_check):
            print(f"⚠️  DUPLICATES DETECTED: {total_events - len(duplicate_check)} duplicate events")
        else:
            print("✅ NO DUPLICATES: All events were unique")
        
        print(f"\n🎯 TOKEN STREAMING:")
        for token_type, count in token_counts.items():
            print(f"   {token_type}: {count} tokens")
        
        print(f"\n👥 AGENTS INVOLVED:")
        for agent, count in events_by_agent.items():
            print(f"   {agent}: {count} events")
        
        print(f"\n📋 EVENT TYPES:")
        for event_type, count in events_by_type.items():
            print(f"   {event_type}: {count} occurrences")
        
        # Validation checks
        print(f"\n🔍 VALIDATION CHECKS:")
        
        # Check agent diversity
        agent_diversity = len(events_by_agent) >= 3
        print(f"   Agent Diversity (≥3): {'✅' if agent_diversity else '❌'} ({len(events_by_agent)} agents)")
        
        # Check token streaming
        token_streaming = sum(token_counts.values()) > 0
        print(f"   Token Streaming: {'✅' if token_streaming else '❌'} ({sum(token_counts.values())} tokens)")
        
        # Check workflow completion
        required_events = ["research_started", "question_validated", "documents_retrieved"]
        workflow_complete = all(event in events_by_type for event in required_events)
        print(f"   Workflow Complete: {'✅' if workflow_complete else '❌'}")
        
        # Check no duplicates
        no_duplicates = total_events == len(duplicate_check)
        print(f"   No Duplicates: {'✅' if no_duplicates else '❌'}")
        
        # Overall result
        all_checks_passed = agent_diversity and token_streaming and workflow_complete and no_duplicates
        
        print(f"\n🎯 OVERALL RESULT: {'🎉 SUCCESS' if all_checks_passed else '❌ ISSUES DETECTED'}")
        
        if not all_checks_passed:
            print("\n💡 Issues to investigate:")
            if not agent_diversity:
                print("   - Not enough agent diversity in responses")
            if not token_streaming:
                print("   - Token streaming not working")
            if not workflow_complete:
                print("   - Research workflow incomplete")
            if not no_duplicates:
                print("   - Event duplication detected")
        
        return all_checks_passed
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Cannot connect to production API")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: Request took too long")
        return False
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run the production streaming test."""
    success = test_production_streaming()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 