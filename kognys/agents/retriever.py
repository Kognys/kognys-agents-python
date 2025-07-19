# kognys/agents/retriever.py
from kognys.graph.state import KognysState
from kognys.services.openalex_client import search_works
from kognys.services.arxiv_client import search_arxiv
from kognys.services.semantic_scholar_client import search_semantic_scholar
from kognys.utils.transcript import append_entry

def node(state: KognysState) -> dict:
    """
    Retrieves documents from OpenAlex, arXiv, and Semantic Scholar.
    """
    query = state.validated_question or state.question
    
    print(f"---RETRIEVER: Searching OpenAlex, arXiv, and Semantic Scholar for: '{query}'---")

    openalex_docs = search_works(query, k=5)
    arxiv_docs = search_arxiv(query, k=5)
    semantic_scholar_docs = search_semantic_scholar(query, k=5)
    
    combined_docs = openalex_docs + arxiv_docs + semantic_scholar_docs
    
    if not combined_docs:
        print("---RETRIEVER: No documents found from any source.---")
        update_dict = {"documents": [], "retrieval_status": "No documents found"}
    else:
        print(f"---RETRIEVER: Found {len(combined_docs)} total documents from all sources.---")
        
        print("---RETRIEVER: Sources Found ---")
        for doc in combined_docs:
            title = doc.get('title', 'No Title Available')
            url = doc.get('url', 'No URL Available')
            print(f"  - \"{title}\" ({url})")
            
        update_dict = {"documents": combined_docs, "retrieval_status": "Documents found"}
    
    update_dict["transcript"] = append_entry(
        state.transcript,
        agent="Retriever",
        action="Retrieved documents",
        details=f"{len(combined_docs)} docs"
    )
    
    return update_dict
