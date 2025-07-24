# kognys/agents/publisher.py
import hashlib
import uuid
import os
import threading
from kognys.graph.state import KognysState
from kognys.services.membase_client import store_final_answer_in_kb, store_transcript_in_memory, finish_task
from kognys.services.unibase_da_client import archive_research_packet
# --- REMOVED blockchain_client IMPORT ---
from kognys.utils.transcript import append_entry

def node(state: KognysState) -> dict:
    final_answer = state.final_answer
    original_question = state.question
    
    # Initialize verifiable data dictionary
    verifiable_data = {
        "task_id": None,
        "finish_task_txn_hash": None,
        "da_archival_id": None,
        "da_storage_receipt": None
    }

    if state.retrieval_status != "No documents found" and final_answer:
        paper_id = state.paper_id
        task_id = state.task_id 
        agent_id = os.getenv("MEMBASE_ID")
        verifiable_data["task_id"] = task_id

        # 1. Store in Membase KB
        store_final_answer_in_kb(paper_id, final_answer, original_question, state.user_id)
        
        # 2. Store transcript in background
        transcript_thread = threading.Thread(
            target=store_transcript_in_memory,
            args=(paper_id, state.transcript)
        )
        transcript_thread.start()
        
        # 3. Archive to Unibase DA and capture the receipt
        da_response = archive_research_packet(
            paper_id=paper_id,
            paper_content=final_answer,
            original_question=original_question,
            transcript=state.transcript,
            source_documents=state.documents,
            user_id=state.user_id
        )
        verifiable_data["da_archival_id"] = da_response.get("id")
        verifiable_data["da_storage_receipt"] = da_response 

        # 4. Finish the on-chain task and capture the transaction hash
        if task_id and agent_id:
            finish_response = finish_task(task_id=task_id, agent_id=agent_id)
            verifiable_data["finish_task_txn_hash"] = finish_response.get("transaction_hash")
        
        print("\n" + "="*60)
        print("🔍 KOGNYS VERIFIABILITY SUMMARY 🔍")
        print("="*60)
        print(f"  - On-Chain Task ID: {task_id}")
        print(f"  - Finish Task TXN Hash: {verifiable_data['finish_task_txn_hash']}")
        print(f"  - DA Archival ID: {verifiable_data['da_archival_id']}")
        print("="*60 + "\n")

    else:
        print("---PUBLISHER: Skipping storage because no answer was generated.---")

    # Add the captured verifiable data to the state update
    return { 
        "final_answer": final_answer,
        "verifiable_data": verifiable_data,
        "transcript": append_entry(state.transcript, agent="Publisher", action="Stored, archived, and finished task") 
    }
