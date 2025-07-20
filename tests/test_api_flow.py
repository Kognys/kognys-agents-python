# test_api_flow.py
import requests
import time

# Make sure your FastAPI server is running before executing this script
API_BASE_URL = "http://localhost:8000"

def run_api_tests():
    """
    Runs a series of tests against the live Kognys API server.
    """
    print("="*60)
    print("🚀 STARTING KOGNYS API FLOW TEST 🚀")
    print("="*60)

    # --- Test 1: Health Check ---
    print("\n--- ✅ 1. Testing Health Check (GET /) ---")
    try:
        response = requests.get(API_BASE_URL)
        response.raise_for_status()
        assert response.json() == {"status": "ok"}
        print("    - PASSED: Health check returned 'ok'.")
    except Exception as e:
        print(f"    - FAILED: Health check failed. Error: {e}")
        return

    # --- Test 2: Bad Question (Rejection Case) ---
    print("\n--- ✅ 2. Testing Bad Question (POST /papers) ---")
    bad_payload = {"message": "hi", "user_id": "test-user-bad"}
    try:
        response = requests.post(f"{API_BASE_URL}/papers", json=bad_payload)
        assert response.status_code == 400
        print(f"    - PASSED: API correctly returned a {response.status_code} error for a bad question.")
        print(f"    - Server Response: {response.json()['detail'][:100]}...")
    except Exception as e:
        print(f"    - FAILED: Bad question test failed. Error: {e}")
        return

    # --- Test 3: Good Question & Retrieval (Happy Path) ---
    print("\n--- ✅ 3. Testing Good Question & Retrieval (POST /papers, GET /papers/{id}) ---")
    good_payload = {
        "message": "What are the benefits of using LangGraph for AI agents?",
        "user_id": "test-user-good"
    }
    paper_id = None
    original_content = None

    try:
        print("    - Submitting a good research question...")
        response = requests.post(f"{API_BASE_URL}/papers", json=good_payload)
        response.raise_for_status()
        assert response.status_code == 200
        
        data = response.json()
        paper_id = data.get("paper_id")
        original_content = data.get("paper_content")
        
        assert paper_id and original_content
        print(f"    - PASSED: Successfully created paper with ID: {paper_id}")
    except Exception as e:
        print(f"    - FAILED: Submitting a good question failed. Error: {e}")
        return

    # Wait a moment for the data to be retrievable from the KB
    print("    - Waiting 2 seconds before retrieval...")
    time.sleep(2)

    try:
        print(f"    - Retrieving the created paper with ID: {paper_id}...")
        response = requests.get(f"{API_BASE_URL}/papers/{paper_id}")
        response.raise_for_status()
        assert response.status_code == 200

        retrieved_data = response.json()
        assert retrieved_data.get("paper_id") == paper_id
        # Note: We don't assert content equality as the final answer might have slight variations
        print(f"    - PASSED: Successfully retrieved paper with ID: {paper_id}")
    except Exception as e:
        print(f"    - FAILED: Retrieving the paper failed. Error: {e}")
        return
        
    print("\n" + "="*60)
    print("🎉 ALL API TESTS PASSED SUCCESSFULLY! 🎉")
    print("="*60)


if __name__ == "__main__":
    # First, make sure your API server is running in another terminal:
    # uvicorn api_main:app --host 0.0.0.0 --port 8000
    run_api_tests()
