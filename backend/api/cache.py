import json
import logging
from functools import wraps
from typing import Optional, Callable
import redis
import os

logger = logging.getLogger(__name__)

# Connect to Redis
def get_redis():
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return None


def cache_response(key: str, ttl: int = 300):
    """
    Cache decorator for FastAPI route functions.
    ttl = seconds to cache (default 5 minutes)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            r = get_redis()
            if not r:
                return func(*args, **kwargs)

            # Build cache key from function args
            cache_key = f"cache:{key}:{hash(str(kwargs))}"

            try:
                cached = r.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

            # Call the actual function
            result = func(*args, **kwargs)

            try:
                r.setex(cache_key, ttl, json.dumps(result, default=str))
                logger.debug(f"Cache set: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")

            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """Delete all cache keys matching a pattern."""
    r = get_redis()
    if not r:
        return
    try:
        keys = r.keys(f"cache:{pattern}:*")
        if keys:
            r.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys for {pattern}")
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")


def get_cached(key: str) -> Optional[dict]:
    """Get a value from cache."""
    r = get_redis()
    if not r:
        return None
    try:
        value = r.get(f"cache:{key}")
        return json.loads(value) if value else None
    except Exception:
        return None


def set_cached(key: str, value: dict, ttl: int = 300):
    """Set a value in cache."""
    r = get_redis()
    if not r:
        return
    try:
        r.setex(f"cache:{key}", ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"Cache set error: {e}")