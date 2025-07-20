#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time Server Logs Viewer

Watch server logs in real-time while testing streaming.
Run this in a separate terminal while running your streaming tests.
"""

import requests
import json
import time
from datetime import datetime

def watch_logs():
    """Stream real-time logs from the server."""
    
    url = "https://kognys-agents-python-production.up.railway.app/logs/stream"
    
    print("KOGNYS REAL-TIME LOGS VIEWER")
    print("=" * 50)
    print(f"Streaming from: {url}")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    print()
    
    headers = {
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache"
    }
    
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=300)
        
        if response.status_code != 200:
            print(f"ERROR: HTTP {response.status_code}")
            print(response.text)
            return
        
        print("Connected! Watching logs...")
        print("-" * 40)
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event = json.loads(line[6:])
                    
                    event_type = event.get('event_type', 'unknown')
                    data = event.get('data', {})
                    timestamp = event.get('timestamp', time.time())
                    agent = event.get('agent', 'unknown')
                    
                    # Format timestamp
                    dt = datetime.fromtimestamp(timestamp)
                    time_str = dt.strftime("%H:%M:%S")
                    
                    # Handle different event types
                    if event_type == "heartbeat":
                        print(f"[{time_str}] HEARTBEAT - System alive")
                        continue
                        
                    elif event_type == "research_started":
                        question = data.get('question', 'N/A')
                        print(f"[{time_str}] NEW RESEARCH ({agent})")
                        print(f"          Question: {question[:80]}...")
                        
                    elif event_type == "question_validated":
                        validated = data.get('validated_question', 'N/A')
                        print(f"[{time_str}] VALIDATED ({agent})")
                        print(f"          Refined: {validated[:80]}...")
                        
                    elif event_type == "documents_retrieved":
                        count = data.get('document_count', 0)
                        print(f"[{time_str}] DOCUMENTS ({agent}): {count} found")
                        
                    elif event_type.endswith("_token"):
                        token = data.get('token', '')
                        token_preview = token[:30].replace('\n', ' ')
                        print(f"[{time_str}] TOKEN ({agent}): '{token_preview}{'...' if len(token) > 30 else ''}'")
                        
                    elif event_type == "draft_generated":
                        length = data.get('draft_length', 0)
                        print(f"[{time_str}] DRAFT DONE ({agent}): {length} chars")
                        
                    elif event_type == "criticisms_received":
                        count = data.get('criticism_count', 0)
                        print(f"[{time_str}] CRITICISMS ({agent}): {count} received")
                        
                    elif event_type == "orchestrator_decision":
                        decision = data.get('decision', 'unknown')
                        print(f"[{time_str}] DECISION ({agent}): {decision}")
                        
                    elif event_type == "research_completed":
                        print(f"[{time_str}] COMPLETED ({agent}): Research finished")
                        
                    elif event_type in ["error", "validation_error"]:
                        error = data.get('error', 'Unknown')
                        print(f"[{time_str}] ERROR ({agent}): {error}")
                        
                    else:
                        status = data.get('status', 'N/A')
                        print(f"[{time_str}] {event_type.upper()} ({agent}): {status}")
                    
                except json.JSONDecodeError:
                    continue
                except KeyboardInterrupt:
                    break
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to logs stream")
    except requests.exceptions.Timeout:
        print("ERROR: Connection timed out")
    except KeyboardInterrupt:
        print("\nStopped watching logs")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    watch_logs() 