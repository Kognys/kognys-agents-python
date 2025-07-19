# kognys/agents/publisher.py
import hashlib
import uuid
from kognys.graph.state import KognysState
from kognys.services.unibase_da_client import upload_paper_to_da
from kognys.services.blockchain_client import publish_hash_on_chain

def node(state: KognysState) -> dict:
    """
    Generates a unique ID for the paper, saves the final answer to Unibase DA,
    and publishes a hash of the result on-chain.
    """
    final_answer = state.final_answer
    original_question = state.question
    
    storage_receipt_id = None

    # Only save to DA if the retrieval was successful and we have a real answer.
    if state.retrieval_status != "No documents found" and final_answer:
        try:
            # --- START OF FIX ---
            # Generate the unique, content-addressable ID here
            paper_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, original_question + final_answer))
            # --- END OF FIX ---

            print(f"---PUBLISHER: Saving final answer to Unibase DA with ID: {paper_id} ---")
            
            response_data = upload_paper_to_da(
                paper_id=paper_id,
                paper_content=final_answer,
                original_question=original_question
            )
            if response_data and response_data.get("success"):
                storage_receipt_id = response_data.get("id")

        except Exception as e:
            print(f"---PUBLISHER: Failed to save document to Unibase DA. Error: {e} ---")
    else:
        print(f"---PUBLISHER: Skipping save to Unibase DA because no answer was generated.---")

    # Now, publish the hash of the content to the blockchain
    if final_answer:
        answer_hash = hashlib.sha256(final_answer.encode()).hexdigest()
        
        print("\n" + "="*50)
        print("📰 Kognys On-Chain Publisher Agent 📰")
        print("="*50)
        print(f"DA Storage ID: {storage_receipt_id}")
        print(f"Content Hash: {answer_hash}")
        
        tx_hash = publish_hash_on_chain(answer_hash)
        if tx_hash:
            print(f"✅ On-chain verification successful. Transaction Hash: {tx_hash}")
        else:
            print("❌ On-chain verification failed.")
        print("="*50 + "\n")
    
    return {}