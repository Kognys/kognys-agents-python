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
    # Use direct attribute access instead of .get()
    final_answer = state.final_answer
    
    if not final_answer or state.retrieval_status == "No documents found":
        print("---PUBLISHER: Skipping storage, no answer generated.---")
        return {"final_answer": final_answer}

    # Use direct attribute access for all state fields
    paper_id = state.paper_id
    task_id = state.task_id
    agent_id = os.getenv("MEMBASE_ID")
    original_question = state.question
    user_id = state.user_id
    transcript = state.transcript
    documents = state.documents

    # Initialize a dictionary to hold all verifiable data
    verifiable_data = {
        "task_id": task_id,
        "membase_kb_storage_receipt": None,
        "finish_task_txn_hash": None,
        "da_storage_receipt": None
    }

    # 1. Store in Membase KB and capture the response
    kb_response = store_final_answer_in_kb(paper_id, final_answer, original_question, user_id)
    verifiable_data["membase_kb_storage_receipt"] = kb_response

    # 2. Archive to Unibase DA and capture the full receipt
    da_response = archive_research_packet(
        paper_id=paper_id,
        paper_content=final_answer,
        original_question=original_question,
        transcript=transcript,
        source_documents=documents,
        user_id=user_id
    )
    verifiable_data["da_storage_receipt"] = da_response

    # 3. Finish the on-chain task and capture the transaction hash
    if task_id and agent_id:
        finish_response = finish_task(task_id=task_id, agent_id=agent_id)
        verifiable_data["finish_task_txn_hash"] = finish_response.get("transaction_hash")

    # 4. Store transcript in a background thread
    threading.Thread(
        target=store_transcript_in_memory,
        args=(paper_id, transcript)
    ).start()

    print("\n" + "="*60)
    print("🔍 KOGNYS VERIFIABILITY SUMMARY 🔍")
    print("="*60)
    print(f"  - On-Chain Task ID: {task_id}")
    print(f"  - Finish Task TXN Hash: {verifiable_data['finish_task_txn_hash']}")
    print(f"  - Membase KB Storage Success: {kb_response.get('success')}")
    print(f"  - DA Archival ID: {da_response.get('id')}")
    print("="*60 + "\n")

    return { 
        "final_answer": final_answer,
        "verifiable_data": verifiable_data,
        "transcript": append_entry(transcript, agent="Publisher", action="Stored, archived, and finished task") 
    }
