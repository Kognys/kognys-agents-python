# kognys/graph/builder.py
from langgraph.graph import StateGraph, END
from kognys.graph.state import KognysState

# Import the core agents
from kognys.agents.input_validator import node as input_validator
from kognys.agents.retriever import node as retriever
from kognys.agents.synthesizer import node as synthesizer
from kognys.agents.challenger import node as challenger
from kognys.agents.orchestrator import node as orchestrator
from kognys.agents.publisher import node as publisher

_graph = StateGraph(KognysState)

# --- Add Nodes ---
_graph.add_node("input_validator", input_validator)
_graph.add_node("retriever", retriever)
_graph.add_node("synthesizer", synthesizer)
_graph.add_node("challenger", challenger)
_graph.add_node("orchestrator", orchestrator)
_graph.add_node("publisher", publisher)

# --- Define Edges ---
_graph.set_entry_point("input_validator")
_graph.add_edge("input_validator", "retriever")
_graph.add_edge("synthesizer", "challenger")
_graph.add_edge("challenger", "orchestrator")
_graph.add_edge("publisher", END)

# --- Conditional Routing Logic ---
def route_after_retrieval(state: KognysState) -> str:
    if state.retrieval_status == "No documents found":
        return "orchestrator"
    return "synthesizer"

def route_after_orchestrator(state: KognysState) -> str:
    if state.final_answer:
        return "publisher"
    elif not state.documents: # This is the signal to research again
        return "retriever"
    else: # This is the signal to revise
        return "synthesizer"

_graph.add_conditional_edges("retriever", route_after_retrieval, {
    "orchestrator": "orchestrator",
    "synthesizer": "synthesizer"
})
_graph.add_conditional_edges("orchestrator", route_after_orchestrator, {
    "publisher": "publisher",
    "retriever": "retriever",
    "synthesizer": "synthesizer"
})

kognys_graph = _graph.compile()

