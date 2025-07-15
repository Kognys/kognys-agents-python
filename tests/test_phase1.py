# tests/test_phase1.py
from unittest.mock import patch
from langgraph.graph import StateGraph, END
from kognys.graph.state import KognysState

# Import the actual node functions to build a temporary graph
from kognys.agents.input_validator import node as input_validator
from kognys.agents.retriever import node as retriever

# The patch decorator targets the function where the external call is made.
@patch('kognys.services.vector_store.similarity_search')
def test_validation_and_retrieval_flow(mock_similarity_search):
    """
    Tests the initial flow from input validation to document retrieval.
    Mocks the vector store to ensure the test is fast and isolated.
    """
    # Arrange: Build a temporary graph specifically for this test.
    # This graph will stop after the retriever node.
    workflow = StateGraph(KognysState)
    workflow.add_node("input_validator", input_validator)
    workflow.add_node("retriever", retriever)
    workflow.set_entry_point("input_validator")
    workflow.add_edge("input_validator", "retriever")
    workflow.add_edge("retriever", END) # Explicitly end the graph here for this test.
    
    isolated_graph = workflow.compile()

    # Arrange: Configure the mock to return a predictable list of documents.
    mock_docs = [
        {"content": "Intermittent fasting can lead to weight loss.", "score": 0.9},
        {"content": "It may also improve metabolic health.", "score": 0.88}
    ]
    mock_similarity_search.return_value = mock_docs

    # Arrange: Define the initial state for the graph invocation.
    initial_state = KognysState(question="What are the proven benefits of intermittent fasting?")
    
    # Act: Invoke the isolated graph.
    out = isolated_graph.invoke(initial_state)

    # Assert: Verify that the state was correctly updated by the first two nodes.
    assert out['validated_question'] is not None
    assert "intermittent fasting" in out['validated_question']
    
    assert "documents" in out
    assert len(out['documents']) == 2
    assert out['documents'][0]['content'] == "Intermittent fasting can lead to weight loss."

    # Assert that the mock function was actually called.
    mock_similarity_search.assert_called_once()

    print("\n✅ Phase 1 Test Passed: Input validation and retrieval flow is working correctly.")
