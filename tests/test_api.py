from fastapi.testclient import TestClient
from unittest.mock import patch

# Import the FastAPI app instance from your api_main.py file
from api_main import app

# Create a client to interact with your API in a test environment
client = TestClient(app)


@patch('api_main.kognys_graph.invoke')
def test_create_paper_endpoint(mock_graph_invoke):
    """
    Tests the POST /papers endpoint.
    It mocks the agent graph to ensure the API layer works in isolation.
    """
    # 1. ARRANGE: Set up the mock return value for the Kognys agent
    mock_final_answer = "This is a detailed research paper about quantum computing."
    mock_graph_invoke.return_value = {
        "final_answer": mock_final_answer,
        "retrieval_status": "Documents found"
    }

    # Define the request payload
    request_payload = {
        "message": "What is quantum computing?",
        "user_id": "test-user-001"
    }

    # 2. ACT: Make a request to the API endpoint
    response = client.post("/papers", json=request_payload)

    # 3. ASSERT: Check the response and that our agent was called
    assert response.status_code == 200
    response_data = response.json()
    assert "paper_id" in response_data
    assert response_data["paper_content"] == mock_final_answer
    mock_graph_invoke.assert_called_once()
    
    print("\n✅ API test for POST /papers passed successfully.")


@patch('api_main.get_paper_by_title')
def test_get_paper_endpoint(mock_get_paper):
    """
    Tests the GET /papers/{paper_title} endpoint.
    It mocks the service function to ensure the API layer works in isolation.
    """
    # 1. ARRANGE: Set up the mock return value for the Membase client
    # --- THIS IS THE FIX: Removed the trailing '?' ---
    paper_title_to_find = "Research on: What is quantum computing"
    # --- END OF FIX ---
    
    mock_paper_content = "This is a detailed research paper about quantum computing."
    mock_get_paper.return_value = {
        "source": "doc-id-123",
        "content": mock_paper_content,
        "score": 0.95
    }

    # 2. ACT: Make a request to the API endpoint
    response = client.get(f"/papers/{paper_title_to_find}")

    # 3. ASSERT: Check the response and that our service was called
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["paper_id"] == "doc-id-123"
    assert response_data["paper_content"] == mock_paper_content
    mock_get_paper.assert_called_once_with(paper_title_to_find)

    print("\n✅ API test for GET /papers/{paper_title} passed successfully.")


@patch('api_main.get_paper_by_title')
def test_get_paper_not_found(mock_get_paper):
    """
    Tests the GET /papers/{paper_title} endpoint for a paper that doesn't exist.
    """
    # 1. ARRANGE: Set the mock to return None, simulating a failed search
    mock_get_paper.return_value = None
    
    paper_title_to_find = "A paper that does not exist"

    # 2. ACT: Make a request to the API endpoint
    response = client.get(f"/papers/{paper_title_to_find}")

    # 3. ASSERT: Check that the API returns a 404 Not Found error
    assert response.status_code == 404
    assert response.json() == {"detail": "Paper not found in the knowledge base."}
    mock_get_paper.assert_called_once_with(paper_title_to_find)
    
    print("\n✅ API test for 404 Not Found passed successfully.")
