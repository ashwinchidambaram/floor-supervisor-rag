"""RAG + cache tests. Skipped automatically if Redis isn't reachable, so the suite
stays green on a machine without Redis (the modules degrade to in-memory anyway)."""

import pytest

from src.tools import DIM, VectorStore, cached, embed_query, ping

pytestmark = pytest.mark.skipif(not ping(), reason="Redis not reachable")


def test_embedding_shape_and_norm():
    v = embed_query("hello world")
    assert v.shape == (DIM,)
    assert abs(float((v * v).sum()) - 1.0) < 1e-3  # L2-normalized


def test_retrieval_ranks_relevant_doc_first():
    store = VectorStore(index="pytest")
    store.clear()
    store.add(
        ["Reset your password from the Settings page.",
         "Refunds are issued within 30 days.",
         "We are open 9 to 5 on weekdays."],
        metadatas=[{"t": "account"}, {"t": "billing"}, {"t": "hours"}],
    )
    hits = store.search("forgot my login", k=2)
    assert hits[0].metadata["t"] == "account"
    assert hits[0].score > hits[1].score
    store.clear()


def test_response_cache_executes_once():
    calls = {"n": 0}

    @cached("pytest_llm", ttl=30)
    def f(x: str) -> dict:
        calls["n"] += 1
        return {"y": x}

    f("a")
    f("a")
    assert calls["n"] == 1
