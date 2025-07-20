#!/usr/bin/env python3
"""
Test script for AIP integration in Kognys
Run this with ENABLE_AIP_AGENTS=true to test the AIP features
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path to import kognys
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure AIP is enabled for this test
os.environ["ENABLE_AIP_AGENTS"] = "true"

from kognys.services.membase_client import (
    create_aip_agent,
    query_aip_agent,
    send_agent_message,
    route_request,
    buy_agent_auth,
    check_agent_auth
)

async def test_aip_integration():
    """Test the AIP integration features"""
    print("\n=== Testing AIP Integration ===\n")
    
    # Test 1: Create a test agent
    print("1. Creating test AIP agent...")
    result = create_aip_agent(
        agent_id="test-researcher",
        description="A test research agent",
        conversation_id="test-conv"
    )
    if result:
        print("   ✅ Agent created successfully")
    else:
        print("   ❌ Failed to create agent")
        return
    
    # Test 2: Query the agent
    print("\n2. Querying the AIP agent...")
    query_result = query_aip_agent(
        agent_id="test-researcher",
        query="What are the key considerations when researching quantum computing applications?",
        conversation_id="test-conv"
    )
    if query_result.get("response"):
        print(f"   ✅ Received response: {query_result['response'][:200]}...")
    else:
        print("   ❌ No response received")
    
    # Test 3: Test routing
    print("\n3. Testing intelligent routing...")
    routes = route_request(
        "I need to analyze the latest machine learning papers on transformers",
        top_k=3
    )
    if routes:
        print(f"   ✅ Found {len(routes)} routes")
    else:
        print("   ❌ No routes found")
    
    # Test 4: Create another agent for messaging
    print("\n4. Creating second agent for inter-agent communication...")
    result2 = create_aip_agent(
        agent_id="test-analyzer", 
        description="A test analysis agent",
        conversation_id="test-conv-2"
    )
    
    if result2:
        # Test 5: Buy authorization
        print("\n5. Setting up agent authorization...")
        auth_success = buy_agent_auth("test-analyzer", "test-researcher")
        if auth_success:
            print("   ✅ Authorization granted")
            
            # Check authorization
            has_auth = check_agent_auth("test-analyzer", "test-researcher")
            print(f"   Authorization check: {'✅ Valid' if has_auth else '❌ Invalid'}")
        
        # Test 6: Inter-agent messaging
        print("\n6. Testing inter-agent messaging...")
        msg_result = send_agent_message(
            from_agent_id="test-researcher",
            to_agent_id="test-analyzer",
            action="request",
            message="Please analyze the quantum computing research landscape"
        )
        if msg_result and not msg_result.get("error"):
            print("   ✅ Message sent successfully")
        else:
            print(f"   ❌ Message failed: {msg_result.get('error', 'Unknown error')}")
    
    print("\n=== AIP Integration Test Complete ===\n")

def main():
    """Run the test with the current graph setup"""
    print("\n=== Testing AIP Integration with Kognys Graph ===\n")
    
    # Import after setting environment
    try:
        from kognys.graph.builder import kognys_graph
        from kognys.graph.state import KognysState
    except Exception as e:
        print(f"Note: Could not import graph components: {e}")
        print("Running standalone AIP tests only...\n")
        asyncio.run(test_aip_integration())
        return
    
    # Create a test state
    test_state = KognysState(
        question="What are the latest advances in quantum error correction?",
        paper_id="test-aip-001"
    )
    
    print("Running research with AIP agents enabled...")
    print("(Set ENABLE_AIP_AGENTS=true in your .env file)\n")
    
    # Run the async test
    asyncio.run(test_aip_integration())
    
    # Optionally run a full graph execution
    # result = kognys_graph.invoke(test_state)
    # print("\nResearch completed with AIP enhancement!")

if __name__ == "__main__":
    main()