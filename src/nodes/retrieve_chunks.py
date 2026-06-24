"""retrieve_chunks — hybrid (dense + BM25) retrieval for known-source sub-questions.

Role:     For each sub-question whose source was successfully routed AND whose current
          evidence hasn't passed the judge (or hasn't been tried yet), call hybrid_search
          to fetch the top-k chunks from the right system of record. Increments
          `retrieval_attempts` on every call so the retry-loop cap (`max_retrieval_loops`)
          is enforced by the conditional edge in graph.py, not here.
Contract: in  → state.current_turn.sub_questions[]:
                  routed_source != UNKNOWN   → will be (re)retrieved if also needs retrieval
                  routed_source == UNKNOWN   → SKIPPED (empty retrieved, no attempt increment)
                  judge_verdict == PASS      → SKIPPED (already passed; no re-retrieve)
                  retrieval_attempts >= config.max_retrieval_loops → SKIPPED (cap; edge handles)
          out → sq.retrieved filled with list[RetrievedChunk] ([] on empty index / embed error)
                sq.retrieval_attempts incremented for every sub-q that was attempted
                current_turn.status = RETRIEVED
          cost_usd = 0.0  (deterministic: embed call is in the tool; we emit $0 at the node level)
Failure:  hybrid_search never raises (returns [] on EMPTY_INDEX or EMBED_ERROR — see contract).
          A [] result is legitimate empty evidence, not a crash: the judge will FAIL it and
          assess_confidence will record a LOW + KnowledgeGap.  This node degrades, never crashes.
"""

from __future__ import annotations

from src.observability import traced_node
from src.state import ConversationState, DocSource, JudgeVerdict, RetrievedChunk, TurnStatus
from src.tools.cache import cache_get, cache_set, node_cache_enabled
from src.tools.hybrid_search import hybrid_search, index_fingerprint


def _retrieve(query_text: str, source: DocSource, top_k: int, fp: str) -> tuple[list[RetrievedChunk], bool]:
    """hybrid_search behind the spec-§4b retrieval cache. Deterministic, so a hit saves latency
    (the cost is $0 either way). Key = (subq, source, top_k, index fingerprint). Returns
    (chunks, was_cache_hit). Best-effort: any cache error just recomputes."""
    if not node_cache_enabled():
        return hybrid_search(query_text=query_text, source=source, top_k=top_k), False
    key = {"subq": query_text, "source": source.value, "top_k": top_k, "fp": fp}
    cached = cache_get("retrieval", key)
    if cached is not None:
        return [RetrievedChunk.model_validate(c) for c in cached["chunks"]], True
    results = hybrid_search(query_text=query_text, source=source, top_k=top_k)
    cache_set("retrieval", key, {"chunks": [c.model_dump(mode="json") for c in results]})
    return results, False


@traced_node("retrieve_chunks", deterministic=True)
def retrieve_chunks(state: ConversationState, span) -> ConversationState:
    turn = state.current_turn
    if turn is None:
        span.note(
            "no_active_turn",
            before={},
            after={"status": "FAILED"},
            detail="retrieve_chunks called with no current_turn",
        )
        return state

    top_k = state.config.top_k
    max_loops = state.config.max_retrieval_loops

    # Collect sub-questions that need (re)retrieval this pass:
    #   (a) routed_source is known  — UNKNOWN sources are never searched (routing invariant)
    #   (b) judge has not passed    — PASS means we already have good evidence, skip
    #   (c) under the attempt cap   — the graph edge enforces the cap, but we skip defensively here
    to_retrieve = [
        sq
        for sq in turn.sub_questions
        if sq.routed_source != DocSource.UNKNOWN
        and sq.judge_verdict != JudgeVerdict.PASS
        and sq.retrieval_attempts < max_loops
    ]

    # Per-sub-question stats for the audit summary (populated below).
    audit_rows: list[str] = []
    fp = index_fingerprint() if to_retrieve and node_cache_enabled() else ""

    for sq in to_retrieve:
        results, was_cached = _retrieve(sq.text, sq.routed_source, top_k, fp)
        if was_cached:
            span.cache_hit = True
        sq.retrieved = results
        sq.retrieval_attempts += 1  # counted regardless of cache (enforces the retry cap)

        # Audit summary row: sq id · #hits · top score (or "empty").
        if results:
            top_score = max(c.score for c in results)
            audit_rows.append(
                f"sq={sq.id} hits={len(results)} top_score={top_score:.3f} "
                f"(attempt {sq.retrieval_attempts}/{max_loops})"
            )
        else:
            audit_rows.append(
                f"sq={sq.id} hits=0 EMPTY (attempt {sq.retrieval_attempts}/{max_loops})"
            )

    # Capture prior status BEFORE mutating, so the audit before/after is a real transition.
    prior_status = turn.status.value if turn else "NONE"
    turn.status = TurnStatus.RETRIEVED

    # Build the span note — what the audit log and event summary will carry.
    attempted_ids = [sq.id for sq in to_retrieve]
    skipped_unknown = [
        sq.id for sq in turn.sub_questions if sq.routed_source == DocSource.UNKNOWN
    ]
    skipped_passed = [
        sq.id
        for sq in turn.sub_questions
        if sq.judge_verdict == JudgeVerdict.PASS
        and sq.routed_source != DocSource.UNKNOWN
    ]
    skipped_at_cap = [
        sq.id
        for sq in turn.sub_questions
        if sq.routed_source != DocSource.UNKNOWN
        and sq.judge_verdict != JudgeVerdict.PASS
        and sq.retrieval_attempts >= max_loops
    ]

    detail_lines = audit_rows or ["no sub-questions needed retrieval this pass"]
    if skipped_unknown:
        detail_lines.append(f"skipped UNKNOWN: {skipped_unknown}")
    if skipped_passed:
        detail_lines.append(f"skipped PASS (already grounded): {skipped_passed}")
    if skipped_at_cap:
        detail_lines.append(f"skipped AT_CAP: {skipped_at_cap}")

    detail = " | ".join(detail_lines)

    span.delta = {
        "status": TurnStatus.RETRIEVED.value,
        "attempted": attempted_ids,
        "skipped_unknown": skipped_unknown,
    }
    span.note(
        action="retrieve_chunks",
        before={"turn_status": prior_status},
        after={
            "turn_status": TurnStatus.RETRIEVED.value,
            "attempted": attempted_ids,
        },
        detail=detail,
    )

    return state
