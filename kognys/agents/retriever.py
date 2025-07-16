# kognys/agents/retriever.py
from kognys.graph.state import KognysState
from kognys.services.membase_client import search_knowledge_base
from kognys.services.openalex_client import search_works

def node(state: KognysState) -> dict:
    """
    Retrieves documents from both the internal Membase KB and the external
    OpenAlex API, then combines the results.
    """
    query = state.validated_question or state.question
    
    print(f"---RETRIEVER: Searching internal Membase and external OpenAlex for: '{query}'---")

    # 1. Search your internal, curated knowledge base first
    membase_docs = search_knowledge_base(query, k=3)
    
    # 2. Search the external, live academic database
    openalex_docs = search_works(query, k=3)
    
    # 3. Combine the results
    # A simple combination for now. A more advanced version could de-duplicate results.
    combined_docs = membase_docs + openalex_docs
    
    if not combined_docs:
        print("---RETRIEVER: No documents found from any source.---")
        return {"documents": [], "retrieval_status": "No documents found"}
    
    print(f"---RETRIEVER: Found {len(combined_docs)} total documents.---")
    return {"documents": combined_docs, "retrieval_status": "Documents found"}
