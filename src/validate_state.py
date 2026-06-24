"""validate_state.py — the §3 freeze gate. Run: python -m src.validate_state

Builds a FULLY-POPULATED ConversationState (every sub-object exercised), then proves it
survives both round-trips the system actually relies on:
  - dict round-trip:  ConversationState(**state.model_dump())          (in-process state passing)
  - JSON round-trip:  model_validate_json(state.model_dump_json())     (the checkpointer's path)
If both reconstruct identically, the schema is frozen and safe to build on.
"""

from __future__ import annotations

from src.state import (
    AuditEntry,
    Citation,
    ConfidenceLevel,
    ConversationState,
    ConversationStatus,
    DocSource,
    ElementType,
    Event,
    GapReason,
    JudgeFailureMode,
    JudgeVerdict,
    KnowledgeGap,
    Metrics,
    RetrievedChunk,
    SubQuestion,
    Turn,
    TurnStatus,
)


def _sample_state() -> ConversationState:
    """A maximal state: a multi-part turn with a TABLE chunk, a citation, a gap, an event,
    and an audit entry — so the round-trip touches every typed field at least once."""
    chunk = RetrievedChunk(
        chunk_id="MPM-MNT-002#sec4#tbl-torque",
        source=DocSource.MAINTENANCE_MANUALS,
        doc_title="Equipment Maintenance Manual",
        doc_version="5.4",
        section="Section 4 — Torque Specifications",
        page=None,
        element_type=ElementType.TABLE,
        text="Torque specifications table: die clamp, bolster, vise jaw fasteners and values.",
        table_markdown="| Application | Fastener | Torque |\n|---|---|---|\n| Vise jaw | M12 8.8 | 80 N·m |",
        score=0.81,
    )
    sub_high = SubQuestion(
        id="sq1",
        text="What is the torque spec for the CNC VF-4 vise jaw bolts?",
        proposed_source=DocSource.MAINTENANCE_MANUALS,
        routed_source=DocSource.MAINTENANCE_MANUALS,
        retrieved=[chunk],
        retrieval_attempts=1,
        judge_verdict=JudgeVerdict.PASS,
        judge_reasons=["value '80 N·m' is unambiguously present in table_markdown"],
        supporting_chunk_ids=["MPM-MNT-002#sec4#tbl-torque"],
        confidence=ConfidenceLevel.HIGH,
    )
    sub_low = SubQuestion(
        id="sq2",
        text="What is the warranty period on the spindle?",
        proposed_source=DocSource.UNKNOWN,
        routed_source=DocSource.UNKNOWN,
        judge_failure_mode=JudgeFailureMode.VALUE_NOT_FOUND,
        confidence=ConfidenceLevel.LOW,
    )
    citation = Citation(
        chunk_id=chunk.chunk_id,
        source=chunk.source,
        doc_title=chunk.doc_title,
        doc_version=chunk.doc_version,
        section=chunk.section,
        element_type=ElementType.TABLE,
        snippet="CNC VF-4 vise jaw bolts | M12 grade 8.8 | 80 N·m (59 ft·lb)",
    )
    turn = Turn(
        turn_id="t1",
        question_text="What's the vise jaw torque, and what's the spindle warranty?",
        sub_questions=[sub_high, sub_low],
        answer_text="The CNC VF-4 vise jaw bolts are torqued to 80 N·m (59 ft·lb) "
        "[Maintenance Manual §4, Rev 5.4]. I can't ground the spindle warranty period in the "
        "available documentation — please consult the equipment OEM warranty records.",
        citations=[citation],
        turn_confidence=ConfidenceLevel.LOW,  # min(HIGH, LOW) — only as trustworthy as weakest part
        status=TurnStatus.ANSWERED_PARTIAL,
    )
    gap = KnowledgeGap(
        turn_id="t1",
        sub_question_id="sq2",
        question_text="What is the warranty period on the spindle?",
        attempted_source=DocSource.UNKNOWN,
        reason=GapReason.NO_SOURCE_MATCHED,
        top_score=None,
    )
    event = Event(
        thread_id="conv-1",
        node="assess_confidence",
        status=TurnStatus.ASSESSED.value,
        model=None,
        cost_usd=0.0,  # deterministic node
        summary="sq1=HIGH, sq2=LOW(NO_SOURCE_MATCHED); turn_confidence=LOW",
        state_delta={"turn_confidence": "LOW"},
    )
    audit = AuditEntry(
        actor="assess_confidence",
        action="confidence_decision",
        before={"sq1": None, "sq2": None},
        after={"sq1": "HIGH", "sq2": "LOW"},
        detail="deterministic: from fused score + judge verdict + judged-chunk coverage",
    )
    return ConversationState(
        conversation_id="conv-1",
        supervisor_id="sup-42",
        status=ConversationStatus.ACTIVE,
        turns=[turn],            # terminal node already appended this exchange
        current_turn=None,       # transient slot is cleared after the terminal node
        knowledge_gaps=[gap],
        audit_log=[audit],
        events=[event],
        metrics=Metrics(knowledge_gap_count=1, partial_rate=1.0),
    )


def main() -> None:
    state = _sample_state()

    # 1. dict round-trip (in-process state passing between nodes)
    dict_rt = ConversationState(**state.model_dump())
    assert dict_rt == state, "dict round-trip changed the state"

    # 2. JSON round-trip (the SqliteSaver checkpointer's serialize/deserialize path)
    json_rt = ConversationState.model_validate_json(state.model_dump_json())
    assert json_rt == state, "JSON round-trip changed the state"

    # 3. a bare, fresh conversation must also validate (defaults are complete)
    fresh = ConversationState(conversation_id="c0", supervisor_id="s0")
    assert ConversationState(**fresh.model_dump()) == fresh, "fresh-state round-trip failed"

    print("✔ state schema validates")
    print(f"  - dict round-trip:  equal ({len(state.model_dump())} top-level fields)")
    print(f"  - JSON round-trip:  equal ({len(state.model_dump_json())} bytes serialized)")
    print(f"  - fresh-state defaults: complete (config top_k={fresh.config.top_k}, "
          f"floors {fresh.config.min_score_floor}/{fresh.config.high_score_floor})")
    print("  FREEZE POINT: schema is safe to build on.")


if __name__ == "__main__":
    main()
