# tests/test_phase1.py
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

def test_validation_round_trip():
    state = KognysState(question="What are the proven benefits of intermittent fasting?")
    out = kognys_graph.invoke(state)
    assert out.validated_question
