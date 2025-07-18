from kognys.graph.state import KognysState
from kognys.services.openalex_client import search_works
from kognys.services.arxiv_client import search_arxiv
from kognys.services.semantic_scholar_client import search_semantic_scholar

def node(state: KognysState) -> dict:
    """
    Retrieves documents from OpenAlex, arXiv, and Semantic Scholar,
    then combines the results.
    """
    query = state.validated_question or state.question
    
    print(f"---RETRIEVER: Searching OpenAlex, arXiv, and Semantic Scholar for: '{query}'---")

    # Call all three APIs
    # NOTE: For a production system, you would run these in parallel (e.g., with threads)
    openalex_docs = search_works(query, k=2)
    arxiv_docs = search_arxiv(query, k=2)
    semantic_scholar_docs = search_semantic_scholar(query, k=2)
    
    # Combine the results
    combined_docs = openalex_docs + arxiv_docs + semantic_scholar_docs
    
    if not combined_docs:
        print("---RETRIEVER: No documents found from any source.---")
        return {"documents": [], "retrieval_status": "No documents found"}
    
    print(f"---RETRIEVER: Found {len(combined_docs)} total documents from all sources.---")
    return {"documents": combined_docs, "retrieval_status": "Documents found"}