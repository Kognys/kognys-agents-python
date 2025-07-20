# -*- coding: utf-8 -*-
# tests/test_logs_and_agent_names.py
import requests
import json
import time
import sys
import os

# Add parent directory to path to import from kognys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_logs_endpoint():
    """Test the new logs API endpoint."""
    print("🧪 Testing logs endpoint...")
    
    # Test the production API
    url = "https://kognys-agents-python-production.up.railway.app/logs"
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    print(f"📍 URL: {url}")
    print("="*50)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 Response Status: {response.status_code}")
        print("📄 Response Body:")
        
        if response.status_code == 200:
            try:
                logs = response.json()
                print(f"✅ Got {len(logs)} log events")
                
                # Check structure of first few logs
                for i, log in enumerate(logs[:3]):
                    print(f"\nLog {i+1}:")
                    print(f"  Event Type: {log.get('event_type', 'N/A')}")
                    print(f"  Agent: {log.get('agent', 'N/A')}")
                    print(f"  Timestamp: {log.get('timestamp', 'N/A')}")
                    print(f"  Data: {str(log.get('data', {}))[:100]}...")
                
                return True
                
            except json.JSONDecodeError:
                print("❌ Response is not valid JSON")
                print(response.text)
                return False
        else:
            print("❌ Request failed!")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 10 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed with exception: {e}")
        return False

def test_agent_names_in_streaming():
    """Test that agent names are included in streaming responses."""
    print("🧪 Testing agent names in streaming responses...")
    
    # Test a quick research request to see if agent names are included
    url = "https://kognys-agents-python-production.up.railway.app/papers/stream"
    
    payload = {
        "message": "What is AI?",
        "user_id": "test_agent_names"
    }
    
    headers = {
        "accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    
    print(f"📍 URL: {url}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    print("="*50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("📄 Streaming Response (first 10 events):")
            event_count = 0
            agent_names_found = set()
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                        event_count += 1
                        
                        event_type = event_data.get('event_type', 'unknown')
                        agent = event_data.get('data', {}).get('agent')
                        
                        if agent:
                            agent_names_found.add(agent)
                        
                        print(f"  Event {event_count}: {event_type} (agent: {agent})")
                        
                        # Stop after 10 events or completion
                        if event_count >= 10 or event_type in ['research_completed', 'research_failed']:
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            print(f"\n✅ Found {event_count} events")
            print(f"✅ Agent names found: {list(agent_names_found)}")
            print(f"✅ Agent names working: {'Yes' if agent_names_found else 'No'}")
            
            return len(agent_names_found) > 0
        else:
            print("❌ Streaming request failed!")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 30 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed with exception: {e}")
        return False

def test_health_check():
    """Test that the API is still working."""
    url = "https://kognys-agents-python-production.up.railway.app/"
    
    print("🏥 Testing API health...")
    try:
        response = requests.get(url, timeout=5)
        print(f"📊 Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ API is alive!")
            return True
        else:
            print("❌ API health check failed!")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Logs and Agent Names Tests...")
    print("=" * 60)
    
    # Test health first
    if not test_health_check():
        print("❌ Exiting: API health check failed")
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # Test logs endpoint
    logs_success = test_logs_endpoint()
    
    print("\n" + "="*60)
    
    # Test agent names in streaming
    agent_names_success = test_agent_names_in_streaming()
    
    print("\n" + "="*60)
    
    if logs_success and agent_names_success:
        print("🎉 All tests passed!")
        print("✅ Logs endpoint working")
        print("✅ Agent names in responses working")
    elif logs_success:
        print("⚠️ Logs endpoint working, but agent names may need verification")
    elif agent_names_success:
        print("⚠️ Agent names working, but logs endpoint may have issues")
    else:
        print("❌ Tests failed - check the error details above")
        sys.exit(1) 