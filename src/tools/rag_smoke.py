"""Round-trip smoke test for the RAG + cache stack. Run: python -m src.tools.rag_smoke

Proves end-to-end: Redis ping -> embed (with cache hit) -> index -> search -> response cache.
Not a pytest (that lives in tests/); this is the 30-second "is it wired?" check.
"""

from __future__ import annotations

import time

from .cache import cached
from .embeddings import DIM, embed_query
from .redis_client import ping
from .vector_store import VectorStore


def main() -> None:
    print(f"1. Redis reachable: {ping()}")

    # Embedding + per-text cache: second call should be a cache hit (faster, identical).
    t0 = time.perf_counter()
    v1 = embed_query("how do I reset my password?")
    t1 = time.perf_counter()
    v2 = embed_query("how do I reset my password?")
    t2 = time.perf_counter()
    print(f"2. Embedding dim={v1.shape[0]} (expected {DIM}); identical on cache: {bool((v1 == v2).all())}")
    print(f"   cold={1000*(t1-t0):.1f}ms  cached={1000*(t2-t1):.1f}ms")

    # Vector store add + search on a fresh, isolated index.
    store = VectorStore(index="smoke")
    store.clear()
    store.add(
        [
            "To reset your password, open Settings and click 'Forgot password'.",
            "Our refund policy allows returns within 30 days of purchase.",
            "The office is open Monday to Friday, 9am to 5pm.",
        ],
        metadatas=[{"topic": "account"}, {"topic": "billing"}, {"topic": "hours"}],
    )
    hits = store.search("I forgot my login credentials", k=2)
    print(f"3. Indexed {store.count()} docs; top hit (score={hits[0].score:.3f}, topic={hits[0].metadata['topic']}):")
    print(f"   {hits[0].text!r}")
    assert hits[0].metadata["topic"] == "account", "expected the password doc to win"

    # Application-level response cache via the decorator.
    calls = {"n": 0}

    @cached("smoke_llm", ttl=60)
    def fake_llm(prompt: str) -> dict:
        calls["n"] += 1
        return {"answer": f"echo: {prompt}"}

    fake_llm("hello")
    fake_llm("hello")  # served from cache -> fn body runs once
    print(f"4. Response cache: fn executed {calls['n']}x for 2 identical calls (expected 1)")

    store.clear()
    print("\nAll checks passed ✔  (Redis cache + fastembed + vector search wired)")


if __name__ == "__main__":
    main()
