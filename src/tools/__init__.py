# Tool implementations, mocked behind clean interfaces. Typed inputs/outputs + explicit error surface.

from .cache import cache_get, cache_set, cached
from .embeddings import DIM, embed_query, embed_texts
from .redis_client import get_redis, ping
from .vector_store import Hit, VectorStore

__all__ = [
    "cache_get",
    "cache_set",
    "cached",
    "DIM",
    "embed_query",
    "embed_texts",
    "get_redis",
    "ping",
    "Hit",
    "VectorStore",
]
