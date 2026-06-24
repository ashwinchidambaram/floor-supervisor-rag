"""deliver_answer — the hard citation + honesty guarantee (terminal node).

Role:     Stand behind only what is grounded. Enforce ≥1 citation per HIGH/MEDIUM fragment;
          downgrade any uncited fragment to LOW; stitch DETERMINISTIC uncertainty lines for LOW
          parts; set the final turn status + confidence. The LLM never bypasses either guarantee.
Contract: reads current_turn.{sub_questions[].confidence/supporting_chunk_ids, answer_text (assembled
          grounded fragments), citations[]}. Writes final current_turn.answer_text, turn_confidence,
          status ANSWERED / ANSWERED_PARTIAL; appends the finished turn to state.turns (decision #2).
Failure / routing: if NO grounded part survives citation enforcement, it leaves status non-terminal
          (still ASSEMBLED, set by assemble_answer) and does NOT append — the graph edge then routes to `abstain`.

Citation rule: a HIGH/MEDIUM sub-question is "cited" iff some Citation.chunk_id ∈ its
          supporting_chunk_ids. No overlap → downgrade that part to LOW (never delivered as fact).
"""

from __future__ import annotations

from src.observability import traced_node
from src.state import ConfidenceLevel, ConversationState, DocSource, TurnStatus

_RANK = {ConfidenceLevel.LOW: 0, ConfidenceLevel.MEDIUM: 1, ConfidenceLevel.HIGH: 2}
_SOURCE_LABEL = {
    DocSource.SAFETY_PROCEDURES: "the safety procedures",
    DocSource.MAINTENANCE_MANUALS: "the maintenance manual",
    DocSource.QUALITY_CONTROL: "the quality-control standards",
    DocSource.UNKNOWN: "the relevant documentation or your supervisor / SME",
}


@traced_node("deliver_answer", deterministic=True)
def deliver_answer(state: ConversationState, span) -> ConversationState:
    turn = state.current_turn
    if turn is None:
        return state

    cited_ids = {c.chunk_id for c in turn.citations}

    # 1. Citation enforcement: a HIGH/MEDIUM part with no supporting citation → LOW.
    for sq in turn.sub_questions:
        if sq.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
            if not (set(sq.supporting_chunk_ids) & cited_ids):
                sq.confidence = ConfidenceLevel.LOW

    grounded = [sq for sq in turn.sub_questions
                if sq.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM)]
    low = [sq for sq in turn.sub_questions if sq.confidence == ConfidenceLevel.LOW]

    # 2. Nothing grounded survives → hand off to abstain (don't finalize, don't append).
    if not grounded:
        turn.turn_confidence = ConfidenceLevel.LOW
        span.note("deliver_answer", before={}, after={"grounded": 0},
                  detail="no grounded part survived citation enforcement → abstain")
        span.delta = {"grounded": 0}
        return state

    # 3. Compose: assembled grounded text + deterministic caveats/uncertainty lines.
    parts: list[str] = []
    if turn.answer_text and turn.answer_text.strip():
        parts.append(turn.answer_text.strip())
    for sq in grounded:
        if sq.confidence == ConfidenceLevel.MEDIUM:  # MEDIUM → explicit "verify against §X" caveat
            parts.append(f'⚠︎ Evidence for "{sq.text}" is partial — verify against the cited section.')
    for sq in low:  # honest, templated, never fabricated
        parts.append(f'⚠︎ Regarding "{sq.text}": I don\'t have grounded documentation to answer '
                     f'this — please consult {_SOURCE_LABEL.get(sq.routed_source, _SOURCE_LABEL[DocSource.UNKNOWN])}.')
    turn.answer_text = "\n\n".join(parts)

    # 4. Finalize: min confidence, partial iff any LOW part remains; terminal append to history.
    confidences = [sq.confidence for sq in turn.sub_questions if sq.confidence is not None]
    turn.turn_confidence = min(confidences, key=lambda lvl: _RANK[lvl], default=ConfidenceLevel.LOW)
    turn.status = TurnStatus.ANSWERED_PARTIAL if low else TurnStatus.ANSWERED
    state.turns.append(turn)
    span.note("deliver_answer", before={}, after={"status": turn.status.value,
              "grounded": len(grounded), "low": len(low)},
              detail=f"{turn.status.value}: {len(grounded)} grounded, {len(low)} low")
    span.delta = {"status": turn.status.value}
    return state
