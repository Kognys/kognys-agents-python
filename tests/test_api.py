from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import uuid

# Import the FastAPI app instance from your api_main.py file
from api_main import app

# Create a client to interact with your API in a test environment
client = TestClient(app)


def test_health_check_endpoint():
    """
    Tests the GET / endpoint to ensure it returns a successful response.
    """
    # 1. ACT: Make a request to the health check endpoint
    response = client.get("/")

    # 2. ASSERT: Check that the API returned a successful status code and message
    assert response.status_code == 200
    # --- THIS IS THE FIX: Changed to match the actual API response ---
    assert response.json() == {"status": "ok"}
    # --- END OF FIX ---
    
    print("\n✅ API test for GET / (health check) passed successfully.")


@patch('api_main.kognys_graph.ainvoke', new_callable=AsyncMock)
def test_create_paper_endpoint(mock_graph_invoke):
    """
    Tests the POST /papers endpoint.
    It mocks the agent graph to ensure the API layer works in isolation.
    """
    # 1. ARRANGE: Set up the mock return value for the Kognys agent
    mock_final_answer = "This is a detailed research paper about decentralized AI."
    # Since we're now using ainvoke (async), use AsyncMock
    mock_graph_invoke.return_value = {
        "final_answer": mock_final_answer,
        "retrieval_status": "Documents found"
    }

    # Define the request payload
    request_payload = {
        "message": "What is decentralized AI?",
        "user_id": "test-user-002"
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


@patch('api_main.download_paper_from_da')
def test_get_paper_endpoint(mock_download_paper):
    """
    Tests the GET /papers/{paper_id} endpoint.
    It mocks the unibase_da_client to ensure the API layer works in isolation.
    """
    # 1. ARRANGE: Set up the mock return value for the DA client
    paper_id_to_find = str(uuid.uuid4())
    mock_paper_content = "This is the content of the downloaded paper."
    mock_download_paper.return_value = {
        "id": paper_id_to_find,
        "message": mock_paper_content,
        "owner": "test-owner"
    }

    # 2. ACT: Make a request to the API endpoint
    response = client.get(f"/papers/{paper_id_to_find}")

    # 3. ASSERT: Check the response and that our service was called
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["paper_id"] == paper_id_to_find
    assert response_data["paper_content"] == mock_paper_content
    mock_download_paper.assert_called_once_with(paper_id_to_find)

    print("\n✅ API test for GET /papers/{paper_id} passed successfully.")


@patch('api_main.download_paper_from_da')
def test_get_paper_not_found(mock_download_paper):
    """
    Tests the GET /papers/{paper_id} endpoint for a paper that doesn't exist.
    """
    # 1. ARRANGE: Set the mock to return None, simulating a failed download
    mock_download_paper.return_value = None
    
    paper_id_to_find = "an-id-that-does-not-exist"

    # 2. ACT: Make a request to the API endpoint
    response = client.get(f"/papers/{paper_id_to_find}")

    # 3. ASSERT: Check that the API returns a 404 Not Found error
    assert response.status_code == 404
    assert response.json() == {"detail": "Paper not found in Unibase DA."}
    mock_download_paper.assert_called_once_with(paper_id_to_find)
    
    print("\n✅ API test for 404 Not Found passed successfully.")