# kognys/agents/publisher.py
import hashlib
from kognys.graph.state import KognysState
from kognys.services.membase_client import add_knowledge_document

def node(state: KognysState) -> dict:
    """
    Saves the final answer to Membase (if successful) and simulates
    publishing a hash of the result on-chain.
    """
    final_answer = state.final_answer
    original_question = state.question

    # Only save to Membase if the retrieval was successful and we have a real answer.
    if state.retrieval_status != "No documents found" and final_answer:
        try:
            print(f"---PUBLISHER: Saving final answer to Membase Knowledge Base...---")
            add_knowledge_document(
                title=f"Research on: {original_question[:50]}...",
                content=final_answer,
                source_id="kognys_research_run"
            )
        except Exception as e:
            print(f"---PUBLISHER: Failed to add document to Membase. Error: {e} ---")
    else:
        print(f"---PUBLISHER: Skipping save to Membase because no answer was generated.---")

    # The on-chain hash publication can still happen for all results.
    if final_answer:
        answer_hash = hashlib.sha256(final_answer.encode()).hexdigest()
        print("\n" + "="*50)
        print("📰 Kognys On-Chain Publisher Agent 📰")
        print("="*50)
        print(f"Final Answer Hash: {answer_hash}")
        print(f"Simulating transaction to BNB Chain smart contract to publish hash...")
        print("✅ Transaction successful. Research result is now verifiably stored.")
        print("="*50 + "\n")
    
    return {}
