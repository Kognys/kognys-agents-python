# tests/test_full_workflow.py
from unittest.mock import patch, MagicMock
from kognys.graph.builder import kognys_graph
from kognys.graph.state import KognysState

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
    including one full debate-and-refine loop, with detailed logging.
    """
    # 1. ARRANGE: Configure all mock responses
    print("\n\n--- 🧪 ARRANGE: SETTING UP MOCKS ---")
    mock_validator_chain.invoke.return_value.approved = True
    mock_validator_chain.invoke.return_value.revised_question = "What are the health benefits of a ketogenic diet?"
    mock_retriever_search.return_value = [
        {"content": "Keto can lead to weight loss.", "score": 0.9},
        {"content": "It may improve cognitive function.", "score": 0.8}
    ]
    mock_synthesizer_chain.invoke.side_effect = [
        MagicMock(content="The keto diet is a diet."),
        MagicMock(content="The ketogenic diet can result in weight loss and may enhance cognitive function.")
    ]
    mock_challenger_chain.invoke.side_effect = [
        MagicMock(content="* The answer is vague and misses key details from the documents."),
        MagicMock(content="")
    ]
    mock_checklist_chain.invoke.side_effect = [
        MagicMock(is_sufficient=False, reasoning="The answer lacks substance..."),
        MagicMock(is_sufficient=True, reasoning="The revised answer is comprehensive...")
    ]
    mock_orchestrator_chain.invoke.return_value.content = "Final Answer: The ketogenic diet offers two primary health benefits..."
    print("Mocks configured successfully.")

    # 2. ACT: Run the graph a SINGLE time using .stream()
    print("\n--- 🏃 ACT: RUNNING GRAPH & STREAMING STATE ---")
    initial_state = KognysState(question="tell me about keto")
    
    final_state = {}
    for chunk in kognys_graph.stream(initial_state):
        # The stream yields updates at each step. We log the update and also merge it into our final_state accumulator.
        node_name, state_update = list(chunk.items())[0]
        print(f"\n--- STEP: Node '{node_name}' ---")
        print(f"  - Update: {state_update}")
        final_state.update(state_update)

    # 3. ASSERT: Verify the final state and call counts
    print("\n\n--- ✅ ASSERT: VERIFYING RESULTS ---")
    
    assert "Final Answer" in final_state["final_answer"]
    print("=> Assertion PASSED: Final answer is correct.")

    mock_validator_chain.invoke.assert_called_once()
    mock_retriever_search.assert_called_once()
    assert mock_synthesizer_chain.invoke.call_count == 2
    assert mock_challenger_chain.invoke.call_count == 2
    assert mock_checklist_chain.invoke.call_count == 2
    mock_orchestrator_chain.invoke.assert_called_once()
    print("=> Assertion PASSED: All agents were called the correct number of times.")

    print("\n[SUCCESS] Full Workflow Test Passed.")
