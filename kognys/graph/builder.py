# kognys/graph/builder.py
from langgraph.graph import StateGraph, END
from kognys.graph.state import KognysState
from kognys.config import ENABLE_AIP_AGENTS
from kognys.utils.aip_init import initialize_aip_agents

# Import the core agents
from kognys.agents.input_validator import node as input_validator
from kognys.agents.query_refiner import node as query_refiner
from kognys.agents.retriever import node as retriever
from kognys.agents.synthesizer import node as synthesizer
from kognys.agents.challenger import node as challenger
from kognys.agents.orchestrator import node as orchestrator
from kognys.agents.publisher import node as publisher

# Initialize AIP agents if enabled
if ENABLE_AIP_AGENTS:
    initialize_aip_agents()

_graph = StateGraph(KognysState)

# --- Add Nodes ---
_graph.add_node("input_validator", input_validator)
_graph.add_node("query_refiner", query_refiner)
_graph.add_node("retriever", retriever)
_graph.add_node("synthesizer", synthesizer)
_graph.add_node("challenger", challenger)
_graph.add_node("orchestrator", orchestrator)
_graph.add_node("publisher", publisher)

# --- Define Edges ---
_graph.set_entry_point("input_validator")
_graph.add_edge("input_validator", "query_refiner")
_graph.add_edge("query_refiner", "retriever")
_graph.add_edge("synthesizer", "challenger")
_graph.add_edge("challenger", "orchestrator")
_graph.add_edge("publisher", END)

# --- Conditional Routing Logic ---
def route_after_retrieval(state: KognysState) -> str:
    if state.retrieval_status == "No documents found":
        return "orchestrator"
    return "synthesizer"

def route_after_orchestrator(state: KognysState) -> str:
    """
    Determines the next step after the orchestrator makes a decision.
    """
    if state.final_answer:
        return "publisher"
    
    # --- FIX: Use attribute access instead of .get() ---
    if state.validated_question and not state.refined_queries:
        print("---ROUTING: Orchestrator decided to research again. Routing to Query Refiner.---")
        return "query_refiner"
    else:
        print("---ROUTING: Orchestrator decided to revise. Routing to Synthesizer.---")
        return "synthesizer"
    # ---------------------------------------------------

_graph.add_conditional_edges("retriever", route_after_retrieval, {
    "orchestrator": "orchestrator",
    "synthesizer": "synthesizer"
})
_graph.add_conditional_edges("orchestrator", route_after_orchestrator, {
    "publisher": "publisher",
    "query_refiner": "query_refiner",
    "synthesizer": "synthesizer"
})

kognys_graph = _graph.compile()
