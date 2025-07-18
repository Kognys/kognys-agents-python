# kognys/agents/retriever.py
from kognys.graph.state import KognysState
from kognys.services.openalex_client import search_works

def node(state: KognysState) -> dict:
    """
    Retrieves documents for research from the external OpenAlex API.
    """
    query = state.validated_question or state.question
    
    print(f"---RETRIEVER: Searching external OpenAlex for: '{query}'---")

    # Search the external, live academic database
    openalex_docs = search_works(query, k=5)
    
    if not openalex_docs:
        print("---RETRIEVER: No documents found from OpenAlex.---")
        return {"documents": [], "retrieval_status": "No documents found"}
    
    print(f"---RETRIEVER: Found {len(openalex_docs)} documents from OpenAlex.---")
    return {"documents": openalex_docs, "retrieval_status": "Documents found"}
