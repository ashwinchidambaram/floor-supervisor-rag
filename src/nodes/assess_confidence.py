"""assess_confidence — the deterministic confidence decision (+ knowledge-gap logging).

Role:     Decide HIGH/MEDIUM/LOW per sub-question from signals the LLM CANNOT fake — retrieval
          score, the judge's verdict + typed failure mode, and citation (judged-chunk) coverage.
          This is the defensible heart of the agency line: a model never decides its own confidence.
Contract: reads sub_questions[].{routed_source, judge_verdict, judge_failure_mode, supporting_chunk_ids,
          retrieved[].score}; writes sub_questions[].confidence, current_turn.turn_confidence (= MIN
          across parts), appends a KnowledgeGap per LOW/UNKNOWN part; status → ASSESSED.
Failure:  any missing signal → conservative LOW (never an optimistic guess).

Confidence mapping (spec §6), evaluated in priority order:
  UNKNOWN source                         → LOW  (gap NO_SOURCE_MATCHED)
  judge FAIL, value-not-found            → LOW  (gap VALUE_NOT_FOUND)
  judge FAIL, otherwise (at retry cap)   → LOW  (gap JUDGE_FAIL_AT_CAP)
  no chunk ≥ min_score_floor             → LOW  (gap LOW_RETRIEVAL)
  judge PASS + top ≥ high_floor + cover  → HIGH
  judge PASS but weak score / partial    → MEDIUM
"""

from __future__ import annotations

from src.observability import record_gap, traced_node
from src.state import (
    ConfidenceLevel,
    ConversationState,
    DocSource,
    GapReason,
    JudgeFailureMode,
    JudgeVerdict,
    KnowledgeGap,
    SubQuestion,
    TurnStatus,
)

# MIN over a multi-part answer: a turn is only as trustworthy as its weakest part.
_RANK = {ConfidenceLevel.LOW: 0, ConfidenceLevel.MEDIUM: 1, ConfidenceLevel.HIGH: 2}


def _decide(sq: SubQuestion, top_score: float, high_floor: float, min_floor: float
            ) -> tuple[ConfidenceLevel, GapReason | None]:
    """Pure mapping from a sub-question's signals to (confidence, gap-reason-if-LOW)."""
    if sq.routed_source == DocSource.UNKNOWN:
        return ConfidenceLevel.LOW, GapReason.NO_SOURCE_MATCHED
    if sq.judge_verdict == JudgeVerdict.FAIL:
        if sq.judge_failure_mode == JudgeFailureMode.VALUE_NOT_FOUND:
            return ConfidenceLevel.LOW, GapReason.VALUE_NOT_FOUND
        return ConfidenceLevel.LOW, GapReason.JUDGE_FAIL_AT_CAP
    if top_score < min_floor:
        return ConfidenceLevel.LOW, GapReason.LOW_RETRIEVAL
    if sq.judge_verdict == JudgeVerdict.PASS:
        full_coverage = bool(sq.supporting_chunk_ids)
        if top_score >= high_floor and full_coverage:
            return ConfidenceLevel.HIGH, None
        return ConfidenceLevel.MEDIUM, None  # PASS but weak score or partial coverage → caveat
    return ConfidenceLevel.LOW, GapReason.LOW_RETRIEVAL  # no verdict → conservative


@traced_node("assess_confidence", deterministic=True)
def assess_confidence(state: ConversationState, span) -> ConversationState:
    turn = state.current_turn
    if turn is None:  # no working turn → nothing to assess (wrapper still emits the event)
        return state
    cfg = state.config
    levels: list[ConfidenceLevel] = []

    for sq in turn.sub_questions:
        top_score = max((c.score for c in sq.retrieved), default=0.0)
        level, gap_reason = _decide(sq, top_score, cfg.high_score_floor, cfg.min_score_floor)
        sq.confidence = level
        levels.append(level)
        if gap_reason is not None:  # every LOW/UNKNOWN part is telemetry for the doc team
            record_gap(state, KnowledgeGap(
                turn_id=turn.turn_id, sub_question_id=sq.id, question_text=sq.text,
                attempted_source=sq.routed_source, reason=gap_reason, top_score=top_score))

    turn.turn_confidence = min(levels, key=lambda lvl: _RANK[lvl]) if levels else ConfidenceLevel.LOW
    turn.status = TurnStatus.ASSESSED
    counts = {c.value: [lv.value for lv in levels].count(c.value) for c in ConfidenceLevel}
    span.note("assess_confidence", before={}, after={"turn_confidence": turn.turn_confidence.value,
              "levels": counts}, detail=f"turn_confidence={turn.turn_confidence.value} {counts}")
    span.delta = {"turn_confidence": turn.turn_confidence.value}
    return state
