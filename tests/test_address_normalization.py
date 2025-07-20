# -*- coding: utf-8 -*-
# tests/test_address_normalization.py
import sys
import os

# Add parent directory to path to import from kognys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kognys.utils.address import normalize_address, is_valid_address_format, ensure_address_prefix


def test_normalize_address():
    """Test address normalization functionality."""
    print("Testing address normalization...")
    
    # Test mixed case address normalization
    mixed_case = "0x6604Ef12FB993B31aeaAE18E925b6726e0a3678B"
    expected_lower = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
    
    result = normalize_address(mixed_case)
    assert result == expected_lower, f"Expected {expected_lower}, got {result}"
    print(f"✓ Mixed case normalization: {mixed_case} -> {result}")
    
    # Test already lowercase address
    already_lower = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
    result = normalize_address(already_lower)
    assert result == already_lower, f"Already lowercase should remain unchanged"
    print(f"✓ Already lowercase: {already_lower} -> {result}")
    
    # Test None input
    result = normalize_address(None)
    assert result is None, "None input should return None"
    print("✓ None input handled correctly")
    
    # Test empty string
    result = normalize_address("")
    assert result is None, "Empty string should return None"
    print("✓ Empty string handled correctly")
    
    # Test invalid format
    invalid = "not_an_address"
    result = normalize_address(invalid)
    assert result is None, "Invalid format should return None"
    print(f"✓ Invalid format rejected: {invalid}")
    
    print("✓ All address normalization tests passed!\n")


def test_is_valid_address_format():
    """Test address format validation."""
    print("Testing address format validation...")
    
    # Valid address
    valid = "0x6604Ef12FB993B31aeaAE18E925b6726e0a3678B"
    assert is_valid_address_format(valid), f"Valid address should pass: {valid}"
    print(f"✓ Valid address accepted: {valid}")
    
    # Valid lowercase address
    valid_lower = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
    assert is_valid_address_format(valid_lower), f"Valid lowercase address should pass: {valid_lower}"
    print(f"✓ Valid lowercase address accepted: {valid_lower}")
    
    # Invalid - too short
    too_short = "0x6604ef12fb993b31aeaae18e925b6726e0a3678"
    assert not is_valid_address_format(too_short), f"Too short should fail: {too_short}"
    print(f"✓ Too short address rejected: {too_short}")
    
    # Invalid - too long
    too_long = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b1"
    assert not is_valid_address_format(too_long), f"Too long should fail: {too_long}"
    print(f"✓ Too long address rejected: {too_long}")
    
    # Invalid - missing 0x prefix
    no_prefix = "6604ef12fb993b31aeaae18e925b6726e0a3678b"
    assert not is_valid_address_format(no_prefix), f"Missing prefix should fail: {no_prefix}"
    print(f"✓ Missing prefix rejected: {no_prefix}")
    
    # Invalid - non-hex characters
    non_hex = "0x6604ef12fb993b31aeaae18e925b6726e0a3678g"
    assert not is_valid_address_format(non_hex), f"Non-hex should fail: {non_hex}"
    print(f"✓ Non-hex characters rejected: {non_hex}")
    
    print("✓ All address format validation tests passed!\n")


def test_ensure_address_prefix():
    """Test address prefix handling."""
    print("Testing address prefix handling...")
    
    # Address without prefix
    without_prefix = "6604ef12fb993b31aeaae18e925b6726e0a3678b"
    expected = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
    result = ensure_address_prefix(without_prefix)
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"✓ Added prefix: {without_prefix} -> {result}")
    
    # Address with prefix
    with_prefix = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
    result = ensure_address_prefix(with_prefix)
    assert result == with_prefix, f"Should remain unchanged: {with_prefix}"
    print(f"✓ Prefix preserved: {with_prefix}")
    
    print("✓ All address prefix tests passed!\n")


def test_integration_scenarios():
    """Test real-world integration scenarios."""
    print("Testing integration scenarios...")
    
    # Scenario 1: User submits mixed case address
    user_input = "0x6604Ef12FB993B31aeaAE18E925b6726e0a3678B"
    normalized = normalize_address(user_input)
    expected = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
    
    assert normalized == expected, f"User input normalization failed"
    print(f"✓ User input scenario: {user_input} -> {normalized}")
    
    # Scenario 2: Database comparison (both should match after normalization)
    db_stored = "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"  # Stored lowercase
    api_request = "0x6604Ef12FB993B31aeaAE18E925b6726e0a3678B"  # User sends mixed case
    
    normalized_request = normalize_address(api_request)
    assert normalized_request == db_stored, "Database comparison should work"
    print(f"✓ Database comparison scenario: {api_request} matches stored {db_stored}")
    
    # Scenario 3: Non-address user_id (should pass through unchanged)
    non_address = "user123"
    result = normalize_address(non_address)
    assert result is None, "Non-address should return None for safety"
    print(f"✓ Non-address pass-through: {non_address} -> {result}")
    
    print("✓ All integration scenarios passed!\n")


if __name__ == "__main__":
    print("🧪 Starting address normalization tests...")
    print("=" * 50)
    
    test_normalize_address()
    test_is_valid_address_format()
    test_ensure_address_prefix()
    test_integration_scenarios()
    
    print("=" * 50)
    print("🎉 All tests passed! Address normalization is working correctly.") 