"""run_demo.py — push a sample supervisor question through the graph; print the event feed.

Demonstrates the walking skeleton end-to-end: one turn flows through all nodes, the deterministic
nodes are REAL (routing, retrieval against the live kb index, confidence, citation enforcement),
the three LLM nodes are stubs. Prints the per-node event feed + the final answer + the metrics
rollup, and exports the data-out JSON the UI reads (Q3: JSON fixtures behind a swappable read module).

Run: python run_demo.py
"""

from __future__ import annotations

import json
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver

from src.graph import build_graph
from src.observability import export_data_out, metrics_rollup, reset_sink
from src.state import ConversationState, DocSource, SubQuestion, Turn

FIXTURE_PATH = Path(__file__).resolve().parent / "mock_data" / "data_out.json"


def _sample_state() -> ConversationState:
    """A mixed multi-part turn: one groundable (maintenance torque) + one unanswerable (warranty).
    Sub-questions are pre-seeded so the LLM-stub decomposer keeps them — the skeleton demonstrates
    the grounded + honest-abstain paths in one turn (ANSWERED_PARTIAL)."""
    turn = Turn(
        turn_id="t1",
        question_text="What torque do the CNC VF-4 vise jaw bolts need, and what's the spindle warranty period?",
        sub_questions=[
            SubQuestion(id="sq1", text="What is the torque spec for the CNC VF-4 vise jaw bolts?",
                        proposed_source=DocSource.MAINTENANCE_MANUALS),
            SubQuestion(id="sq2", text="What is the warranty period on the CNC VF-4 spindle?",
                        proposed_source=DocSource.UNKNOWN),
        ],
    )
    return ConversationState(conversation_id="demo-1", supervisor_id="sup-7", current_turn=turn)


def main() -> None:
    reset_sink()
    app = build_graph(checkpointer=MemorySaver())  # in-memory: zero disk writes
    result = app.invoke(_sample_state(), config={"configurable": {"thread_id": "demo-1"}})
    state = ConversationState.model_validate(result)

    print("\n=== EVENT FEED ===")
    print(f"{'node':<20}{'status':<20}{'ms':>7}{'cost$':>9}")
    for e in state.events:
        print(f"{e.node:<20}{e.status:<20}{e.latency_ms:>7.0f}{e.cost_usd:>9.4f}")

    turn = state.turns[-1] if state.turns else state.current_turn
    print("\n=== FINAL ANSWER ===")
    print(f"status: {turn.status.value} | turn_confidence: {turn.turn_confidence.value if turn.turn_confidence else '-'}")
    print(turn.answer_text)
    print(f"\ncitations: {[(c.source.value, c.section, c.doc_version) for c in turn.citations]}")

    m = metrics_rollup(state)
    print("\n=== METRICS ROLLUP ===")
    print(f"cycle_time={m.cycle_time:.3f}s  tokens={m.tokens_total}  cost=${m.cost_total:.4f}  "
          f"gaps={m.knowledge_gap_count}  straight_through={m.straight_through_pct:.0f}% "
          f"partial={m.partial_rate:.0f}% abstain={m.abstain_rate:.0f}%")
    if m.cost_by_agent:
        print(f"most-expensive node: {max(m.cost_by_agent, key=m.cost_by_agent.get)} (deterministic nodes = $0)")

    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(json.dumps(export_data_out(state), indent=2))
    print(f"\ndata-out JSON exported → {FIXTURE_PATH.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
