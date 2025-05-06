"""Caching mechanism for contextual information."""

import time
from typing import Dict, Any, Optional, Callable, Tuple
from functools import wraps

class Cache:
    """Cache for contextual information.
    
    Provides time-based caching to minimize external API calls.
    """
    
    def __init__(self, default_ttl: int = 300):
        """Initialize the cache.
        
        Args:
            default_ttl: Default time-to-live for cache entries in seconds.
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache if it exists and is not expired.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found or expired.
        """
        if key not in self._cache:
            return None
            
        value, expiry = self._cache[key]
        if time.time() > expiry:
            # Remove expired entry
            del self._cache[key]
            return None
            
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache with a time-to-live.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds. Defaults to the cache default_ttl.
        """
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    def invalidate(self, key: str) -> None:
        """Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate.
        """
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


def cached(ttl: Optional[int] = None):
    """Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds. If None, uses the cache default.
        
    Returns:
        Decorated function.
    """
    def decorator(func: Callable):
        # Create a cache for this function
        func_cache = Cache(default_ttl=ttl or 300)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name, args, and kwargs
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = "|".join(key_parts)
            
            # Try to get from cache
            cached_value = func_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Cache the result
            func_cache.set(cache_key, result, ttl)
            
            return result
        
        # Attach the cache to the function for potential manual access
        wrapper.cache = func_cache
        return wrapper
    
    return decorator
