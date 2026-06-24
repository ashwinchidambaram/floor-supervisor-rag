"""route_sources — validate proposed sources and set routed_source per sub-question.

Role:     Deterministic guard between decompose_question (LLM) and retrieve_chunks.
          The LLM proposes a source per sub-question; this node validates each
          proposal against the DocSource enum and locks in the routed_source. An
          invalid or UNKNOWN proposed_source stays UNKNOWN — never silently invented.
Contract: reads  current_turn.sub_questions[].proposed_source (set by decompose_question).
          writes sub_questions[].routed_source: known source → proposed_source;
                 UNKNOWN / anything unrecognised → DocSource.UNKNOWN.
          writes current_turn.status = ROUTED.
          Does NOT retrieve and does NOT log knowledge gaps — UNKNOWN sub-questions are
          left with routed_source=UNKNOWN; the graph edge skips them from retrieval and
          assess_confidence logs the gap downstream.
Failure:  no sub_questions → status ROUTED with empty routing summary (safe no-op);
          any unexpected error → traced_node wrapper marks FAILED and records the error.
"""

from __future__ import annotations

from collections import Counter

from src.observability import traced_node
from src.state import ConversationState, DocSource, TurnStatus

# The set of sources that are valid retrieval targets (all DocSource values except UNKNOWN).
_KNOWN_SOURCES: frozenset[DocSource] = frozenset(
    s for s in DocSource if s is not DocSource.UNKNOWN
)


@traced_node("route_sources", deterministic=True)
def route_sources(state: ConversationState, span) -> ConversationState:
    turn = state.current_turn

    # No active turn — nothing to route; treat as a safe no-op.
    if turn is None:
        span.note(
            "route_sources_no_turn",
            before={},
            after={"status": "ROUTED"},
            detail="no current_turn; nothing to route",
        )
        return state

    routed_counts: Counter[str] = Counter()  # source_name -> count of sub-qs routed there
    unknown_count = 0

    for sq in turn.sub_questions:
        if sq.proposed_source in _KNOWN_SOURCES:
            sq.routed_source = sq.proposed_source
            routed_counts[sq.proposed_source.value] += 1
        else:
            # UNKNOWN proposed_source (or any value not in the known-sources set) → UNKNOWN.
            # We never invent a source. assess_confidence will record the gap downstream.
            sq.routed_source = DocSource.UNKNOWN
            unknown_count += 1

    turn.status = TurnStatus.ROUTED

    # Build a compact routing summary for the audit trail.
    routed_summary = dict(routed_counts)
    detail = (
        f"routed {sum(routed_counts.values())} sub-q(s) to known sources "
        f"{routed_summary}; {unknown_count} UNKNOWN (skipped from retrieval)"
    )

    span.note(
        action="route_sources",
        before={"sub_questions": [sq.id for sq in turn.sub_questions]},
        after={
            "routed": routed_summary,
            "unknown_count": unknown_count,
            "status": TurnStatus.ROUTED.value,
        },
        detail=detail,
    )
    span.delta = {
        "routed": routed_summary,
        "unknown_count": unknown_count,
        "status": TurnStatus.ROUTED.value,
    }

    return state
