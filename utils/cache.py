# utils/cache.py
import functools
import time
from typing import Dict, Any

_cache: Dict[str, Dict[str, Any]] = {}

def cached(ttl: int = 300):
    """Cache decorator with TTL."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            now = time.time()
            
            if key in _cache:
                cached_data = _cache[key]
                if now - cached_data["timestamp"] < ttl:
                    return cached_data["data"]
            
            result = func(*args, **kwargs)
            _cache[key] = {"data": result, "timestamp": now}
            return result
        return wrapper
    return decorator
