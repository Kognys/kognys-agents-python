# kognys/graph/builder.py
from langgraph.graph import StateGraph, END
from kognys.graph.state import KognysState

# Import all agents, including the new summarizer
from kognys.agents.input_validator import node as input_validator
from kognys.agents.retriever import node as retriever
from kognys.agents.synthesizer import node as synthesizer
from kognys.agents.challenger import node as challenger
from kognys.agents.checklist import node as checklist
from kognys.agents.orchestrator import node as orchestrator
from kognys.agents.publisher import node as publisher
from kognys.agents.reviser import node as reviser
from kognys.agents.summarizer import node as summarizer

_graph = StateGraph(KognysState)

# --- Add all nodes to the graph ---
_graph.add_node("input_validator", input_validator)
_graph.add_node("retriever", retriever)
_graph.add_node("synthesizer", synthesizer)
_graph.add_node("challenger", challenger)
_graph.add_node("checklist", checklist)
_graph.add_node("orchestrator", orchestrator)
_graph.add_node("publisher", publisher)
_graph.add_node("reviser", reviser)
_graph.add_node("summarizer", summarizer)

# --- Define the graph's edges ---
_graph.set_entry_point("input_validator")
_graph.add_edge("input_validator", "retriever")
_graph.add_edge("synthesizer", "challenger")
_graph.add_edge("challenger", "checklist")
_graph.add_edge("orchestrator", "publisher")
_graph.add_edge("publisher", END)
_graph.add_edge("summarizer", "synthesizer")
_graph.add_edge("reviser", "retriever")

# --- Conditional Edge After Retrieval ---
def route_after_retrieval(state: KognysState) -> str:
    if state.retrieval_status == "No documents found":
        return "orchestrator"
    else:
        return "synthesizer"

_graph.add_conditional_edges(
    "retriever",
    route_after_retrieval,
    {
        "orchestrator": "orchestrator",
        "synthesizer": "synthesizer"
    }
)

# --- Define the smarter conditional routing ---
def route_after_checklist(state: KognysState) -> str:
    if state.is_sufficient:
        return "orchestrator"
    
    if any("documents" in c.lower() or "sources" in c.lower() for c in state.criticisms):
        return "reviser"
    else:
        # Loop to our new summarizer first.
        print("---DECISION: Answer needs refinement. Summarizing context...")
        return "summarizer"

_graph.add_conditional_edges(
    "checklist",
    route_after_checklist,
    {
        "orchestrator": "orchestrator",
        "reviser": "reviser",
        "summarizer": "summarizer"
    }
)

# Compile the final graph
kognys_graph = _graph.compile()
