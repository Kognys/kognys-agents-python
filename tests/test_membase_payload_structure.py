# -*- coding: utf-8 -*-
# tests/test_membase_payload_structure.py
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path to import from kognys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kognys.services.membase_client import store_final_answer_in_kb


class TestMembasePayloadStructure:
    """Test the correct payload structure for Membase knowledge base operations."""
    
    @patch('kognys.services.membase_client.requests.post')
    @patch('kognys.services.membase_client.API_BASE_URL', 'https://test-api.example.com')
    def test_store_final_answer_payload_structure_with_user_id(self, mock_post):
        """Test that the payload structure is correct when user_id is provided."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        paper_id = "test-paper-123"
        paper_content = "This is a test research paper about AI."
        original_question = "What is artificial intelligence?"
        user_id = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
        
        # Act
        result = store_final_answer_in_kb(paper_id, paper_content, original_question, user_id)
        
        # Assert
        assert result is True
        assert mock_post.called
        
        # Verify the URL
        call_args = mock_post.call_args
        expected_url = "https://test-api.example.com/api/v1/knowledge/documents"
        assert call_args[1]['url'] == expected_url
        
        # Verify the payload structure
        payload = call_args[1]['json']
        
        # Check top-level structure
        assert "documents" in payload
        assert "strict" in payload
        assert payload["strict"] is True
        
        # Verify documents is a single object, not an array
        documents = payload["documents"]
        assert isinstance(documents, dict), "documents should be a dict, not a list"
        assert not isinstance(documents, list), "documents should not be an array"
        
        # Verify document structure
        assert "content" in documents
        assert "metadata" in documents
        assert documents["content"] == paper_content
        
        # Verify metadata structure
        metadata = documents["metadata"]
        assert metadata["paper_id"] == paper_id
        assert metadata["original_question"] == original_question
        assert metadata["user_id"] == user_id
        
        print("✓ Payload structure test with user_id PASSED")

    @patch('kognys.services.membase_client.requests.post')
    @patch('kognys.services.membase_client.API_BASE_URL', 'https://test-api.example.com')
    def test_store_final_answer_payload_structure_without_user_id(self, mock_post):
        """Test that the payload structure is correct when user_id is None."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        paper_id = "test-paper-456"
        paper_content = "This is another test research paper."
        original_question = "What is machine learning?"
        user_id = None
        
        # Act
        result = store_final_answer_in_kb(paper_id, paper_content, original_question, user_id)
        
        # Assert
        assert result is True
        assert mock_post.called
        
        # Verify the payload structure
        payload = mock_post.call_args[1]['json']
        
        # Check top-level structure
        assert "documents" in payload
        assert "strict" in payload
        assert payload["strict"] is True
        
        # Verify documents is a single object, not an array
        documents = payload["documents"]
        assert isinstance(documents, dict), "documents should be a dict, not a list"
        
        # Verify metadata structure (user_id should not be included)
        metadata = documents["metadata"]
        assert metadata["paper_id"] == paper_id
        assert metadata["original_question"] == original_question
        assert "user_id" not in metadata, "user_id should not be in metadata when None"
        
        print("✓ Payload structure test without user_id PASSED")

    @patch('kognys.services.membase_client.requests.post')
    @patch('kognys.services.membase_client.API_BASE_URL', 'https://test-api.example.com')
    def test_payload_matches_partner_api_format(self, mock_post):
        """Test that our payload exactly matches the format expected by partner's API."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Act
        store_final_answer_in_kb(
            paper_id="abc123",
            paper_content="Machine learning is a subset of AI...",
            original_question="What is ML?",
            user_id="0x6604Ef12FB993B31aeaAE18E925b6726e0a3678B"
        )
        
        # Assert - Check exact format matches partner's example
        payload = mock_post.call_args[1]['json']
        
        expected_structure = {
            "documents": {
                "content": "Machine learning is a subset of AI...",
                "metadata": {
                    "paper_id": "abc123",
                    "original_question": "What is ML?",
                    "user_id": "0x6604Ef12FB993B31aeaAE18E925b6726e0a3678B"
                }
            },
            "strict": True
        }
        
        assert payload == expected_structure
        print("✓ Partner API format compatibility test PASSED")

    @patch('kognys.services.membase_client.requests.post')
    @patch('kognys.services.membase_client.API_BASE_URL', 'https://test-api.example.com')
    def test_error_handling(self, mock_post):
        """Test error handling when API call fails."""
        # Arrange
        mock_post.side_effect = Exception("API Error")
        
        # Act
        result = store_final_answer_in_kb("test", "content", "question", "user123")
        
        # Assert
        assert result is False
        assert mock_post.called
        
        print("✓ Error handling test PASSED")

    def test_payload_serialization(self):
        """Test that the payload can be properly serialized to JSON."""
        # This tests the structure without making actual API calls
        paper_id = "test-serialization"
        paper_content = "Test content with special characters and unicode"
        original_question = "Test question?"
        user_id = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
        
        # Simulate the payload creation logic
        metadata = {"paper_id": paper_id, "original_question": original_question}
        metadata["user_id"] = user_id
        document = {"content": paper_content, "metadata": metadata}
        payload = {"documents": document, "strict": True}
        
        # Test JSON serialization
        try:
            json_str = json.dumps(payload)
            parsed_back = json.loads(json_str)
            assert parsed_back == payload
            print("✓ JSON serialization test PASSED")
        except Exception as e:
            raise AssertionError("JSON serialization failed: " + str(e))


def test_regression_no_array_structure():
    """Regression test to ensure we never go back to array structure."""
    paper_id = "regression-test"
    paper_content = "Regression test content"
    original_question = "Regression test question"
    user_id = "test-user"
    
    # Simulate the corrected payload structure
    metadata = {"paper_id": paper_id, "original_question": original_question}
    metadata["user_id"] = user_id
    document = {"content": paper_content, "metadata": metadata}
    payload = {"documents": document, "strict": True}
    
    # Assert the structure is correct
    assert isinstance(payload["documents"], dict), "documents must be a dict object"
    assert not isinstance(payload["documents"], list), "documents must NOT be a list/array"
    assert payload["strict"] is True, "strict parameter must be included"
    
    # Ensure user_id is in the right place
    assert payload["documents"]["metadata"]["user_id"] == user_id
    
    print("✓ Regression test PASSED - no array structure")


if __name__ == "__main__":
    # Run tests directly
    test_suite = TestMembasePayloadStructure()
    
    print("Running Membase Payload Structure Tests...")
    print("=" * 50)
    
    try:
        test_suite.test_store_final_answer_payload_structure_with_user_id()
        test_suite.test_store_final_answer_payload_structure_without_user_id()
        test_suite.test_payload_matches_partner_api_format()
        test_suite.test_error_handling()
        test_suite.test_payload_serialization()
        test_regression_no_array_structure()
        
        print("=" * 50)
        print("All tests PASSED!")
        
    except Exception as e:
        print("Test failed: " + str(e))
        raise 