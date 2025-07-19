# kognys/agents/publisher.py
import hashlib
from kognys.graph.state import KognysState

def node(state: KognysState) -> dict:
    final_answer = state.final_answer

    if final_answer:
        answer_hash = hashlib.sha256(final_answer.encode()).hexdigest()
        print("\n" + "="*50)
        print("📰 Kognys On-Chain Verifier 📰")
        print("="*50)
        print(f"✅ Research complete. Final Answer Hash: {answer_hash}")
        print("="*50 + "\n")
    
    return {}
