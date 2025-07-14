from kognys.graph.state import KognysState
from kognys.services.vector_store import similarity_search

def node(state: KognysState, **_) -> KognysState:
    docs = similarity_search(state.validated_question or state.question, k=6)
    if not docs:
        raise ValueError("RetrieverAgent found no matching documents.")
    state.documents = docs
    return state
