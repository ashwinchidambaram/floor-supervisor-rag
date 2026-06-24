"""abstain — emit a fully deterministic, honest abstention.

Role:     TERMINAL node. The system found no grounded documentation for the question
          (all sub-questions landed LOW, or every retrieved chunk failed the judge).
          Never fabricates content or citations. Tells the supervisor exactly which
          sources were attempted so they can consult the right SME or document.
Contract: reads  current_turn (with sub_questions, each carrying routed_source)
          writes current_turn.answer_text  — templated honest message, sources-specific
                 current_turn.status       → ABSTAINED
                 current_turn.turn_confidence → LOW
          TERMINAL: appends current_turn to state.turns (state design decision #2).
          Deterministic. Always succeeds — no failure path; callers never reach here on
          a None current_turn (graph routes only valid turns here), but we guard anyway.
Failure:  None — this node cannot fail; any guard path writes a safe fallback and still
          appends the turn so the conversation record is complete.
"""

from __future__ import annotations

from src.observability import traced_node
from src.state import (
    ConfidenceLevel,
    ConversationState,
    DocSource,
    TurnStatus,
)

# Human-readable labels for each source — used in the message template.
_SOURCE_LABELS: dict[DocSource, str] = {
    DocSource.SAFETY_PROCEDURES: "Safety Procedures",
    DocSource.MAINTENANCE_MANUALS: "Maintenance Manuals",
    DocSource.QUALITY_CONTROL: "Quality Control Standards",
}

def _build_abstain_message(attempted_sources: list[DocSource]) -> str:
    """Deterministic template. Names the specific sources that were searched (if any known),
    so the supervisor knows where the system looked and where to go next. Invents nothing."""
    known = [s for s in attempted_sources if s != DocSource.UNKNOWN]
    if not known:
        # All sub-questions had UNKNOWN routing — no search was attempted at all.
        return (
            "I was unable to answer your question: the system could not identify a "
            "relevant documentation source for any part of your query. "
            "Please consult your subject-matter expert directly."
        )

    # Deduplicate while preserving insertion order.
    seen: set[DocSource] = set()
    unique: list[DocSource] = []
    for s in known:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    source_list = ", ".join(_SOURCE_LABELS[s] for s in unique)
    return (
        f"I was unable to find grounded documentation to answer your question. "
        f"I searched the following source(s): {source_list}. "
        f"No retrieved passages were judged sufficient to support a confident, cited answer. "
        f"Please consult the relevant documentation directly or raise this with your "
        f"subject-matter expert."
    )


@traced_node("abstain", deterministic=True)
def abstain(state: ConversationState, span) -> ConversationState:
    turn = state.current_turn

    # Guard: should never be None when the graph routes here, but be safe.
    if turn is None:
        span.note(
            "abstain_no_turn",
            before={},
            after={"status": "ABSTAINED"},
            detail="abstain called with no current_turn — nothing to append",
        )
        return state

    # Collect the attempted sources from sub-questions, preserving order.
    attempted: list[DocSource] = [sq.routed_source for sq in turn.sub_questions]

    # Build the deterministic message — specific to what was tried.
    message = _build_abstain_message(attempted)

    # Stamp the turn.
    turn.answer_text = message
    turn.status = TurnStatus.ABSTAINED
    turn.turn_confidence = ConfidenceLevel.LOW

    # Audit the decision with before/after.
    span.note(
        "abstain_turn",
        before={"status": turn.status.value, "answer_text": None},
        after={
            "status": TurnStatus.ABSTAINED.value,
            "turn_confidence": ConfidenceLevel.LOW.value,
            "attempted_sources": [s.value for s in attempted],
        },
        detail=(
            f"abstained on turn {turn.turn_id}; "
            f"attempted_sources=[{', '.join(s.value for s in attempted)}]"
        ),
    )
    span.delta = {
        "status": TurnStatus.ABSTAINED.value,
        "turn_confidence": ConfidenceLevel.LOW.value,
    }

    # TERMINAL: append to persisted history (state design decision #2). Keep current_turn SET —
    # the node-template wrapper reads current_turn.status AFTER this returns to stamp the event,
    # and the next invocation overwrites current_turn with the new question.
    state.turns.append(turn)

    return state
