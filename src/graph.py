"""graph.py — the orchestration: nodes + typed state + deterministic conditional edges.

This is the ONLY place edges live — it's what you narrate against the mermaid render. Routing is
deterministic (predicates over current_turn.sub_questions); no interrupts (no HIL in this system);
the SqliteSaver checkpointer provides conversation memory + replay, keyed by thread_id == conversation_id.

Pipeline (spec §6):
  ingest → decompose → route ─(known?)→ retrieve → judge ─(fail&under-cap?)↺ retrieve
                              └(all UNKNOWN)──────────────────────────────────→ assess
  judge ─(else)→ assess ─(any HIGH/MEDIUM?)→ assemble → deliver ─(grounded?)→ END
                       └(all LOW)→ abstain → END        deliver └(none)→ abstain
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from src.nodes.abstain import abstain
from src.nodes.assemble_answer import assemble_answer
from src.nodes.assess_confidence import assess_confidence
from src.nodes.decompose_question import decompose_question
from src.nodes.deliver_answer import deliver_answer
from src.nodes.ingest_question import ingest_question
from src.nodes.judge_grounding import judge_grounding
from src.nodes.retrieve_chunks import retrieve_chunks
from src.nodes.route_sources import route_sources
from src.state import (
    ConfidenceLevel,
    ConversationState,
    DocSource,
    JudgeVerdict,
    TurnStatus,
)

_CKPT_PATH = Path(__file__).resolve().parents[1] / "var" / "checkpoints.db"


# --- deterministic routing predicates (read-only over current_turn) ---------
def _after_ingest(state: ConversationState) -> str:
    return "end" if state.current_turn and state.current_turn.status == TurnStatus.FAILED else "decompose"


def _after_route(state: ConversationState) -> str:
    """Any sub-question routed to a known source → retrieve; all UNKNOWN → skip to assess."""
    sqs = state.current_turn.sub_questions if state.current_turn else []
    return "retrieve" if any(sq.routed_source != DocSource.UNKNOWN for sq in sqs) else "assess"


def _after_judge(state: ConversationState) -> str:
    """Bounded retry: re-retrieve only failing, known-source sub-qs still under the attempt cap."""
    sqs = state.current_turn.sub_questions if state.current_turn else []
    cap = state.config.max_retrieval_loops
    needs_retry = any(
        sq.judge_verdict == JudgeVerdict.FAIL
        and sq.routed_source != DocSource.UNKNOWN
        and sq.retrieval_attempts < cap
        for sq in sqs
    )
    return "retrieve" if needs_retry else "assess"


def _after_assess(state: ConversationState) -> str:
    sqs = state.current_turn.sub_questions if state.current_turn else []
    return "assemble" if any(sq.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM) for sq in sqs) else "abstain"


def _after_deliver(state: ConversationState) -> str:
    """≥1 grounded part survived citation enforcement → END; else deliver routes to abstain."""
    ok = state.current_turn and state.current_turn.status in (TurnStatus.ANSWERED, TurnStatus.ANSWERED_PARTIAL)
    return "end" if ok else "abstain"


def build_graph(checkpointer=None):
    """Wire the graph and compile it. Pass a checkpointer, or None to use the default SqliteSaver."""
    g = StateGraph(ConversationState)
    for node in (ingest_question, decompose_question, route_sources, retrieve_chunks,
                 judge_grounding, assess_confidence, assemble_answer, deliver_answer, abstain):
        g.add_node(node.__name__, node)

    g.add_edge(START, "ingest_question")
    g.add_conditional_edges("ingest_question", _after_ingest,
                            {"decompose": "decompose_question", "end": END})
    g.add_edge("decompose_question", "route_sources")
    g.add_conditional_edges("route_sources", _after_route,
                            {"retrieve": "retrieve_chunks", "assess": "assess_confidence"})
    g.add_edge("retrieve_chunks", "judge_grounding")
    g.add_conditional_edges("judge_grounding", _after_judge,
                            {"retrieve": "retrieve_chunks", "assess": "assess_confidence"})
    g.add_conditional_edges("assess_confidence", _after_assess,
                            {"assemble": "assemble_answer", "abstain": "abstain"})
    g.add_edge("assemble_answer", "deliver_answer")
    g.add_conditional_edges("deliver_answer", _after_deliver, {"end": END, "abstain": "abstain"})
    g.add_edge("abstain", END)

    if checkpointer is None:
        _CKPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        checkpointer = SqliteSaver(sqlite3.connect(_CKPT_PATH, check_same_thread=False))
    return g.compile(checkpointer=checkpointer)
