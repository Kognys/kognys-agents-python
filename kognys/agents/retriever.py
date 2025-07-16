# kognys/agents/retriever.py
from kognys.graph.state import KognysState
from kognys.services.membase_client import search_knowledge_base

def node(state: KognysState) -> dict:
    """
    Retrieves documents from the Membase API based on the validated question.
    """
    # Call the new search_knowledge_base function
    docs = search_knowledge_base(state.validated_question or state.question, k=5)
    
    if not docs:
        print("---RETRIEVER (Membase): No documents found.---")
        return {"documents": [], "retrieval_status": "No documents found"}
    
    print(f"---RETRIEVER (Membase): Found {len(docs)} documents.---")
    return {"documents": docs, "retrieval_status": "Documents found"}
