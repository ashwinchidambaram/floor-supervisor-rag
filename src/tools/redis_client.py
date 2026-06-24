"""Redis connection — the single place a Redis handle is created.

Role:     Hand out a shared, lazily-initialized Redis client.
Contract: get_redis() -> redis.Redis  (decode_responses=False; we store bytes for vectors).
Failure:  Connection errors surface on first command, not at import. Callers that
          treat Redis as a *cache* (see cache.py) swallow these and degrade to a miss,
          so a dead Redis never takes the system down — it just removes the speedup.

Config:   REDIS_URL env var (default redis://localhost:6379/0).
"""

from __future__ import annotations

import os
from functools import lru_cache

import redis

_DEFAULT_URL = "redis://localhost:6379/0"


def redis_url() -> str:
    """The Redis URL, read lazily so it reflects .env loaded by config (import-order safe).
    Treats an empty/whitespace value (e.g. `REDIS_URL=` in .env) as unset → the local default,
    so a blank slot in .env can never produce an invalid-scheme URL."""
    return (os.getenv("REDIS_URL") or "").strip() or _DEFAULT_URL


# Back-compat constant for any module that imports it (best-effort snapshot).
REDIS_URL = redis_url()


@lru_cache(maxsize=1)
def get_redis() -> redis.Redis:
    """Return a process-wide Redis client (pooled internally by redis-py)."""
    return redis.from_url(redis_url(), decode_responses=False)


def ping() -> bool:
    """Cheap liveness probe. True if Redis answers, False on any connection error."""
    try:
        return bool(get_redis().ping())
    except redis.RedisError:
        return False
