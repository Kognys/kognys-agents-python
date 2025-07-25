from langgraph.graph import StateGraph, END
from kognys.graph.state import KognysState
from kognys.config import ENABLE_AIP_AGENTS
from kognys.utils.aip_init import initialize_aip_agents

# Import the core agents
from kognys.agents.input_validator import node as input_validator
from kognys.agents.query_refiner import node as query_refiner  # <-- IMPORT NEW AGENT
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
    # --- UPDATE THIS LOGIC ---
    if state.final_answer:
        return "publisher"
    # Check for the signal to research again (now comes from refined_queries being cleared)
    elif state.get("validated_question") and not state.get("refined_queries"): 
        return "query_refiner" # Route back to the refiner, not retriever
    else: # This is the signal to revise
        return "synthesizer"

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
