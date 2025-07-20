# kognys/agents/publisher.py
import hashlib
import uuid
import os
from kognys.graph.state import KognysState
from kognys.services.membase_client import store_final_answer_in_kb, store_transcript_in_memory, finish_task
from kognys.services.unibase_da_client import archive_research_packet
# --- REMOVED blockchain_client IMPORT ---
from kognys.utils.transcript import append_entry

def node(state: KognysState) -> dict:
    final_answer = state.final_answer
    original_question = state.question
    
    if state.retrieval_status != "No documents found" and final_answer:
        paper_id = state.paper_id
        task_id = state.task_id 
        agent_id = os.getenv("MEMBASE_ID")

        # 1. Store active memory in Membase
        store_final_answer_in_kb(paper_id, final_answer, original_question, state.user_id)
        store_transcript_in_memory(paper_id, state.transcript)
        
        # 2. Archive the full packet to the DA Layer
        da_response = archive_research_packet(
            paper_id=paper_id,
            paper_content=final_answer,
            original_question=original_question,
            transcript=state.transcript,
            source_documents=state.documents
        )
        storage_receipt_id = da_response.get("id")

        # --- STEP 3 IS NOW FINISHING THE TASK ---
        # 3. Finish the on-chain task (this is our on-chain verification step)
        if task_id and agent_id:
            finish_task(task_id=task_id, agent_id=agent_id)

        # --- SIMPLIFIED VERIFIABILITY SUMMARY ---
        print("\n" + "="*60)
        print("🔍 KOGNYS VERIFIABILITY SUMMARY 🔍")
        print("="*60)
        print("The research task is complete. The following records were created:")
        print(f"\n- Agent ID:")
        print(f"  {agent_id}")
        print(f"\n- On-Chain Task ID / Paper ID:")
        print(f"  {task_id}")
        print(f"\n- DA Archival ID:")
        print(f"  {storage_receipt_id}")
        print("\nVerification is handled automatically by the Membase & Unibase DA services.")
        print("="*60 + "\n")

    else:
        print("---PUBLISHER: Skipping storage because no answer was generated.---")

    return { "transcript": append_entry(state.transcript, agent="Publisher", action="Stored, archived, and finished task") }
