# kognys/graph/builder.py
from langgraph.graph import StateGraph, END
from kognys.graph.state import KognysState
from kognys.agents.input_validator import node as input_validator
from kognys.agents.retriever import node as retriever

_graph = StateGraph(state_schema=KognysState)

# ── Nodes ──────────────────────────────────────────────────────────────
_graph.add_node("input_validator", input_validator)
_graph.add_node("retriever",       retriever)

# ── Entry & edges ──────────────────────────────────────────────────────
_graph.set_entry_point("input_validator")
_graph.add_edge("input_validator", "retriever")

# For now we finish after retrieval; later phases will move END further.
_graph.set_finish_point("retriever")

# Compile once and reuse
kognys_graph = _graph.compile()
