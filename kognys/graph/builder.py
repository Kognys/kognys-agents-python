# kognys/graph/builder.py
from langgraph import StateGraph, END
from kognys.graph.state import KognysState
from kognys.agents.input_validator import node as input_validator
from kognys.agents.retriever import node as retriever     # ←- new

_graph = StateGraph(schema=KognysState)

# ── Nodes ──────────────────────────────────────────────────────────────
_graph.add_node("input_validator", input_validator)
_graph.add_node("retriever",       retriever)

# ── Entry & edges ──────────────────────────────────────────────────────
_graph.set_entry_point("input_validator")
_graph.add_edge("input_validator", "retriever")

# For now we finish after retrieval; later phases will move END further.
_graph.set_finish_point(END)

# Compile once and reuse
kognys_graph = _graph.compile()
