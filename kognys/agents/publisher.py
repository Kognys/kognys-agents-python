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
    final_answer = state.get("final_answer")
    if not final_answer or state.get("retrieval_status") == "No documents found":
        print("---PUBLISHER: Skipping storage, no answer generated.---")
        return {"final_answer": final_answer}

    paper_id = state.get("paper_id")
    task_id = state.get("task_id")
    agent_id = os.getenv("MEMBASE_ID")

    # Store verifiable data as we go
    verifiable_data = {
        "task_id": task_id,
        "membase_kb_storage": None,
        "finish_task_txn_hash": None,
        "da_storage_receipt": None
    }

    # 1. Store in Membase KB
    kb_response = store_final_answer_in_kb(paper_id, final_answer, state.get("question"), state.get("user_id"))
    verifiable_data["membase_kb_storage"] = kb_response

    # 2. Archive to Unibase DA
    da_response = archive_research_packet(
        paper_id=paper_id,
        paper_content=final_answer,
        original_question=state.get("question"),
        transcript=state.get("transcript", []),
        source_documents=state.get("documents", []),
        user_id=state.get("user_id")
    )
    verifiable_data["da_storage_receipt"] = da_response

    # 3. Finish the on-chain task
    if task_id and agent_id:
        finish_response = finish_task(task_id=task_id, agent_id=agent_id)
        verifiable_data["finish_task_txn_hash"] = finish_response.get("transaction_hash")

    # 4. Store transcript in background
    threading.Thread(
        target=store_transcript_in_memory,
        args=(paper_id, state.get("transcript", []))
    ).start()

    print("\n" + "="*60)
    print("🔍 KOGNYS VERIFIABILITY SUMMARY 🔍")
    print("="*60)
    print(f"  - On-Chain Task ID: {task_id}")
    print(f"  - Finish Task TXN Hash: {verifiable_data['finish_task_txn_hash']}")
    print(f"  - DA Archival ID: {da_response.get('id')}")
    print("="*60 + "\n")

    return { 
        "final_answer": final_answer,
        "verifiable_data": verifiable_data,
        "transcript": append_entry(state.get("transcript", []), agent="Publisher", action="Stored, archived, and finished task") 
    }
