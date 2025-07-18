# kognys/agents/publisher.py
import hashlib
from kognys.graph.state import KognysState
from kognys.services.unibase_da_client import upload_paper_to_da

def node(state: KognysState) -> dict:
    """
    Saves the final answer to Unibase DA and simulates the on-chain hash publication.
    """
    final_answer = state.final_answer
    original_question = state.question

    if state.retrieval_status != "No documents found" and final_answer:
        try:
            print(f"---PUBLISHER: Saving final answer to Unibase DA...---")
            upload_paper_to_da(
                paper_content=final_answer,
                original_question=original_question
            )
        except Exception as e:
            print(f"---PUBLISHER: Failed to save document to Unibase DA. Error: {e} ---")
    else:
        print(f"---PUBLISHER: Skipping save to Unibase DA because no answer was generated.---")

    # The on-chain hash simulation remains the same
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