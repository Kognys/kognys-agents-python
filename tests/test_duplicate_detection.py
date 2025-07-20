#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Duplicate and Infinite Loop Detection Test

This test will:
1. Monitor for exact duplicate events
2. Detect potential infinite loops
3. Show detailed event timing and patterns
4. Provide comprehensive analysis
"""

import requests
import json
import time
import sys
from collections import defaultdict, Counter
from datetime import datetime

def test_duplicates_and_loops():
    """Comprehensive test for duplicates and infinite loops."""
    
    url = "https://kognys-agents-python-production.up.railway.app/papers/stream"
    payload = {
        "message": "What is artificial intelligence?",
        "user_id": "duplicate_test_user"
    }
    
    print("COMPREHENSIVE DUPLICATE & LOOP DETECTION TEST")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Question: {payload['message']}")
    print("=" * 60)
    print()
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    try:
        print("Connecting and monitoring for duplicates/loops...")
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=120)
        
        if response.status_code != 200:
            print(f"ERROR: HTTP {response.status_code}")
            print(response.text)
            return False
        
        print("Connected! Monitoring events...")
        print("-" * 50)
        
        # Comprehensive tracking
        all_events = []
        event_hashes = set()
        duplicate_events = []
        event_type_counts = Counter()
        same_event_sequence = []
        last_event_type = None
        same_type_streak = 0
        
        start_time = time.time()
        max_events = 200  # Safety limit to prevent true infinite loops
        
        for line_num, line in enumerate(response.iter_lines(decode_unicode=True)):
            if line.startswith('data: '):
                try:
                    event_data = json.loads(line[6:])
                    
                    # Basic event info
                    event_type = event_data.get('event_type', 'unknown')
                    data = event_data.get('data', {})
                    timestamp = event_data.get('timestamp', time.time())
                    agent = data.get('agent', 'unknown')
                    elapsed = time.time() - start_time
                    
                    # Create unique event hash (for exact duplicate detection)
                    event_hash = f"{event_type}_{timestamp}_{json.dumps(data, sort_keys=True)}"
                    
                    # Store comprehensive event info
                    event_info = {
                        'line_num': line_num + 1,
                        'event_type': event_type,
                        'agent': agent,
                        'timestamp': timestamp,
                        'elapsed': elapsed,
                        'data': data,
                        'hash': event_hash,
                        'raw_data': event_data
                    }
                    all_events.append(event_info)
                    
                    # Check for exact duplicates
                    if event_hash in event_hashes:
                        duplicate_events.append(event_info)
                        print(f"[{elapsed:.1f}s] ⚠️  DUPLICATE #{len(duplicate_events)}: {event_type} (agent: {agent})")
                    else:
                        event_hashes.add(event_hash)
                        print(f"[{elapsed:.1f}s] ✅ UNIQUE: {event_type} (agent: {agent})")
                    
                    # Track event type counts and sequences
                    event_type_counts[event_type] += 1
                    
                    # Check for same event type streaks (potential loops)
                    if event_type == last_event_type:
                        same_type_streak += 1
                        if same_type_streak >= 5:  # 5+ same events in a row
                            print(f"[{elapsed:.1f}s] 🔄 POTENTIAL LOOP: {event_type} repeated {same_type_streak + 1} times")
                    else:
                        if same_type_streak > 0:
                            same_event_sequence.append((last_event_type, same_type_streak + 1))
                        same_type_streak = 0
                        last_event_type = event_type
                    
                    # Safety check for infinite loops
                    if len(all_events) >= max_events:
                        print(f"\n🛑 SAFETY STOP: Reached {max_events} events limit!")
                        print("This suggests a potential infinite loop!")
                        break
                    
                    # Check for completion
                    if event_type in ["research_completed", "paper_generated", "error", "validation_error"]:
                        print(f"\n✅ Research workflow completed with: {event_type}")
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"JSON Error on line {line_num + 1}: {e}")
                    continue
        
        # Comprehensive Analysis
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("COMPREHENSIVE ANALYSIS")
        print("=" * 60)
        
        print(f"📊 BASIC STATS:")
        print(f"   Total Events: {len(all_events)}")
        print(f"   Unique Events: {len(event_hashes)}")
        print(f"   Duplicate Events: {len(duplicate_events)}")
        print(f"   Total Time: {total_time:.2f} seconds")
        print(f"   Events/Second: {len(all_events)/total_time:.2f}")
        
        print(f"\n🔄 DUPLICATE ANALYSIS:")
        if duplicate_events:
            print(f"   ❌ DUPLICATES FOUND: {len(duplicate_events)} duplicate events!")
            
            # Group duplicates by type
            dup_by_type = defaultdict(list)
            for dup in duplicate_events:
                dup_by_type[dup['event_type']].append(dup)
            
            for event_type, dups in dup_by_type.items():
                print(f"   - {event_type}: {len(dups)} duplicates")
                for dup in dups[:3]:  # Show first 3 examples
                    original_idx = next(i for i, e in enumerate(all_events) if e['hash'] == dup['hash'] and e != dup)
                    print(f"     * Line {dup['line_num']} duplicates line {all_events[original_idx]['line_num']}")
        else:
            print("   ✅ NO DUPLICATES: All events were unique!")
        
        print(f"\n🔄 LOOP DETECTION:")
        if same_event_sequence:
            print("   Event type repetition patterns found:")
            for event_type, count in same_event_sequence:
                if count >= 3:
                    print(f"   - {event_type}: repeated {count} times consecutively")
        
        # Check for suspicious patterns
        suspicious_patterns = []
        for event_type, count in event_type_counts.items():
            if count > 10 and event_type not in ["draft_answer_token", "final_answer_token", "criticism_token"]:
                suspicious_patterns.append((event_type, count))
        
        if suspicious_patterns:
            print("   ⚠️  SUSPICIOUS PATTERNS:")
            for event_type, count in suspicious_patterns:
                print(f"   - {event_type}: {count} occurrences (unusually high)")
        
        print(f"\n📋 EVENT TYPE BREAKDOWN:")
        for event_type, count in event_type_counts.most_common():
            percentage = (count / len(all_events)) * 100
            print(f"   {event_type}: {count} ({percentage:.1f}%)")
        
        print(f"\n👥 AGENT BREAKDOWN:")
        agent_counts = Counter(event['agent'] for event in all_events)
        for agent, count in agent_counts.most_common():
            percentage = (count / len(all_events)) * 100
            print(f"   {agent}: {count} ({percentage:.1f}%)")
        
        # Show timing analysis
        print(f"\n⏱️  TIMING ANALYSIS:")
        if len(all_events) > 1:
            time_gaps = []
            for i in range(1, len(all_events)):
                gap = all_events[i]['elapsed'] - all_events[i-1]['elapsed']
                time_gaps.append(gap)
            
            avg_gap = sum(time_gaps) / len(time_gaps)
            max_gap = max(time_gaps)
            min_gap = min(time_gaps)
            
            print(f"   Average gap between events: {avg_gap:.3f}s")
            print(f"   Max gap: {max_gap:.3f}s")
            print(f"   Min gap: {min_gap:.3f}s")
            
            # Check for rapid-fire events (potential duplicates)
            rapid_events = sum(1 for gap in time_gaps if gap < 0.001)  # Less than 1ms apart
            if rapid_events > 0:
                print(f"   ⚠️  {rapid_events} events occurred <1ms apart (potential duplicates)")
        
        # Final verdict
        print(f"\n🎯 FINAL VERDICT:")
        has_duplicates = len(duplicate_events) > 0
        has_loops = len(suspicious_patterns) > 0 or len(all_events) >= max_events
        has_rapid_events = len(all_events) > 1 and sum(1 for i in range(1, len(all_events)) 
                                                       if all_events[i]['elapsed'] - all_events[i-1]['elapsed'] < 0.001) > 0
        
        if has_duplicates:
            print("   ❌ DUPLICATE ISSUE: Found duplicate events")
        if has_loops:
            print("   ❌ LOOP ISSUE: Detected potential infinite loops")
        if has_rapid_events:
            print("   ⚠️  TIMING ISSUE: Events occurring too rapidly")
        
        if not has_duplicates and not has_loops and not has_rapid_events:
            print("   ✅ ALL GOOD: No duplicates or loops detected")
        
        # Export detailed log for analysis
        if duplicate_events or has_loops:
            log_file = f"duplicate_analysis_{int(time.time())}.json"
            with open(log_file, 'w') as f:
                json.dump({
                    'all_events': all_events,
                    'duplicate_events': duplicate_events,
                    'event_type_counts': dict(event_type_counts),
                    'agent_counts': dict(agent_counts),
                    'total_time': total_time,
                    'analysis': {
                        'has_duplicates': has_duplicates,
                        'has_loops': has_loops,
                        'has_rapid_events': has_rapid_events
                    }
                }, f, indent=2)
            print(f"\n📄 Detailed analysis saved to: {log_file}")
        
        return not (has_duplicates or has_loops)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to API")
        return False
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
        return False
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_duplicates_and_loops()
    print(f"\nTest Result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1) 