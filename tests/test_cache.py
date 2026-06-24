"""Cache behaviour (spec §4b) — the per-node response cache for retrieve_chunks / assemble_answer.

These assert the cost-relevant guarantee: an identical assemble request is served from cache on the
second call (no second LLM call), the cached part prices to $0, and cost_avoided is tracked. Requires
a live Redis; skipped otherwise (CI runs Redis-less, where the cache safely no-ops).
"""

from __future__ import annotations

import pytest

from src.state import DocSource, ElementType, RetrievedChunk


def _redis_or_skip():
    from src.tools.redis_client import get_redis

    try:
        get_redis().ping()
    except Exception:
        pytest.skip("redis unavailable — node cache no-ops without it")


def _chunk(chunk_id: str = "c1") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        source=DocSource.MAINTENANCE_MANUALS,
        doc_title="Maintenance Manual",
        doc_version="v5.4",
        section="Section 4 — Torque",
        element_type=ElementType.PROSE,
        text="Tighten the vise jaw bolts to 80 N·m.",
        score=0.9,
    )


def test_assemble_second_call_served_from_cache(monkeypatch):
    """Same (subq, supporting chunks) → 2nd assemble is a cache hit: no LLM call, $0, cost_avoided>0."""
    monkeypatch.setenv("RAG_DISABLE_NODE_CACHE", "0")
    _redis_or_skip()

    from src.nodes import assemble_answer as aa
    from src.tools import cache as cache_mod

    cache_mod.flush_namespace("llm:assemble")
    cache_mod.reset_stats()

    calls = {"n": 0}

    def fake_complete(agent_key, messages, temperature=0):
        calls["n"] += 1
        return "Tighten to 80 N·m.", {
            "tokens_in": 120,
            "tokens_out": 40,
            "model": "anthropic/claude-sonnet-4.6",
        }

    monkeypatch.setattr(aa, "complete_with_usage", fake_complete)

    chunks = [_chunk("c1")]
    msgs = [{"role": "user", "content": "torque?"}]

    d1, u1, hit1 = aa._assemble_cached("assemble_answer", "what torque?", chunks, msgs)
    d2, u2, hit2 = aa._assemble_cached("assemble_answer", "what torque?", chunks, msgs)

    assert calls["n"] == 1, "second identical request must not call the model"
    assert hit1 is False and hit2 is True
    assert d1 == d2 == "Tighten to 80 N·m."
    assert u2["tokens_in"] == 0 and u2["tokens_out"] == 0, "cache hit prices to $0"

    stats = cache_mod.cache_stats()["llm:assemble"]
    assert stats["hits"] >= 1
    assert stats["cost_avoided_usd"] > 0


def test_node_cache_disabled_bypasses_cache(monkeypatch):
    """With RAG_DISABLE_NODE_CACHE=1 (the suite default) the model is called every time."""
    monkeypatch.setenv("RAG_DISABLE_NODE_CACHE", "1")
    from src.nodes import assemble_answer as aa

    calls = {"n": 0}

    def fake_complete(agent_key, messages, temperature=0):
        calls["n"] += 1
        return "x", {"tokens_in": 1, "tokens_out": 1, "model": "anthropic/claude-sonnet-4.6"}

    monkeypatch.setattr(aa, "complete_with_usage", fake_complete)
    chunks = [_chunk("c1")]
    msgs = [{"role": "user", "content": "q"}]
    aa._assemble_cached("assemble_answer", "q", chunks, msgs)
    _, _, hit = aa._assemble_cached("assemble_answer", "q", chunks, msgs)
    assert calls["n"] == 2 and hit is False
