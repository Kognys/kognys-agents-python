# kognys/agents/retriever.py

from kognys.graph.state import KognysState
from kognys.services.vector_store import similarity_search

def node(state: KognysState) -> dict: # Change return type hint to dict
    """
    Retrieves documents relevant to the validated question.
    """
    docs = similarity_search(state.validated_question or state.question, k=6)
    
    if not docs:
        raise ValueError("RetrieverAgent found no matching documents.")
    
    # Return a dictionary with ONLY the state field that needs to be updated.
    # LangGraph will merge this into the main state.
    return {"documents": docs}
