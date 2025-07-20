# kognys/agents/publisher.py
import hashlib
import uuid
import os
from kognys.graph.state import KognysState
from kognys.services.membase_client import store_final_answer_in_kb, store_transcript_in_memory
from kognys.services.unibase_da_client import archive_research_packet
from kognys.services.blockchain_client import publish_hash_on_chain
from kognys.utils.transcript import append_entry

def node(state: KognysState) -> dict:
    final_answer = state.final_answer
    original_question = state.question
    
    if state.retrieval_status != "No documents found" and final_answer:
        paper_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, original_question + final_answer))
        
        # 1. Store active memory in Membase
        store_final_answer_in_kb(paper_id, final_answer, original_question)
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

        # 3. Publish the hash of the final answer to the blockchain
        answer_hash = hashlib.sha256(final_answer.encode()).hexdigest()
        
        print("\n" + "="*50)
        print("📰 Kognys On-Chain Publisher Agent 📰")
        print("="*50)
        print(f"DA Archival ID: {storage_receipt_id}")
        print(f"Content Hash: {answer_hash}")
        
        tx_hash = publish_hash_on_chain(answer_hash)
        if tx_hash:
            print(f"✅ On-chain verification successful.")
            print(f"   - Transaction Hash: {tx_hash}")
        else:
            print("❌ On-chain verification failed.")
        print("="*50)

        # --- THIS NEW SECTION ADDS THE HELPFUL SUMMARY ---
        print("\n" + "="*60)
        print("🔍 KOGNYS VERIFIABILITY SUMMARY 🔍")
        print("="*60)
        print("Use the following identifiers to find your data on the explorers:")
        print(f"\n- Agent ID:")
        print(f"  {os.getenv('MEMBASE_ID')}")
        print(f"\n- Paper ID (for Membase 'memory' or DA 'file' search):")
        print(f"  {paper_id}")
        print(f"\n- BNB Testnet Transaction Hash:")
        print(f"  {tx_hash}")
        print("="*60 + "\n")

    else:
        print("---PUBLISHER: Skipping storage because no answer was generated.---")

    return { "transcript": append_entry(state.transcript, agent="Publisher", action="Stored and archived research") }
