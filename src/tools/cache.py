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
import os
from typing import Any, Callable

import redis

from .redis_client import get_redis

DEFAULT_TTL = 60 * 60 * 24  # 24h


def node_cache_enabled() -> bool:
    """The per-node response caches (retrieve_chunks / assemble_answer) are gated on this so
    the §11 forced-stub tests run cache-free and deterministic. Set RAG_DISABLE_NODE_CACHE=1
    to turn them off (the test conftest does this). The embedding + table caches are unaffected."""
    return os.getenv("RAG_DISABLE_NODE_CACHE", "") != "1"


# --- lightweight in-process instrumentation (per-namespace hit/miss + cost avoided) ---------
# Process-local counters: enough to ground the README's measured run and to drive the Knowledge
# cache band locally. The deployed demo runs Redis-less, so its band reads recorded fixtures.
_STATS: dict[str, dict[str, float]] = {}


def _bump(namespace: str, field: str, by: float = 1) -> None:
    _STATS.setdefault(namespace, {"hits": 0, "misses": 0, "cost_avoided_usd": 0.0})[field] += by


def record_cost_avoided(namespace: str, usd: float) -> None:
    """A cache hit on a priced node (e.g. assemble) avoided this much spend — track it for the band."""
    _bump(namespace, "cost_avoided_usd", usd)


def cache_stats() -> dict[str, dict[str, float]]:
    """Per-namespace {hits, misses, hit_rate, cost_avoided_usd}. Process-local since last reset."""
    out: dict[str, dict[str, float]] = {}
    for ns, s in _STATS.items():
        total = s["hits"] + s["misses"]
        out[ns] = {**s, "hit_rate": (s["hits"] / total if total else 0.0)}
    return out


def reset_stats() -> None:
    """Zero the counters (used by the measured run + cache tests)."""
    _STATS.clear()


def flush_namespace(namespace: str) -> int:
    """Delete every entry under one namespace. Returns the count removed (0 on any cache error)."""
    try:
        r = get_redis()
        keys = list(r.scan_iter(match=f"cache:{namespace}:*"))
        return r.delete(*keys) if keys else 0
    except redis.RedisError:
        return 0


def _make_key(namespace: str, key_parts: Any) -> str:
    """Stable cache key. Sorted-keys JSON so dict ordering never changes the hash."""
    blob = json.dumps(key_parts, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(f"{namespace}:{blob}".encode()).hexdigest()
    return f"cache:{namespace}:{digest}"


def cache_get(namespace: str, key_parts: Any) -> dict | None:
    """Return the cached JSON value, or None on miss / any cache error. Records a hit/miss."""
    try:
        raw = get_redis().get(_make_key(namespace, key_parts))
        if raw is not None:
            _bump(namespace, "hits")
            return json.loads(raw)
        _bump(namespace, "misses")
        return None
    except (redis.RedisError, json.JSONDecodeError, TypeError):
        _bump(namespace, "misses")
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
