from langgraph.graph import StateGraph, END
from kognys.graph.state import KognysState

# Import all your agent nodes
from kognys.agents.input_validator import node as input_validator
from kognys.agents.retriever import node as retriever
from kognys.agents.synthesizer import node as synthesizer
from kognys.agents.challenger import node as challenger

_graph = StateGraph(KognysState)

# ── Nodes ────────────────────────────────────────────────────────────────
_graph.add_node("input_validator", input_validator)
_graph.add_node("retriever", retriever)
_graph.add_node("synthesizer", synthesizer)
_graph.add_node("challenger", challenger)

# ── Entry & Edges ────────────────────────────────────────────────────────
_graph.set_entry_point("input_validator")
_graph.add_edge("input_validator", "retriever")
_graph.add_edge("retriever", "synthesizer")
_graph.add_edge("synthesizer", "challenger")

# ── Conditional Edge (The Debate Loop) ───────────────────────────────────
def should_continue_debate(state: KognysState) -> str:
    """Determines whether to continue the debate or finalize the answer."""
    if not state.criticisms:
        print("---DEBATE COMPLETE: NO CRITICISMS---")
        # This is a key in the map below, which correctly routes to END
        return "end_debate" 
    else:
        print("---DEBATE CONTINUES: RE-SYNTHESIZE---")
        # This is the key that was missing. It should be "continue_debate".
        return "continue_debate"

_graph.add_conditional_edges(
    "challenger",
    should_continue_debate,
    {
        "end_debate": END,
        "continue_debate": "synthesizer" # This now correctly maps the key to the destination node
    }
)

# Compile once and reuse
kognys_graph = _graph.compile()
