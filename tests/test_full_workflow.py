# tests/test_full_workflow.py
from unittest.mock import patch, MagicMock
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

# We need to patch all 5 agents that make LLM calls, plus the retriever's DB call.
@patch('kognys.agents.orchestrator._chain')
@patch('kognys.agents.checklist._chain')
@patch('kognys.agents.challenger._chain')
@patch('kognys.agents.synthesizer._chain')
@patch('kognys.agents.retriever.similarity_search')
@patch('kognys.agents.input_validator._chain')
def test_full_research_workflow(
    mock_validator_chain,
    mock_retriever_search,
    mock_synthesizer_chain,
    mock_challenger_chain,
    mock_checklist_chain,
    mock_orchestrator_chain,
):
    """
    Tests the full agent workflow from input to final answer,
    including one full debate-and-refine loop.
    """
    # 1. ARRANGE: Configure all mock responses for the entire workflow
    
    mock_validator_chain.invoke.return_value.approved = True
    mock_validator_chain.invoke.return_value.revised_question = "What are the health benefits of a ketogenic diet?"

    mock_retriever_search.return_value = [
        {"content": "Keto can lead to weight loss.", "score": 0.9},
        {"content": "It may improve cognitive function.", "score": 0.8}
    ]

    # Synthesizer will be called twice
    mock_synthesizer_chain.invoke.side_effect = [
        MagicMock(content="The keto diet is a diet."),
        MagicMock(content="The ketogenic diet can result in weight loss and may enhance cognitive function.")
    ]
    
    # CORRECTED: Challenger will also be called twice
    mock_challenger_chain.invoke.side_effect = [
        MagicMock(content="* The answer is vague and misses key details from the documents."), # First call
        MagicMock(content="") # Second call, finds no issues with the refined draft
    ]
    
    # Checklist will be called twice
    mock_checklist_chain.invoke.side_effect = [
        MagicMock(is_sufficient=False, reasoning="The answer lacks substance..."),
        MagicMock(is_sufficient=True, reasoning="The revised answer is comprehensive...")
    ]

    mock_orchestrator_chain.invoke.return_value.content = "Final Answer: The ketogenic diet..."

    # 2. ACT: Run the entire graph
    initial_state = KognysState(question="tell me about keto")
    final_state = kognys_graph.invoke(initial_state)

    # 3. ASSERT: Verify the workflow and final state
    
    assert "Final Answer" in final_state["final_answer"]

    # CORRECTED: Verify the correct number of calls for each agent
    mock_validator_chain.invoke.assert_called_once()
    mock_retriever_search.assert_called_once()
    assert mock_synthesizer_chain.invoke.call_count == 2
    assert mock_challenger_chain.invoke.call_count == 2 # Expect 2 calls now
    assert mock_checklist_chain.invoke.call_count == 2
    mock_orchestrator_chain.invoke.assert_called_once()

    print("\n✅ Full Workflow Test Passed: The agent successfully validated, retrieved, debated, refined, and finalized the answer.")
    