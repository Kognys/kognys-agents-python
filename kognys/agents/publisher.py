# kognys/agents/publisher.py
import hashlib
from kognys.graph.state import KognysState
from kognys.services.unibase_da_client import upload_paper_to_da

def node(state: KognysState) -> dict:
    """
    Saves the final answer to Unibase DA and provides the real storage ID
    as a verifiable proof.
    """
    final_answer = state.final_answer
    original_question = state.question
    
    storage_receipt_id = None

    if state.retrieval_status != "No documents found" and final_answer:
        try:
            print(f"---PUBLISHER: Saving final answer to Unibase DA...---")
            # --- START OF CHANGE ---
            # Capture the response from the upload function
            response_data = upload_paper_to_da(
                paper_content=final_answer,
                original_question=original_question
            )
            # Extract the real document ID as the proof
            if response_data and response_data.get("success"):
                storage_receipt_id = response_data.get("id")
            # --- END OF CHANGE ---
        except Exception as e:
            print(f"---PUBLISHER: Failed to save document to Unibase DA. Error: {e} ---")
    else:
        print(f"---PUBLISHER: Skipping save to Unibase DA because no answer was generated.---")

    # --- START OF CHANGE: Remove simulation and use real proof ---
    if storage_receipt_id:
        print("\n" + "="*50)
        print("📰 Kognys On-Chain Verifier 📰")
        print("="*50)
        print(f"✅ Research successfully stored on Unibase DA.")
        print(f"Verifiable Storage ID: {storage_receipt_id}")
        print("="*50 + "\n")
    # --- END OF CHANGE ---
    
    return {}