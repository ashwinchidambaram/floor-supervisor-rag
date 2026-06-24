"""Redis-backed cache — embeddings and LLM responses keyed by a hash of their input.

Role:     Provider-agnostic exact-match cache. Same input -> same key -> cached value,
          with a TTL. Cuts repeat embedding compute and repeat LLM calls (your
          "prompt caching" layer, done at the application level so it works with any
          provider behind OpenRouter).
Contract:
  cache_get(namespace, key_parts) -> dict | None
  cache_set(namespace, key_parts, value: dict, ttl: int) -> None
  cached(namespace, ttl)  ->  decorator that memoizes a function's JSON-able return.
Failure:  Cache is best-effort. Any RedisError or decode error is treated as a MISS
          (read) or a silent no-op (write) — the caller recomputes. The cache can never
          be the reason a request fails; it only ever makes things faster.

Key design: key = sha256 of the namespace + a stable JSON dump of key_parts. Values are
            JSON. Namespaces ("emb", "llm", "retrieval") let us flush one class of entry
            without touching the others.
"""

from __future__ import annotations

import functools
import hashlib
import json
from typing import Any, Callable

import redis

from .redis_client import get_redis

DEFAULT_TTL = 60 * 60 * 24  # 24h


def _make_key(namespace: str, key_parts: Any) -> str:
    """Stable cache key. Sorted-keys JSON so dict ordering never changes the hash."""
    blob = json.dumps(key_parts, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(f"{namespace}:{blob}".encode()).hexdigest()
    return f"cache:{namespace}:{digest}"


def cache_get(namespace: str, key_parts: Any) -> dict | None:
    """Return the cached JSON value, or None on miss / any cache error."""
    try:
        raw = get_redis().get(_make_key(namespace, key_parts))
        return json.loads(raw) if raw is not None else None
    except (redis.RedisError, json.JSONDecodeError, TypeError):
        return None


def cache_set(namespace: str, key_parts: Any, value: dict, ttl: int = DEFAULT_TTL) -> None:
    """Store a JSON-able value under the input hash. Silent no-op on any cache error."""
    try:
        payload = json.dumps(value, default=str).encode()
        get_redis().set(_make_key(namespace, key_parts), payload, ex=ttl)
    except (redis.RedisError, TypeError):
        pass  # best-effort: a failed write just means a future miss


def cached(namespace: str, ttl: int = DEFAULT_TTL) -> Callable:
    """Memoize a function on its (args, kwargs). Return value must be JSON-able.

    Usage:
        @cached("llm", ttl=3600)
        def complete(prompt: str, model: str) -> dict: ...
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key_parts = {"fn": fn.__name__, "args": args, "kwargs": kwargs}
            hit = cache_get(namespace, key_parts)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            cache_set(namespace, key_parts, result, ttl=ttl)
            return result

        return wrapper

    return decorator
