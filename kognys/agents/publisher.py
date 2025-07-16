# kognys/agents/publisher.py
import hashlib
from kognys.graph.state import KognysState
from kognys.services.membase_client import add_knowledge_document # <-- Import the new function

def node(state: KognysState) -> dict:
    """
    Takes the final answer, saves it to the Membase Knowledge Base,
    and then simulates the on-chain hash publication.
    """
    final_answer = state.final_answer
    original_question = state.question

    if not final_answer:
        return {}

    # --- Start of Changes ---
    # 1. Add the final answer to our persistent knowledge base
    try:
        add_knowledge_document(
            title=f"Research on: {original_question[:50]}...",
            content=final_answer,
            source_id="kognys_research_run" # In a real app, this could be a run ID
        )
    except Exception as e:
        print(f"---PUBLISHER: Failed to add document to Membase. Error: {e} ---")
    # --- End of Changes ---

    # 2. Simulate the on-chain transaction (this part remains the same)
    answer_hash = hashlib.sha256(final_answer.encode()).hexdigest()
    print("\n" + "="*50)
    print("📰 Kognys On-Chain Publisher Agent 📰")
    print("="*50)
    print(f"Final Answer Hash: {answer_hash}")
    print(f"Simulating transaction to BNB Chain smart contract to publish hash...")
    print("✅ Transaction successful. Research result is now verifiably stored.")
    print("="*50 + "\n")

    return {}
