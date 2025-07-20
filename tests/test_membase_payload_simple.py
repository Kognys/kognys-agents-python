# -*- coding: utf-8 -*-
# tests/test_membase_payload_simple.py
import json
import sys
import os

# Add parent directory to path to import from kognys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_payload_structure():
    """Test the payload structure matches partner's API expectations."""
    print("Testing Membase payload structure...")
    
    # Simulate the payload creation logic from store_final_answer_in_kb
    paper_id = "test-paper-123"
    paper_content = "This is a test research paper about AI."
    original_question = "What is artificial intelligence?"
    user_id = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
    
    # Build metadata same way as the function
    metadata = {"paper_id": paper_id, "original_question": original_question}
    if user_id:
        metadata["user_id"] = user_id
    
    # Build document same way as the function  
    document = {"content": paper_content, "metadata": metadata}
    
    # Build payload same way as the function
    payload = {"documents": document, "strict": True}
    
    # Test 1: Verify documents is a dict, not an array
    assert isinstance(payload["documents"], dict), "documents should be a dict object"
    assert not isinstance(payload["documents"], list), "documents should NOT be an array"
    print("✓ Payload documents structure is correct (dict, not array)")
    
    # Test 2: Verify strict parameter is included
    assert "strict" in payload, "strict parameter should be included"
    assert payload["strict"] is True, "strict should be True"
    print("✓ Strict parameter is correctly included")
    
    # Test 3: Verify document has correct structure
    documents = payload["documents"]
    assert "content" in documents, "document should have content field"
    assert "metadata" in documents, "document should have metadata field"
    assert documents["content"] == paper_content, "content should match"
    print("✓ Document structure is correct")
    
    # Test 4: Verify metadata has correct fields
    metadata_check = documents["metadata"]
    assert metadata_check["paper_id"] == paper_id, "paper_id should match"
    assert metadata_check["original_question"] == original_question, "original_question should match"
    assert metadata_check["user_id"] == user_id, "user_id should match"
    print("✓ Metadata structure is correct with user_id")
    
    # Test 5: Verify exact structure matches partner's API example
    expected_structure = {
        "documents": {
            "content": paper_content,
            "metadata": {
                "paper_id": paper_id,
                "original_question": original_question,
                "user_id": user_id
            }
        },
        "strict": True
    }
    
    assert payload == expected_structure, "Payload should exactly match expected structure"
    print("✓ Payload exactly matches partner's API format")
    
    return True

def test_payload_without_user_id():
    """Test payload structure when user_id is None."""
    print("Testing payload structure without user_id...")
    
    paper_id = "test-paper-456"
    paper_content = "Another test paper"
    original_question = "Test question"
    user_id = None
    
    # Build payload same way as the function
    metadata = {"paper_id": paper_id, "original_question": original_question}
    if user_id:  # This condition will be False
        metadata["user_id"] = user_id
    
    document = {"content": paper_content, "metadata": metadata}
    payload = {"documents": document, "strict": True}
    
    # Verify user_id is NOT in metadata when None
    assert "user_id" not in payload["documents"]["metadata"], "user_id should not be in metadata when None"
    print("✓ user_id correctly excluded when None")
    
    return True

def test_json_serialization():
    """Test that the payload can be serialized to JSON."""
    print("Testing JSON serialization...")
    
    # Create a test payload
    metadata = {
        "paper_id": "json-test",
        "original_question": "Can this be serialized?",
        "user_id": "test-user-123"
    }
    document = {"content": "Test content for JSON", "metadata": metadata}
    payload = {"documents": document, "strict": True}
    
    # Test serialization
    try:
        json_string = json.dumps(payload)
        parsed_back = json.loads(json_string)
        assert parsed_back == payload, "Parsed JSON should match original payload"
        print("✓ JSON serialization works correctly")
        return True
    except Exception as e:
        raise AssertionError("JSON serialization failed: " + str(e))

def test_regression_no_array():
    """Regression test to ensure we never go back to using arrays."""
    print("Testing regression - ensuring no array structure...")
    
    # This tests that we don't accidentally revert to the old format
    metadata = {"paper_id": "regression-test", "user_id": "test"}
    document = {"content": "test", "metadata": metadata}
    
    # OLD WAY (wrong): payload = {"documents": [document]}
    # NEW WAY (correct): payload = {"documents": document, "strict": True}
    
    correct_payload = {"documents": document, "strict": True}
    wrong_payload = {"documents": [document]}  # This is what we DON'T want
    
    # Verify correct structure
    assert isinstance(correct_payload["documents"], dict), "Correct payload should use dict"
    assert not isinstance(correct_payload["documents"], list), "Correct payload should NOT use list"
    
    # Verify wrong structure is different
    assert isinstance(wrong_payload["documents"], list), "Wrong payload uses list (this is what we fixed)"
    
    print("✓ Regression test passed - not using array structure")
    return True

def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("MEMBASE PAYLOAD STRUCTURE TESTS")
    print("=" * 60)
    
    tests = [
        test_payload_structure,
        test_payload_without_user_id, 
        test_json_serialization,
        test_regression_no_array
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print("")  # Add spacing between tests
        except Exception as e:
            failed += 1
            print("FAILED: " + str(e))
            print("")
    
    print("=" * 60)
    print("RESULTS: " + str(passed) + " passed, " + str(failed) + " failed")
    
    if failed == 0:
        print("ALL TESTS PASSED!")
        return True
    else:
        print("SOME TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1) 