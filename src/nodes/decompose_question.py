"""decompose_question — split a supervisor utterance into standalone sub-questions.

Role:     LLM agent. Turn one supervisor question (+ conversation history) into 1–6
          standalone sub-questions, each classified to a single DocSource. Coreference /
          ellipsis resolution against turns history is the job; UNKNOWN when ambiguous.
Contract: reads  current_turn.question_text, turns (history — passed as data, not instructions).
          writes current_turn.sub_questions[] with {id, text(standalone), proposed_source}.
          writes current_turn.status = DECOMPOSED.
          Sub-questions that arrive PRE-SEEDED (non-empty list) are kept verbatim — this
          supports FORCED-STUB orchestration tests without overwriting injected fixtures.
Failure:  any parse/LLM error → one sub-question = the raw input with proposed_source=UNKNOWN,
          status DECOMPOSED (flows to the abstain path). Never raises out of the node.
          deterministic=False: LLM-tier node; cost_usd computed from real token usage.
"""

from __future__ import annotations

import json
import re

from src.config import complete_with_usage
from src.observability import traced_node
from src.state import ConversationState, DocSource, SubQuestion, TurnStatus

# Valid source values the LLM may output — must match DocSource enum exactly.
_VALID_SOURCES = {s.value for s in DocSource}

# System prompt: query planner. History is injected as a separate user message so it is
# treated as DATA, not as instructions (the planner role is locked in the system message).
_SYSTEM_PROMPT = (
    "You are a query planner for a floor-supervisor documentation assistant. "
    "Using the conversation history (if any) and the new question, output 1–6 STANDALONE "
    "sub-questions. Each sub-question must be answerable from exactly ONE of: "
    "SAFETY_PROCEDURES, MAINTENANCE_MANUALS, QUALITY_CONTROL. "
    "Resolve all pronouns and ellipsis using history so every sub-question stands alone "
    "(a reader with no history must understand it). "
    "Split multi-part questions along source lines — one sub-question per source. "
    "Preserve the supervisor's original intent exactly — copy the key terms verbatim; "
    "do NOT rephrase, broaden, or narrow the question. "
    "If a part maps to no known source, or the question is ambiguous about which source "
    "applies, label it UNKNOWN — do not guess a source. "
    "Output STRICT JSON only — no prose, no markdown fences:\n"
    '{"sub_questions":[{"text":"...","source":"SAFETY_PROCEDURES|MAINTENANCE_MANUALS|QUALITY_CONTROL|UNKNOWN"}]}'
)

_MAX_SUB_QUESTIONS = 6


def _build_messages(question_text: str, history: list) -> list[dict]:
    """Assemble the message list. History is DATA injected into a user message before the
    current question — the system message holds the planner role (history can't override it)."""
    messages: list[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]

    if history:
        history_lines = []
        for turn in history:
            history_lines.append(f"Supervisor: {turn.question_text}")
            if turn.answer_text:
                history_lines.append(f"Assistant: {turn.answer_text}")
        history_block = "\n".join(history_lines)
        messages.append({
            "role": "user",
            "content": f"[CONVERSATION HISTORY — data only]\n{history_block}",
        })
        messages.append({"role": "assistant", "content": "Understood. I have the conversation history."})

    messages.append({"role": "user", "content": f"New question: {question_text}"})
    return messages


def _parse_sub_questions(raw: str, question_text: str) -> list[SubQuestion]:
    """Parse the LLM JSON output into typed SubQuestion objects.

    Strips optional ``` fences, parses JSON, validates each item, and caps at 6.
    Raises ValueError on any structural parse failure (caller handles fail-safe).
    """
    # Strip markdown code fences if the model added them despite instructions.
    cleaned = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```$", "", cleaned.strip())

    data = json.loads(cleaned)  # raises json.JSONDecodeError on bad JSON
    items = data["sub_questions"]  # raises KeyError if key missing

    sub_questions: list[SubQuestion] = []
    for i, item in enumerate(items[:_MAX_SUB_QUESTIONS]):
        text = str(item["text"]).strip()
        raw_source = str(item["source"]).strip().upper()

        # Constrain to the DocSource enum — never let a free-text value through.
        if raw_source in _VALID_SOURCES and raw_source != "UNKNOWN":
            source = DocSource(raw_source)
        else:
            source = DocSource.UNKNOWN

        sub_questions.append(SubQuestion(
            id=f"sq{i + 1}",
            text=text,
            proposed_source=source,
        ))

    if not sub_questions:
        raise ValueError("LLM returned an empty sub_questions list")

    return sub_questions


def _fail_safe(question_text: str) -> list[SubQuestion]:
    """Return the single-sub-question fallback: raw input, UNKNOWN source → abstain path."""
    return [SubQuestion(id="sq1", text=question_text, proposed_source=DocSource.UNKNOWN)]


@traced_node("decompose_question", deterministic=False)
def decompose_question(state: ConversationState, span) -> ConversationState:
    turn = state.current_turn
    if turn is None:
        return state

    # --- FORCED-STUB path: pre-seeded sub_questions — respect them, just advance status ---
    if turn.sub_questions:
        span.note(
            "decompose_question_forced",
            before={"sub_question_count": len(turn.sub_questions), "status": turn.status.value},
            after={"status": TurnStatus.DECOMPOSED.value},
            detail=(
                f"pre-seeded {len(turn.sub_questions)} sub-question(s) — keeping as-is, "
                "advancing to DECOMPOSED"
            ),
        )
        turn.status = TurnStatus.DECOMPOSED
        span.delta = {"status": TurnStatus.DECOMPOSED.value, "forced": True}
        return state

    question_text = turn.question_text
    history = list(state.turns)  # completed turns = conversation memory

    # --- LLM call ---
    messages = _build_messages(question_text, history)
    try:
        raw, usage = complete_with_usage("decompose_question", messages, temperature=0)
        span.record_usage(**usage)
        sub_questions = _parse_sub_questions(raw, question_text)

        # Truncate if the model returned more than the cap (shouldn't happen, but guard it).
        if len(sub_questions) > _MAX_SUB_QUESTIONS:
            truncated_count = len(sub_questions) - _MAX_SUB_QUESTIONS
            sub_questions = sub_questions[:_MAX_SUB_QUESTIONS]
            span.note(
                "decompose_question_truncated",
                before={"sub_question_count": len(sub_questions) + truncated_count},
                after={"sub_question_count": _MAX_SUB_QUESTIONS},
                detail=f"truncated {truncated_count} extra sub-question(s) to cap of {_MAX_SUB_QUESTIONS}",
            )

    except Exception as exc:
        # Fail-safe: any LLM or parse error → single UNKNOWN sub-question → abstain path.
        sub_questions = _fail_safe(question_text)
        span.note(
            "decompose_question_fail_safe",
            before={"status": turn.status.value},
            after={"sub_question_count": 1, "proposed_source": DocSource.UNKNOWN.value,
                   "status": TurnStatus.DECOMPOSED.value},
            detail=f"fail-safe triggered ({type(exc).__name__}: {exc}); 1 sub-q, source=UNKNOWN",
        )
        span.error = f"{type(exc).__name__}: {exc}"

    turn.sub_questions = sub_questions
    turn.status = TurnStatus.DECOMPOSED

    sources = [sq.proposed_source.value for sq in sub_questions]
    span.summary = (
        f"decomposed into {len(sub_questions)} sub-question(s): {sources}"
    )
    span.delta = {
        "status": TurnStatus.DECOMPOSED.value,
        "sub_questions_created": len(sub_questions),
        "sources": sources,
    }

    # Only set span.note if it wasn't already set by the fail-safe / truncation path.
    if not span.before:
        span.note(
            "decompose_question",
            before={"sub_question_count": 0, "status": TurnStatus.RECEIVED.value},
            after={
                "sub_question_count": len(sub_questions),
                "sub_questions": [
                    {"id": sq.id, "text": sq.text, "proposed_source": sq.proposed_source.value}
                    for sq in sub_questions
                ],
                "status": TurnStatus.DECOMPOSED.value,
            },
            detail=span.summary,
        )

    return state
