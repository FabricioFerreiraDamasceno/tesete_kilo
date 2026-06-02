"""
Redis Cache Implementation - Provides caching functionality with decorators.
"""

import logging
import functools
import json
from typing import Any, Callable, Optional
import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache wrapper with decorator support."""
    
    def __init__(self):
        self.redis_client = None
        self.connected = False
        self.connect()
    
    def connect(self):
        """Connect to Redis server."""
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.connected = True
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        if not self.connected:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            self.connected = False
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if not self.is_connected():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.warning(f"Redis GET error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if not string)
            timeout: Timeout in seconds (default 5 minutes)
        """
        if not self.is_connected():
            return False
        
        try:
            # Serialize value if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            self.redis_client.setex(key, timeout, value)
            return True
        except Exception as e:
            logger.warning(f"Redis SET error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self.is_connected():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.warning(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in cache."""
        if not self.is_connected():
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Redis INCR error for key {key}: {e}")
            return None
    
    def cache_result(self, timeout: int = 300):
        """
        Decorator to cache function results.
        
        Usage:
            @cache.cache_result(timeout=600)
            def expensive_function(arg1, arg2):
                return compute_something(arg1, arg2)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, timeout)
                logger.debug(f"Cached result for {cache_key}")
                
                return result
            return wrapper
        return decorator
    
    def cache_user_data(self, timeout: int = 600):
        """Decorator specifically for caching user data."""
        return self.cache_result(timeout=timeout)
    
    def cache_targeting_data(self, timeout: int = 300):
        """Decorator specifically for caching targeting data."""
        return self.cache_result(timeout=timeout)
    
    def flush(self) -> bool:
        """Flush all cache data (use with caution)."""
        if not self.is_connected():
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("Redis cache flushed")
            return True
        except Exception as e:
            logger.warning(f"Redis FLUSH error: {e}")
            return False


# Global instance
redis_cache = RedisCache()