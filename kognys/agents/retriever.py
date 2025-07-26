# kognys/agents/retriever.py
from kognys.graph.state import KognysState
from kognys.services.openalex_client import search_works
from kognys.services.arxiv_client import search_arxiv
from kognys.services.semantic_scholar_client import search_semantic_scholar
from kognys.utils.transcript import append_entry

def node(state: KognysState) -> dict:
    """
    Retrieves documents using refined queries for OpenAlex, arXiv, and Semantic Scholar.
    """

    refined_queries = state.refined_queries
    if not refined_queries:
        raise ValueError("Refined queries are missing from the state.")
    
    print("---RETRIEVER: Searching with refined queries---")
    
    # Use the specific, optimized query for each service
    openalex_query = refined_queries.get("openalex")
    arxiv_query = refined_queries.get("arxiv")
    semantic_scholar_query = refined_queries.get("semantic_scholar")

    print(f"  - [OpenAlex] Query: '{openalex_query}'")
    openalex_docs = search_works(openalex_query, k=5)
    for doc in openalex_docs:
        doc['source'] = 'OpenAlex'

    print(f"  - [arXiv] Query: '{arxiv_query}'")
    arxiv_docs = search_arxiv(arxiv_query, k=5)
    for doc in arxiv_docs:
        doc['source'] = 'arXiv'

    print(f"  - [Semantic Scholar] Query: '{semantic_scholar_query}'")
    semantic_scholar_docs = search_semantic_scholar(semantic_scholar_query, k=5)
    for doc in semantic_scholar_docs:
        doc['source'] = 'Semantic Scholar'
    
    combined_docs = openalex_docs + arxiv_docs + semantic_scholar_docs
    
    if not combined_docs:
        print("---RETRIEVER: No documents found from any source.---")
        update_dict = {"documents": [], "retrieval_status": "No documents found"}
    else:
        print(f"---RETRIEVER: Found {len(combined_docs)} total documents from all sources.---")
        
        print("---RETRIEVER: Sources Found ---")
        for doc in combined_docs:
            title = doc.get('title', 'No Title Available')
            source = doc.get('source', 'Unknown Source')
            print(f"  - [{source}] \"{title}\"")
            
        update_dict = {"documents": combined_docs, "retrieval_status": "Documents found"}
    
    update_dict["transcript"] = append_entry(
        state.transcript,
        agent="Retriever",
        action="Retrieved documents with refined queries",
        details=f"{len(combined_docs)} docs found"
    )
    
    return update_dict