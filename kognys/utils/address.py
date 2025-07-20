# kognys/utils/address.py
"""
Utility functions for Ethereum address handling and normalization.
"""
import re
from typing import Optional


def normalize_address(address: Optional[str]) -> Optional[str]:
    """
    Normalize an Ethereum address to lowercase format.
    
    Args:
        address: Ethereum address string (can be None)
    
    Returns:
        Normalized lowercase address or None if input is None/invalid
    
    Example:
        >>> normalize_address("0x6604Ef12FB993B31aeaAE18E925b6726e0a3678B")
        "0x6604ef12fb993b31aeaae18e925b6726e0a3678b"
    """
    if not address:
        return None
    
    # Remove any whitespace
    address = str(address).strip()
    
    # Check if it looks like a valid Ethereum address (0x followed by 40 hex chars)
    if not is_valid_address_format(address):
        return None
    
    # Return lowercase version
    return address.lower()


def is_valid_address_format(address: str) -> bool:
    """
    Check if a string has valid Ethereum address format.
    
    Args:
        address: String to validate
    
    Returns:
        True if address has valid format (0x + 40 hex chars)
    """
    if not address:
        return False
    
    # Ethereum address pattern: 0x followed by exactly 40 hexadecimal characters
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))


def ensure_address_prefix(address: str) -> str:
    """
    Ensure address has 0x prefix.
    
    Args:
        address: Address string
    
    Returns:
        Address with 0x prefix
    """
    if not address:
        return address
    
    address = address.strip()
    if not address.startswith('0x'):
        return f"0x{address}"
    
    return address 