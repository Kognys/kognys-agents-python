# tests/test_phase1.py
from unittest.mock import patch
from langgraph.graph import StateGraph, END
from kognys.graph.state import KognysState

# Import the actual node functions to build a temporary graph
from kognys.agents.input_validator import node as input_validator
from kognys.agents.retriever import node as retriever

# Plan B: Patch the function directly where it is imported and used.
# This is the most robust way to ensure the mock is applied.
@patch('kognys.agents.retriever.similarity_search')
# Bonus: Let's also mock the validator's LLM call to make the test fully offline and faster!
@patch('kognys.agents.input_validator._chain') 
def test_validation_and_retrieval_flow(mock_validator_chain, mock_similarity_search):
    """
    Tests the initial flow from input validation to document retrieval.
    Mocks all external calls (LLM and DB) to ensure the test is fast and isolated.
    """
    # Arrange: Build a temporary graph specifically for this test.
    workflow = StateGraph(KognysState)
    workflow.add_node("input_validator", input_validator)
    workflow.add_node("retriever", retriever)
    workflow.set_entry_point("input_validator")
    workflow.add_edge("input_validator", "retriever")
    workflow.add_edge("retriever", END)
    isolated_graph = workflow.compile()

    # Arrange: Configure the mocks to return predictable values.
    # For the validator
    mock_validator_chain.invoke.return_value.approved = True
    mock_validator_chain.invoke.return_value.revised_question = "What are the benefits of intermittent fasting?"
    
    # For the retriever
    mock_docs = [
        {"content": "Intermittent fasting can lead to weight loss.", "score": 0.9},
        {"content": "It may also improve metabolic health.", "score": 0.88}
    ]
    mock_similarity_search.return_value = mock_docs

    # Arrange: Define the initial state.
    initial_state = KognysState(question="Benefits of intermittent fasting?")
    
    # Act: Invoke the isolated graph.
    out = isolated_graph.invoke(initial_state)

    # Assert: Verify that the state was correctly updated.
    assert out['validated_question'] == "What are the benefits of intermittent fasting?"
    assert "documents" in out
    assert len(out['documents']) == 2
    assert out['documents'][0]['content'] == "Intermittent fasting can lead to weight loss."

    # Assert that our mock functions were called as expected.
    mock_validator_chain.invoke.assert_called_once()
    mock_similarity_search.assert_called_once()

    print("\n✅ Phase 1 Test Passed: Input validation and retrieval flow is working correctly.")
