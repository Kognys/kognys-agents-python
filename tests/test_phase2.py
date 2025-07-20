# tests/test_phase2.py
from unittest.mock import patch, MagicMock
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

# We need to patch the LLM used in both the synthesizer and challenger
@patch('kognys.agents.challenger._chain')
@patch('kognys.agents.synthesizer._chain')
def test_debate_loop_and_termination(mock_synthesizer_chain, mock_challenger_chain):
    """
    Tests the full debate loop, ensuring it continues when criticized
    and terminates when the answer is approved.
    """
    # Arrange: Define the sequence of mock LLM responses
    
    # 1. Synthesizer's first attempt (a weak answer)
    mock_synthesizer_chain.invoke.side_effect = [
        MagicMock(content="Fasting is good for you."), # First call
        MagicMock(content="Intermittent fasting improves metabolic health and can lead to weight loss.") # Second call
    ]

    # 2. Challenger's responses
    mock_challenger_chain.invoke.side_effect = [
        MagicMock(content="* The answer is too generic. It lacks specific benefits mentioned in the documents."), # First call finds a flaw
        MagicMock(content="") # Second call finds no flaws
    ]

    # Initial state after retrieval
    initial_state = {
        "question": "What are the proven benefits of intermittent fasting?",
        "validated_question": "What are the proven benefits of intermittent fasting?",
        "documents": [
            {"content": "Intermittent fasting can lead to weight loss.", "score": 0.9},
            {"content": "It may also improve metabolic health.", "score": 0.88}
        ]
    }

    # Act: Invoke the full graph
    import asyncio
    final_state = asyncio.run(kognys_graph.ainvoke(initial_state))

    # Assert
    # Check that the synthesizer was called twice
    assert mock_synthesizer_chain.invoke.call_count == 2
    
    # Check that the challenger was called twice
    assert mock_challenger_chain.invoke.call_count == 2
    
    # Check the final answer is the improved one
    assert "metabolic health" in final_state["draft_answer"]
    
    # Check that the final state has no criticisms, which caused the loop to end
    assert not final_state["criticisms"]

    print("\n✅ Phase 2 Test Passed: The debate loop successfully refined the answer and terminated.")
