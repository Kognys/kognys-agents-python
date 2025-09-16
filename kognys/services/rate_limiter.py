# kognys/services/rate_limiter.py
import asyncio
import time
from typing import Optional, Callable, Any, Dict
from collections import deque
from dataclasses import dataclass
from enum import Enum

class Priority(Enum):
    """Request priority levels"""
    HIGH = 1
    NORMAL = 2
    LOW = 3

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_second: float
    burst_size: Optional[int] = None
    
    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = int(self.requests_per_second * 2)

class RateLimiter:
    """Token bucket rate limiter for API requests"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_size
        self.max_tokens = config.burst_size
        self.refill_rate = config.requests_per_second
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()
        self.request_queue = asyncio.Queue()
        self.stats = {
            'total_requests': 0,
            'throttled_requests': 0,
            'average_wait_time': 0
        }
        
    async def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.monotonic()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
        
    async def acquire(self, priority: Priority = Priority.NORMAL) -> float:
        """Acquire permission to make a request, returns wait time"""
        start_time = time.monotonic()
        
        async with self.lock:
            await self._refill_tokens()
            
            wait_time = 0
            while self.tokens < 1:
                # Calculate wait time needed
                tokens_needed = 1 - self.tokens
                wait_time = tokens_needed / self.refill_rate
                
                # Apply priority-based wait time adjustment
                if priority == Priority.HIGH:
                    wait_time *= 0.5
                elif priority == Priority.LOW:
                    wait_time *= 1.5
                    
                print(f"Rate limiter: Waiting {wait_time:.2f}s (priority: {priority.name})")
                await asyncio.sleep(wait_time)
                await self._refill_tokens()
                
                self.stats['throttled_requests'] += 1
                
            # Consume a token
            self.tokens -= 1
            self.stats['total_requests'] += 1
            
        actual_wait = time.monotonic() - start_time
        
        # Update average wait time
        if self.stats['total_requests'] > 1:
            self.stats['average_wait_time'] = (
                (self.stats['average_wait_time'] * (self.stats['total_requests'] - 1) + actual_wait) 
                / self.stats['total_requests']
            )
        else:
            self.stats['average_wait_time'] = actual_wait
            
        return actual_wait
        
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            **self.stats,
            'current_tokens': self.tokens,
            'max_tokens': self.max_tokens,
            'refill_rate': self.refill_rate
        }

class RateLimitManager:
    """Manages rate limiters for different services"""
    
    def __init__(self):
        self.limiters = {
            'openalex': RateLimiter(RateLimitConfig(
                requests_per_second=10.0,
                burst_size=20
            )),
            'arxiv': RateLimiter(RateLimitConfig(
                requests_per_second=3.0,
                burst_size=10
            ))
        }
        
    async def acquire(self, service: str, priority: Priority = Priority.NORMAL) -> float:
        """Acquire permission for a specific service"""
        if service not in self.limiters:
            return 0  # No rate limiting for unknown services
            
        return await self.limiters[service].acquire(priority)
        
    def get_stats(self, service: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for rate limiters"""
        if service:
            return self.limiters.get(service, {}).get_stats() if service in self.limiters else {}
            
        return {
            name: limiter.get_stats() 
            for name, limiter in self.limiters.items()
        }

# Singleton instance
rate_limit_manager = RateLimitManager()

async def rate_limited(service: str, func: Callable, *args, **kwargs) -> Any:
    """Decorator/wrapper for rate-limited function calls"""
    wait_time = await rate_limit_manager.acquire(service)
    
    if wait_time > 0:
        print(f"Rate limited: Waited {wait_time:.2f}s before calling {func.__name__}")
        
    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)