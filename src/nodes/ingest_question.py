"""ingest_question — open/validate the turn for a new supervisor question.

Role:     Validate the incoming question and stamp the turn RECEIVED. This is the input
          guardrail at the front of the pipeline.
Contract: reads  current_turn (set by the caller with question_text).
          writes current_turn.status = RECEIVED (or FAILED on bad input). Does NOT append to
          `turns` — terminal nodes (deliver_answer / abstain) own that (state design decision #2).
Failure:  empty or oversized input -> status FAILED + a safe summary; the graph routes FAILED
          to abstain. Never raises.

THIS FILE IS THE NODE PATTERN every node follows: a pure `fn(state, span) -> state`, decorated
with @traced_node so it inherits emit/audit/cost/safe-degrade. Match this shape exactly.
"""

from __future__ import annotations

from src.observability import traced_node
from src.state import ConversationState, TurnStatus

_MAX_QUESTION_CHARS = 2000


@traced_node("ingest_question", deterministic=True)
def ingest_question(state: ConversationState, span) -> ConversationState:
    turn = state.current_turn
    text = (turn.question_text if turn else "").strip()

    if turn is None or not text:
        if turn is not None:
            turn.status = TurnStatus.FAILED
            turn.answer_text = "No question was received. Please ask a question."
        span.note("reject_empty_input", before={"question_len": len(text)}, after={"status": "FAILED"},
                  detail="empty input → FAILED")
        return state

    if len(text) > _MAX_QUESTION_CHARS:
        turn.status = TurnStatus.FAILED
        turn.answer_text = "That question is too long. Please shorten it and ask again."
        span.note("reject_oversized_input", before={"question_len": len(text)},
                  after={"status": "FAILED"}, detail=f"{len(text)} chars > {_MAX_QUESTION_CHARS} → FAILED")
        return state

    turn.status = TurnStatus.RECEIVED
    span.delta = {"status": "RECEIVED"}
    span.note("open_turn", before={}, after={"turn_id": turn.turn_id, "status": "RECEIVED"},
              detail=f"turn opened ({len(text)} chars)")
    return state
