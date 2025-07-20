# kognys/utils/aip_init.py
"""
AIP Agent initialization utilities for Kognys
"""
from kognys.config import (
    ENABLE_AIP_AGENTS, 
    AIP_RETRIEVER_ID, 
    AIP_SYNTHESIZER_ID, 
    AIP_CHALLENGER_ID,
    AIP_ORCHESTRATOR_ID
)
from kognys.services.membase_client import (
    create_aip_agent,
    buy_agent_auth,
    register_agent_if_not_exists
)

def initialize_aip_agents():
    """
    Initialize AIP agents for enhanced research capabilities.
    Creates the agents and sets up authorization between them.
    """
    if not ENABLE_AIP_AGENTS:
        print("---AIP: AIP agents are disabled---")
        return False
    
    print("\n--- 🚀 Initializing AIP Agents ---")
    
    # Define the agents to create
    agents = [
        {
            "id": AIP_RETRIEVER_ID,
            "description": "Specialized in finding and evaluating academic sources"
        },
        {
            "id": AIP_SYNTHESIZER_ID,
            "description": "Expert at synthesizing research findings into coherent answers"
        },
        {
            "id": AIP_CHALLENGER_ID,
            "description": "Critical analyst providing constructive feedback on research drafts"
        },
        {
            "id": AIP_ORCHESTRATOR_ID,
            "description": "Strategic decision maker for research workflow optimization"
        }
    ]
    
    created_agents = []
    
    # Create each AIP agent
    for agent in agents:
        try:
            # First register the agent on blockchain if needed
            register_success = register_agent_if_not_exists(agent["id"])
            if not register_success:
                print(f"  - ⚠️  Could not register {agent['id']} on blockchain")
            
            # Create the AIP agent
            result = create_aip_agent(
                agent_id=agent["id"],
                description=agent["description"],
                conversation_id=f"{agent['id']}-research"
            )
            
            if result:
                created_agents.append(agent["id"])
                print(f"  - ✅ Created: {agent['id']}")
            else:
                print(f"  - ❌ Failed to create: {agent['id']}")
                
        except Exception as e:
            print(f"  - ❌ Error creating {agent['id']}: {e}")
    
    # Set up authorization between agents for collaboration
    if len(created_agents) >= 2:
        print("\n--- 🔐 Setting up agent authorizations ---")
        
        # Allow synthesizer to receive info from retriever
        auth_pairs = [
            (AIP_SYNTHESIZER_ID, AIP_RETRIEVER_ID),
            (AIP_CHALLENGER_ID, AIP_SYNTHESIZER_ID),
            (AIP_ORCHESTRATOR_ID, AIP_CHALLENGER_ID),
            (AIP_ORCHESTRATOR_ID, AIP_SYNTHESIZER_ID),
        ]
        
        for buyer, seller in auth_pairs:
            if buyer in created_agents and seller in created_agents:
                try:
                    success = buy_agent_auth(buyer, seller)
                    if success:
                        print(f"  - ✅ {buyer} authorized to access {seller}")
                except Exception as e:
                    print(f"  - ⚠️  Auth failed: {buyer} → {seller}: {e}")
    
    print(f"\n--- AIP initialization complete: {len(created_agents)}/{len(agents)} agents ready ---")
    return len(created_agents) > 0

def cleanup_aip_agents():
    """
    Clean up AIP agents (if needed in the future).
    Currently a placeholder for potential cleanup logic.
    """
    if not ENABLE_AIP_AGENTS:
        return
    
    print("---AIP: Cleanup not implemented (agents persist for reuse)---")