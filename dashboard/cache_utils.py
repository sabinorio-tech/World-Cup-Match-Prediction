from __future__ import annotations

from functools import lru_cache, wraps
import time


def ttl_cache(ttl_seconds: int = 300, maxsize: int = 8):
    """Small dependency-free TTL cache for dashboard data loaders."""
    def decorator(function):
        @lru_cache(maxsize=maxsize)
        def cached(time_bucket, args, kwargs):
            return function(*args, **dict(kwargs))

        @wraps(function)
        def wrapper(*args, **kwargs):
            bucket = int(time.monotonic() // ttl_seconds)
            return cached(bucket, args, tuple(sorted(kwargs.items())))

        wrapper.cache_clear = cached.cache_clear
        return wrapper
    return decorator
