import os, pytest
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

@pytest.mark.skipif("MONGODB_URI" not in os.environ, reason="requires Mongo URI")
def test_retriever_populates_docs():
    state = KognysState(question="What are the health impacts of red light therapy?")
    out = kognys_graph.invoke(state)
    assert out.documents, "RetrieverAgent should attach documents"
