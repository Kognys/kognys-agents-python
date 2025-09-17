# kognys/services/transaction_events.py
"""
Global transaction event system for blockchain operations.

This module provides a centralized way to emit and consume blockchain transaction events
across different parts of the application without circular import issues.
"""

import asyncio
import time
from typing import Dict, Any, Optional

# Global transaction event queue
_transaction_queue: Optional[asyncio.Queue] = None

def get_transaction_queue() -> asyncio.Queue:
    """Get or create the global transaction event queue."""
    global _transaction_queue
    if _transaction_queue is None:
        _transaction_queue = asyncio.Queue()
    return _transaction_queue

def emit_transaction_confirmed(task_id: str, transaction_hash: str, operation: str = "task_finish"):
    """Emit a transaction_confirmed event to the global queue."""
    try:
        queue = get_transaction_queue()
        event = {
            "event_type": "transaction_confirmed",
            "data": {
                "task_id": task_id,
                "transaction_hash": transaction_hash,
                "operation": operation,
                "status": "Blockchain transaction confirmed"
            },
            "timestamp": time.time(),
            "agent": "system"
        }
        
        queue.put_nowait(event)
        print(f"📡 Emitted transaction_confirmed: {transaction_hash}")
        return True
    except Exception as e:
        print(f"❌ Failed to emit transaction_confirmed: {e}")
        return False

def emit_transaction_failed(task_id: str, error: str, operation: str = "task_finish"):
    """Emit a transaction_failed event to the global queue."""
    try:
        queue = get_transaction_queue()
        event = {
            "event_type": "transaction_failed",
            "data": {
                "task_id": task_id,
                "error": error,
                "operation": operation,
                "status": "Blockchain transaction failed"
            },
            "timestamp": time.time(),
            "agent": "system"
        }
        
        queue.put_nowait(event)
        print(f"📡 Emitted transaction_failed: {error}")
        return True
    except Exception as e:
        print(f"❌ Failed to emit transaction_failed: {e}")
        return False

async def get_transaction_event(timeout: float = 30.0) -> Optional[Dict[str, Any]]:
    """Get the next transaction event from the queue."""
    try:
        queue = get_transaction_queue()
        return await asyncio.wait_for(queue.get(), timeout=timeout)
    except asyncio.TimeoutError:
        return None
    except Exception as e:
        print(f"❌ Error getting transaction event: {e}")
        return None
