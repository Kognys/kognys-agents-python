# run_live.py
from dotenv import load_dotenv
load_dotenv() 

import os
import uuid
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState
from kognys.services.membase_client import register_agent_if_not_exists

def main():
    """
    Registers the agent identity and then runs a live, end-to-end test
    of the Kognys research agent.
    """
    # 1. Register the agent identity before starting the workflow
    print("\n--- AGENT REGISTRATION ---")
    agent_id = os.getenv("MEMBASE_ID", "kognys-research-agent-test-001")
    is_registered = register_agent_if_not_exists(
        agent_id=agent_id,
        name="Kognys Research Agent",
        description="An autonomous agent that performs research using a Chain-of-Debate framework."
    )

    if not is_registered:
        print("\nCould not register agent identity. Aborting research task.")
        return
    print("--------------------------\n")

    # 2. Define the research question for this live run
    research_question = "What are the most promising applications of generative AI in software development?"

    print("="*60)
    print(f"🚀 STARTING KOGNYS RESEARCH AGENT 🚀")
    print(f"Research Question: {research_question}")
    print("="*60 + "\n")

    # 3. Set up the configuration for the graph run
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = KognysState(question=research_question)

    # 4. Use .stream() to see the output from each node as it runs
    for i, chunk in enumerate(kognys_graph.stream(initial_state, config=config)):
        if not chunk:
            continue
        
        node_name, state_update = list(chunk.items())[0]
        
        if state_update is None:
            continue

        print(f"\n--- ➡️ STEP {i+1}: EXECUTING NODE '{node_name}' ---")
        
        # Log the specific data that was changed in this step
        if 'validated_question' in state_update:
            print(f"  - Validated Question: \"{state_update['validated_question']}\"")
        if 'documents' in state_update:
            print(f"  - Retrieved {len(state_update['documents'])} documents.")
        if 'draft_answer' in state_update:
            print(f"  - Draft Answer: \"{state_update['draft_answer']}\"")
        if 'criticisms' in state_update and state_update['criticisms']:
            print(f"  - Criticisms Found: {state_update['criticisms']}")
        if 'is_sufficient' in state_update:
            print(f"  - Sufficiency Check: {state_update['is_sufficient']}")
        if 'final_answer' in state_update:
            print("\n" + "="*60)
            print("✅ FINAL ANSWER")
            print("="*60)
            print(state_update['final_answer'])

if __name__ == "__main__":
    main()
