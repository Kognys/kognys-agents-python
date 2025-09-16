# kognys/services/sync_cache.py
"""Synchronous cache wrapper for use in non-async contexts"""
import os
import json
import hashlib
import redis
from typing import Optional, List, Dict
import time

class SyncCacheManager:
    """Synchronous Redis cache manager for API responses"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.redis_client: Optional[redis.Redis] = None
        self.ttl_seconds = 86400  # 24 hours
        self.enabled = bool(self.redis_url)
        self._connect()
        
    def _connect(self):
        """Initialize Redis connection"""
        if not self.enabled:
            return
            
        try:
            # Parse Redis URL and create client
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            self.redis_client.ping()
            print("Sync Cache Manager: Connected to Redis")
        except Exception as e:
            print(f"Sync Cache Manager: Redis not available, caching disabled: {e}")
            self.enabled = False
            self.redis_client = None
            
    def _generate_key(self, source: str, query: str, k: int) -> str:
        """Generate a cache key from parameters"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"kognys:cache:{source}:{query_hash}:{k}"
        
    def get(self, source: str, query: str, k: int) -> Optional[List[Dict]]:
        """Retrieve cached results if they exist"""
        if not self.enabled or not self.redis_client:
            return None
            
        key = self._generate_key(source, query, k)
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                data = json.loads(cached_data)
                print(f"Cache hit for {source} query: '{query[:50]}...'")
                
                # Add cache metadata
                for item in data:
                    item['cached'] = True
                    
                return data
        except Exception as e:
            print(f"Sync Cache Manager: Error retrieving from cache: {e}")
            
        return None
        
    def set(self, source: str, query: str, k: int, data: List[Dict]) -> bool:
        """Store results in cache"""
        if not self.enabled or not self.redis_client or not data:
            return False
            
        key = self._generate_key(source, query, k)
        
        try:
            serialized = json.dumps(data)
            self.redis_client.setex(key, self.ttl_seconds, serialized)
            print(f"Cached {len(data)} results for {source} query: '{query[:50]}...'")
            return True
        except Exception as e:
            print(f"Sync Cache Manager: Error storing in cache: {e}")
            
        return False

# Singleton instance
sync_cache_manager = SyncCacheManager()