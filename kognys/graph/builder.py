# kognys/graph/builder.py
from langgraph.graph import StateGraph, END
from kognys.graph.state import KognysState

# Import all your agent nodes
from kognys.agents.input_validator import node as input_validator
from kognys.agents.retriever import node as retriever
from kognys.agents.synthesizer import node as synthesizer
from kognys.agents.challenger import node as challenger
from kognys.agents.checklist import node as checklist
from kognys.agents.orchestrator import node as orchestrator

_graph = StateGraph(KognysState)

# ── Nodes ────────────────────────────────────────────────────────────────
_graph.add_node("input_validator", input_validator)
_graph.add_node("retriever", retriever)
_graph.add_node("synthesizer", synthesizer)
_graph.add_node("challenger", challenger)
_graph.add_node("checklist", checklist)
_graph.add_node("orchestrator", orchestrator)

# ── Entry & Edges ────────────────────────────────────────────────────────
_graph.set_entry_point("input_validator")
_graph.add_edge("input_validator", "retriever")
_graph.add_edge("retriever", "synthesizer")
# After synthesizing, we always challenge the answer
_graph.add_edge("synthesizer", "challenger") 
# After challenging, we run our quality check
_graph.add_edge("challenger", "checklist")
# The orchestrator is the last step before ending
_graph.add_edge("orchestrator", END)


# ── Conditional Edge (The Smarter Debate Loop) ──────────────────────────
def route_after_checklist(state: KognysState) -> str:
    """
    Determines the next step after the checklist agent has run.
    """
    if state.is_sufficient:
        # If the answer is sufficient, proceed to the final orchestrator
        return "orchestrator"
    else:
        # Otherwise, loop back to the synthesizer to refine the answer
        return "synthesizer"

_graph.add_conditional_edges(
    "checklist",
    route_after_checklist,
    {
        "orchestrator": "orchestrator",
        "synthesizer": "synthesizer"
    }
)

# Compile once and reuse
kognys_graph = _graph.compile()
