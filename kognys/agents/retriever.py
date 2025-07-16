# kognys/agents/retriever.py
from kognys.graph.state import KognysState
# Change the import to use the new OpenAlex client
from kognys.services.openalex_client import search_works

def node(state: KognysState) -> dict:
    """
    Retrieves documents from the OpenAlex API based on the validated question.
    """
    # Call the new search_works function
    docs = search_works(state.validated_question or state.question, k=5)
    
    if not docs:
        print("---RETRIEVER (OpenAlex): No documents found.---")
        return {"documents": [], "retrieval_status": "No documents found"}
    
    print(f"---RETRIEVER (OpenAlex): Found {len(docs)} documents.---")
    return {"documents": docs, "retrieval_status": "Documents found"}
