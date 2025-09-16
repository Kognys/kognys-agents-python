# kognys/services/cache_manager.py
import os
import json
import hashlib
import asyncio
from typing import Optional, Dict, Any, List
import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError
import time

class CacheManager:
    """Manages caching for API responses using Redis"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.redis_client: Optional[Redis] = None
        self.ttl_seconds = 86400  # 24 hours default TTL
        self.enabled = bool(self.redis_url)
        
    async def connect(self):
        """Initialize Redis connection"""
        if not self.enabled:
            print("Cache Manager: Redis URL not configured, caching disabled")
            return
            
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 3,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                }
            )
            await self.redis_client.ping()
            print("Cache Manager: Connected to Redis successfully")
        except Exception as e:
            print(f"Cache Manager: Failed to connect to Redis: {e}")
            self.enabled = False
            
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            
    def _generate_key(self, source: str, query: str, k: int) -> str:
        """Generate a cache key from parameters"""
        # Create a consistent hash of the query
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"kognys:cache:{source}:{query_hash}:{k}"
        
    async def get(self, source: str, query: str, k: int) -> Optional[List[Dict]]:
        """Retrieve cached results if they exist"""
        if not self.enabled or not self.redis_client:
            return None
            
        key = self._generate_key(source, query, k)
        
        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                data = json.loads(cached_data)
                print(f"Cache hit for {source} query: '{query[:50]}...'")
                
                # Add cache metadata
                for item in data:
                    item['cached'] = True
                    item['cache_key'] = key
                    
                return data
        except (RedisError, json.JSONDecodeError) as e:
            print(f"Cache Manager: Error retrieving from cache: {e}")
            
        return None
        
    async def set(self, source: str, query: str, k: int, data: List[Dict], ttl: Optional[int] = None) -> bool:
        """Store results in cache"""
        if not self.enabled or not self.redis_client or not data:
            return False
            
        key = self._generate_key(source, query, k)
        ttl = ttl or self.ttl_seconds
        
        try:
            # Store with metadata
            cache_data = {
                'data': data,
                'cached_at': time.time(),
                'source': source,
                'query': query
            }
            
            serialized = json.dumps(data)  # Store just the data array
            await self.redis_client.setex(key, ttl, serialized)
            print(f"Cached {len(data)} results for {source} query: '{query[:50]}...' (TTL: {ttl}s)")
            return True
        except (RedisError, json.JSONEncodeError) as e:
            print(f"Cache Manager: Error storing in cache: {e}")
            
        return False
        
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching a pattern"""
        if not self.enabled or not self.redis_client:
            return 0
            
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
                
            if keys:
                deleted = await self.redis_client.delete(*keys)
                print(f"Cache Manager: Cleared {deleted} cache entries")
                return deleted
        except RedisError as e:
            print(f"Cache Manager: Error clearing cache: {e}")
            
        return 0
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled or not self.redis_client:
            return {'enabled': False}
            
        try:
            info = await self.redis_client.info('stats')
            return {
                'enabled': True,
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'N/A')
            }
        except RedisError as e:
            print(f"Cache Manager: Error getting stats: {e}")
            return {'enabled': False, 'error': str(e)}

# Singleton instance
cache_manager = CacheManager()