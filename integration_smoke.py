"""integration_smoke.py — real end-to-end pass over curated real-corpus questions.

Runs the WHOLE pipeline with the REAL agents (decompose→…→deliver/abstain) as a multi-turn
conversation on one thread_id, proving: grounded HIGH answers, a multi-part PARTIAL, an honest
ABSTAIN, and an exact-identifier (BM25) hit. Prints the per-turn event feed + metrics rollup, and
exports the real data-out JSON the UI consumes.

This is the §5 integration smoke (REAL output → RESULTS.md). Conversation memory uses the
checkpointer-continuation pattern the orchestration test surfaced: for turn N>1, load the
checkpointed state and update only current_turn before re-invoking (LangGraph replaces root state).

Run: python integration_smoke.py
"""

from __future__ import annotations

import json
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver

from src.graph import build_graph
from src.observability import export_data_out, metrics_rollup, reset_sink
from src.state import ConversationState, Turn

FIXTURE = Path(__file__).resolve().parent / "mock_data" / "conversation_real.json"

# Curated real-corpus questions — each targets a distinct outcome to exercise every path.
QUESTIONS = [
    "What torque do the CNC VF-4 vise jaw bolts need?",                       # single-source HIGH (table)
    "What is the first action for fault code 144 on the VF-4?",              # exact-identifier (BM25) HIGH
    "What torque do the vise jaw bolts need, and what is the spindle warranty period?",  # PARTIAL
    "What is the company's parental leave policy?",                          # no source → ABSTAIN
]


def ask(app, config, supervisor_id: str, question: str) -> ConversationState:
    """One conversational turn. Loads prior checkpointed state (memory) and updates only the
    working turn, so `turns` accumulates across the conversation."""
    snap = app.get_state(config)
    if snap.values:
        state = ConversationState.model_validate(snap.values)
    else:
        state = ConversationState(conversation_id=config["configurable"]["thread_id"],
                                  supervisor_id=supervisor_id)
    state.current_turn = Turn(turn_id=f"t{len(state.turns) + 1}", question_text=question)
    return ConversationState.model_validate(app.invoke(state, config=config))


def main() -> None:
    reset_sink()
    app = build_graph(checkpointer=MemorySaver())  # in-memory: zero disk writes (no checkpoints.db bloat)
    config = {"configurable": {"thread_id": "smoke-1"}}

    state = None
    for q in QUESTIONS:
        state = ask(app, config, "sup-7", q)
        turn = state.turns[-1]
        print(f"\nQ: {q}")
        print(f"   status={turn.status.value} confidence={turn.turn_confidence.value if turn.turn_confidence else '-'} "
              f"citations={len(turn.citations)}")
        print(f"   answer: {(turn.answer_text or '')[:160].replace(chr(10), ' ')}…")

    assert state is not None
    m = metrics_rollup(state)
    print("\n=== CONVERSATION METRICS ===")
    print(f"turns={len(state.turns)} tokens={m.tokens_total} cost=${m.cost_total:.4f} gaps={m.knowledge_gap_count}")
    print(f"straight_through={m.straight_through_pct:.0f}% partial={m.partial_rate:.0f}% abstain={m.abstain_rate:.0f}%")
    if m.cost_by_agent:
        top = max(m.cost_by_agent, key=m.cost_by_agent.get)
        print(f"most-expensive node: {top} ${m.cost_by_agent[top]:.4f}  (deterministic nodes = $0)")

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(export_data_out(state), indent=2))
    print(f"\nreal data-out exported → {FIXTURE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
