# kognys/agents/retriever.py
from kognys.graph.state import KognysState
from kognys.services.openalex_client import search_works
from kognys.services.arxiv_client import search_arxiv
from kognys.services.semantic_scholar_client import search_semantic_scholar
from kognys.utils.transcript import append_entry
from kognys.config import ENABLE_AIP_AGENTS, AIP_USE_ROUTING, AIP_RETRIEVER_ID
from kognys.services.membase_client import query_aip_agent, route_request

def node(state: KognysState) -> dict:
    """
    Retrieves documents from OpenAlex, arXiv, and Semantic Scholar.
    Optionally uses AIP agents for enhanced retrieval if enabled.
    """
    query = state.validated_question or state.question
    
    print(f"---RETRIEVER: Searching for: '{query}'---")
    
    # Check if we should use AIP routing for smarter search
    if ENABLE_AIP_AGENTS and AIP_USE_ROUTING:
        routes = route_request(query, top_k=3)
        if routes:
            print(f"---RETRIEVER: AIP routing suggests {len(routes)} approaches---")
    
    # Traditional search from academic sources
    openalex_docs = search_works(query, k=5)
    arxiv_docs = search_arxiv(query, k=5)
    semantic_scholar_docs = search_semantic_scholar(query, k=5)
    
    combined_docs = openalex_docs + arxiv_docs + semantic_scholar_docs
    
    # If AIP is enabled, query the AIP retriever for additional insights
    if ENABLE_AIP_AGENTS:
        try:
            aip_prompt = f"""Based on the research question: '{query}'
            
Please suggest:
1. Key search terms and concepts to explore
2. Related topics that might be relevant
3. Specific types of papers or sources to look for
            
Current sources found: {len(combined_docs)} documents from OpenAlex, arXiv, and Semantic Scholar."""
            
            aip_response = query_aip_agent(
                agent_id=AIP_RETRIEVER_ID,
                query=aip_prompt,
                conversation_id=f"research-{state.paper_id}"
            )
            
            if aip_response.get("response"):
                print(f"---RETRIEVER: AIP agent provided additional search guidance---")
                # Could potentially use this to refine search or add metadata
                
        except Exception as e:
            print(f"---RETRIEVER: AIP enhancement failed: {e}, continuing with traditional search---")
    
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
