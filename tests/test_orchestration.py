"""test_orchestration.py — OFFLINE orchestration invariant tests (no API key / no LLM calls).

Covers all 11 named invariants from spec §6 + §11:
  1.  test_grounded_happy_path         — all HIGH → ANSWERED, fully cited
  2.  test_partial_answer              — HIGH + LOW → ANSWERED_PARTIAL + gap
  3.  test_all_low_abstain             — all LOW → ABSTAINED, gaps logged
  4.  test_table_value_not_found       — judge FAIL/VALUE_NOT_FOUND → LOW, value never interpolated
  5.  test_never_answer_ungrounded     — FAIL/LOW part never appears as confident cited claim
  6.  test_always_cite                 — fragment with no citation → downgraded LOW, never delivered
  7.  test_never_guess                 — LOW/UNKNOWN → deterministic uncertainty; assemble never invoked
  8.  test_route_only_known_sources    — UNKNOWN sub-q never reaches retrieval; auto-LOW + gap
  9.  test_max_retrieval_loops         — retries bounded; at cap → LOW
  10. test_confidence_is_min           — turn_confidence == min(sub-question confidences)
  11. test_conversation_memory         — two turns on one thread_id; turn 1 in turns; checkpointer round-trip

Strategy:
  - Full-graph end-to-end: build_graph(checkpointer=MemorySaver()) + app.invoke()
  - Force LLM-node behaviour by PRE-SEEDING sub_questions before invocation
    (decompose keeps pre-seeded sqs; judge skips sub-qs with judge_verdict already set;
     retrieve skips sub-qs with judge_verdict==PASS)
  - Node-level: assess_confidence / deliver_answer / abstain called directly on a
    constructed ConversationState
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from langgraph.checkpoint.memory import MemorySaver

from src.graph import build_graph
from src.nodes.abstain import abstain as abstain_node
from src.nodes.assess_confidence import assess_confidence
from src.nodes.deliver_answer import deliver_answer
from src.state import (
    Citation,
    ConfidenceLevel,
    ConversationState,
    DocSource,
    ElementType,
    GapReason,
    JudgeFailureMode,
    JudgeVerdict,
    Metrics,
    RetrievedChunk,
    SubQuestion,
    Turn,
    TurnStatus,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_state(
    sub_questions: list[SubQuestion] | None = None,
    conversation_id: str | None = None,
    question_text: str = "What is the torque spec?",
) -> ConversationState:
    """Minimal ConversationState with a current_turn pre-seeded with sub_questions."""
    cid = conversation_id or str(uuid.uuid4())
    turn = Turn(
        turn_id=str(uuid.uuid4()),
        question_text=question_text,
        sub_questions=sub_questions or [],
        status=TurnStatus.RECEIVED,
        ts=_now(),
    )
    return ConversationState(
        conversation_id=cid,
        supervisor_id="sup-test",
        current_turn=turn,
        metrics=Metrics(),
    )


def _chunk(
    chunk_id: str = "c1",
    source: DocSource = DocSource.MAINTENANCE_MANUALS,
    score: float = 0.9,
    element_type: ElementType = ElementType.PROSE,
    table_markdown: str | None = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        source=source,
        doc_title="Test Manual",
        doc_version="v1",
        section="§2.1",
        page=10,
        element_type=element_type,
        text="Some relevant text about the topic.",
        table_markdown=table_markdown,
        score=score,
    )


def _citation(chunk_id: str = "c1", source: DocSource = DocSource.MAINTENANCE_MANUALS) -> Citation:
    return Citation(
        chunk_id=chunk_id,
        source=source,
        doc_title="Test Manual",
        doc_version="v1",
        section="§2.1",
        page=10,
        element_type=ElementType.PROSE,
        snippet="Some relevant text about the topic.",
    )


def _sq_high(sq_id: str = "sq1", chunk_id: str = "c1") -> SubQuestion:
    """A sub-question pre-seeded for a HIGH confidence pass-through."""
    return SubQuestion(
        id=sq_id,
        text="What is the maintenance torque?",
        proposed_source=DocSource.MAINTENANCE_MANUALS,
        routed_source=DocSource.MAINTENANCE_MANUALS,
        retrieved=[_chunk(chunk_id=chunk_id, score=0.9)],
        retrieval_attempts=1,
        judge_verdict=JudgeVerdict.PASS,
        judge_reasons=["forced PASS"],
        supporting_chunk_ids=[chunk_id],
    )


def _sq_low_unknown(sq_id: str = "sq2") -> SubQuestion:
    """A sub-question pre-seeded for a LOW via UNKNOWN source."""
    return SubQuestion(
        id=sq_id,
        text="What is the alien repair protocol?",
        proposed_source=DocSource.UNKNOWN,
        routed_source=DocSource.UNKNOWN,
        retrieved=[],
        retrieval_attempts=0,
        judge_verdict=None,
        supporting_chunk_ids=[],
    )


def _invoke_graph(
    sub_questions: list[SubQuestion],
    thread_id: str | None = None,
    question_text: str = "What is the spec?",
) -> ConversationState:
    """Helper: run the full graph with MemorySaver, return validated ConversationState."""
    tid = thread_id or str(uuid.uuid4())
    app = build_graph(checkpointer=MemorySaver())
    state = _make_state(
        sub_questions=sub_questions,
        conversation_id=tid,
        question_text=question_text,
    )
    result = app.invoke(state, config={"configurable": {"thread_id": tid}})
    return ConversationState.model_validate(result)


# ===========================================================================
# 1. test_grounded_happy_path
# ===========================================================================

def test_grounded_happy_path():
    """All HIGH sub-qs → ANSWERED, turn_confidence=HIGH, citations present."""
    sq1 = _sq_high("sq1", "c1")
    sq2 = SubQuestion(
        id="sq2",
        text="What is the safety clearance?",
        proposed_source=DocSource.SAFETY_PROCEDURES,
        routed_source=DocSource.SAFETY_PROCEDURES,
        retrieved=[_chunk("c2", source=DocSource.SAFETY_PROCEDURES, score=0.92)],
        retrieval_attempts=1,
        judge_verdict=JudgeVerdict.PASS,
        judge_reasons=["forced PASS"],
        supporting_chunk_ids=["c2"],
    )

    out = _invoke_graph([sq1, sq2])

    assert out.current_turn is not None
    assert out.current_turn.status == TurnStatus.ANSWERED, (
        f"expected ANSWERED, got {out.current_turn.status}"
    )
    assert out.current_turn.turn_confidence == ConfidenceLevel.HIGH
    assert len(out.current_turn.citations) >= 2, "expected at least 2 citations"
    assert out.current_turn.answer_text is not None
    # No LOW parts → no uncertainty lines in answer
    assert "⚠︎" not in out.current_turn.answer_text or "partial" not in out.current_turn.answer_text.lower()
    # Turn should be in persisted history
    assert any(t.status == TurnStatus.ANSWERED for t in out.turns)


# ===========================================================================
# 2. test_partial_answer
# ===========================================================================

def test_partial_answer():
    """HIGH + UNKNOWN(LOW) → ANSWERED_PARTIAL, turn_confidence=LOW, gap logged, uncertainty line."""
    sq_high = _sq_high("sq1", "c1")
    sq_unk = _sq_low_unknown("sq2")

    out = _invoke_graph([sq_high, sq_unk])

    assert out.current_turn is not None
    assert out.current_turn.status == TurnStatus.ANSWERED_PARTIAL, (
        f"expected ANSWERED_PARTIAL, got {out.current_turn.status}"
    )
    # turn_confidence == min → LOW (because one part is LOW)
    assert out.current_turn.turn_confidence == ConfidenceLevel.LOW
    # At least one gap logged for the UNKNOWN sub-q
    assert len(out.knowledge_gaps) >= 1
    gap_reasons = [g.reason for g in out.knowledge_gaps]
    assert GapReason.NO_SOURCE_MATCHED in gap_reasons
    # The LOW sub-q gets an uncertainty line in answer_text
    assert out.current_turn.answer_text is not None
    assert "⚠︎" in out.current_turn.answer_text


# ===========================================================================
# 3. test_all_low_abstain
# ===========================================================================

def test_all_low_abstain():
    """All LOW → ABSTAINED, deterministic message, gaps logged."""
    sq1 = _sq_low_unknown("sq1")
    sq2 = _sq_low_unknown("sq2")

    out = _invoke_graph([sq1, sq2])

    assert out.current_turn is not None
    assert out.current_turn.status == TurnStatus.ABSTAINED, (
        f"expected ABSTAINED, got {out.current_turn.status}"
    )
    assert out.current_turn.turn_confidence == ConfidenceLevel.LOW
    # Deterministic abstain message — never fabricated
    assert out.current_turn.answer_text is not None
    assert len(out.current_turn.answer_text) > 0
    # Must not contain any asserted citation info
    assert out.current_turn.citations == []
    # All LOW → gaps logged
    assert len(out.knowledge_gaps) >= 2
    # Abstained turn is in persisted history
    assert any(t.status == TurnStatus.ABSTAINED for t in out.turns)


# ===========================================================================
# 4. test_table_value_not_found
# ===========================================================================

def test_table_value_not_found():
    """TABLE chunk retrieved, judge FAILs with VALUE_NOT_FOUND → LOW, value never interpolated."""
    table_chunk = _chunk(
        chunk_id="tbl1",
        element_type=ElementType.TABLE,
        table_markdown="| Part | Torque |\n|---|---|\n| Bolt A | 15 Nm |",
        score=0.88,
    )
    sq = SubQuestion(
        id="sq1",
        text="What is the torque for Bolt Z?",
        proposed_source=DocSource.MAINTENANCE_MANUALS,
        routed_source=DocSource.MAINTENANCE_MANUALS,
        retrieved=[table_chunk],
        retrieval_attempts=1,
        # Pre-seed a FAIL with VALUE_NOT_FOUND
        judge_verdict=JudgeVerdict.FAIL,
        judge_failure_mode=JudgeFailureMode.VALUE_NOT_FOUND,
        judge_reasons=["Bolt Z not found in table"],
        supporting_chunk_ids=[],
    )

    out = _invoke_graph([sq])

    assert out.current_turn is not None
    # The VALUE_NOT_FOUND FAIL should produce LOW confidence → ABSTAINED (all LOW)
    assert out.current_turn.status == TurnStatus.ABSTAINED
    assert out.current_turn.turn_confidence == ConfidenceLevel.LOW
    # Gap logged with VALUE_NOT_FOUND reason
    vnf_gaps = [g for g in out.knowledge_gaps if g.reason == GapReason.VALUE_NOT_FOUND]
    assert len(vnf_gaps) >= 1, f"expected VALUE_NOT_FOUND gap, got {[g.reason for g in out.knowledge_gaps]}"
    # The answer must NOT contain any interpolated value from the table
    answer = out.current_turn.answer_text or ""
    assert "15 Nm" not in answer, "table value must never be interpolated when judge FAILs"
    assert "Bolt Z" not in answer or "⚠︎" in answer or "unable" in answer.lower()


# ===========================================================================
# 5. test_never_answer_ungrounded
# ===========================================================================

def test_never_answer_ungrounded():
    """A FAIL/LOW sub-q never appears as a confident cited claim.

    Node-level: construct a state with one LOW sq (judge FAIL) and directly
    call assess_confidence → deliver_answer. The LOW part must appear only as
    an uncertainty line (or route to abstain), never as a cited answer fragment.
    """
    sq = SubQuestion(
        id="sq1",
        text="How do I override the safety interlock?",
        proposed_source=DocSource.SAFETY_PROCEDURES,
        routed_source=DocSource.SAFETY_PROCEDURES,
        retrieved=[_chunk("c1", score=0.8)],
        retrieval_attempts=2,
        judge_verdict=JudgeVerdict.FAIL,
        judge_failure_mode=JudgeFailureMode.UNGROUNDED,
        judge_reasons=["chunks do not answer the sub-question"],
        supporting_chunk_ids=[],
    )
    state = _make_state([sq])
    # manually set status so deliver_answer starts from the right place
    state.current_turn.status = TurnStatus.RETRIEVED

    # Run assess_confidence first (deterministic)
    state = assess_confidence(state)
    assert state.current_turn.sub_questions[0].confidence == ConfidenceLevel.LOW

    # Now deliver_answer — nothing grounded → routes to abstain path (no append, status stays)
    state_after = deliver_answer(state)

    # If all LOW, deliver_answer does NOT set ANSWERED/ANSWERED_PARTIAL
    final_status = state_after.current_turn.status
    assert final_status not in (TurnStatus.ANSWERED, TurnStatus.ANSWERED_PARTIAL), (
        f"ungrounded LOW sub-q must never produce ANSWERED/ANSWERED_PARTIAL, got {final_status}"
    )
    # Citations must be empty
    assert state_after.current_turn.citations == []


# ===========================================================================
# 6. test_always_cite
# ===========================================================================

def test_always_cite():
    """HIGH/MEDIUM fragment with NO citation → downgraded to LOW by deliver_answer, never delivered.

    Construct a state where a sub-question is HIGH confidence but supporting_chunk_ids
    do NOT overlap with the turn's citations. deliver_answer must downgrade it.
    """
    sq = SubQuestion(
        id="sq1",
        text="What is the pressure rating?",
        proposed_source=DocSource.MAINTENANCE_MANUALS,
        routed_source=DocSource.MAINTENANCE_MANUALS,
        retrieved=[_chunk("c1", score=0.9)],
        retrieval_attempts=1,
        judge_verdict=JudgeVerdict.PASS,
        supporting_chunk_ids=["c1"],
        confidence=ConfidenceLevel.HIGH,  # already assessed
    )
    state = _make_state([sq])
    state.current_turn.status = TurnStatus.ASSESSED
    # Intentionally give the turn a citation for a DIFFERENT chunk id
    state.current_turn.citations = [_citation(chunk_id="c99")]  # no overlap with "c1"
    state.current_turn.answer_text = "The pressure rating is X PSI."

    state_after = deliver_answer(state)

    # With no citation overlap, sq1 must be downgraded to LOW
    sq1_after = state_after.current_turn.sub_questions[0]
    assert sq1_after.confidence == ConfidenceLevel.LOW, (
        f"expected LOW after citation enforcement, got {sq1_after.confidence}"
    )
    # Since all parts are now LOW, deliver_answer does NOT set ANSWERED
    final_status = state_after.current_turn.status
    assert final_status not in (TurnStatus.ANSWERED, TurnStatus.ANSWERED_PARTIAL), (
        f"zero-citation HIGH fragment must not produce ANSWERED, got {final_status}"
    )


# ===========================================================================
# 7. test_never_guess
# ===========================================================================

def test_never_guess():
    """LOW/UNKNOWN sub-q → deterministic uncertainty statement; no fabricated content."""
    sq = _sq_low_unknown("sq1")
    # Run via full graph
    out = _invoke_graph([sq])

    assert out.current_turn is not None
    assert out.current_turn.status == TurnStatus.ABSTAINED
    # The message must be the deterministic template, not a model-generated answer
    answer = out.current_turn.answer_text or ""
    assert len(answer) > 0
    # Deterministic template markers
    assert "unable" in answer.lower() or "no" in answer.lower() or "consult" in answer.lower()
    # No citations on an abstained turn
    assert out.current_turn.citations == []
    # assemble_answer should have been bypassed entirely — no ASSEMBLED status should have been set
    # (we can verify by checking the events — no assemble_answer event, or abstain was reached directly)
    node_names = [e.node for e in out.events]
    # If assemble_answer was invoked it would appear in events; the graph should route to abstain
    # For all-LOW, the graph edge _after_assess returns "abstain" — assemble_answer should NOT appear
    assert "assemble_answer" not in node_names, (
        f"assemble_answer must NOT be invoked on all-LOW sub-qs; events: {node_names}"
    )


# ===========================================================================
# 8. test_route_only_known_sources
# ===========================================================================

def test_route_only_known_sources():
    """UNKNOWN sub-q never reaches hybrid_search; auto-LOW + gap logged."""
    sq = SubQuestion(
        id="sq1",
        text="Tell me about UFO maintenance protocols.",
        proposed_source=DocSource.UNKNOWN,
        routed_source=DocSource.UNKNOWN,  # already routed (or would be by route_sources)
        retrieved=[],
        retrieval_attempts=0,
        judge_verdict=None,
        supporting_chunk_ids=[],
    )
    out = _invoke_graph([sq])

    assert out.current_turn is not None
    assert out.current_turn.status == TurnStatus.ABSTAINED
    assert out.current_turn.turn_confidence == ConfidenceLevel.LOW

    # Gap must be logged with NO_SOURCE_MATCHED
    assert any(g.reason == GapReason.NO_SOURCE_MATCHED for g in out.knowledge_gaps), (
        f"expected NO_SOURCE_MATCHED gap, got {[g.reason for g in out.knowledge_gaps]}"
    )

    # retrieve_chunks must NOT have attempted this sub-q (retrieval_attempts stays 0)
    # Check via the sub-question in current_turn or the final state
    final_sq = out.current_turn.sub_questions[0]
    assert final_sq.retrieval_attempts == 0, (
        f"UNKNOWN source sub-q must have 0 retrieval attempts, got {final_sq.retrieval_attempts}"
    )


# ===========================================================================
# 9. test_max_retrieval_loops
# ===========================================================================

def test_max_retrieval_loops():
    """Retries are bounded by max_retrieval_loops; at cap → LOW, gap JUDGE_FAIL_AT_CAP.

    We pre-seed the sub-question with retrieval_attempts already at max_retrieval_loops
    and judge_verdict=FAIL. The graph's _after_judge edge should route to assess
    (not back to retrieve), and assess should produce LOW + JUDGE_FAIL_AT_CAP gap.
    """
    chunk = _chunk("c1", score=0.7)
    sq = SubQuestion(
        id="sq1",
        text="What is the off-spec temperature limit?",
        proposed_source=DocSource.QUALITY_CONTROL,
        routed_source=DocSource.QUALITY_CONTROL,
        retrieved=[chunk],
        # At cap: attempts == max_retrieval_loops (default=2)
        retrieval_attempts=2,
        judge_verdict=JudgeVerdict.FAIL,
        judge_failure_mode=JudgeFailureMode.IRRELEVANT,
        judge_reasons=["chunks not relevant"],
        supporting_chunk_ids=[],
    )

    out = _invoke_graph([sq])

    assert out.current_turn is not None
    assert out.current_turn.status == TurnStatus.ABSTAINED

    final_sq = out.current_turn.sub_questions[0]
    assert final_sq.confidence == ConfidenceLevel.LOW

    # Gap must be JUDGE_FAIL_AT_CAP
    assert any(g.reason == GapReason.JUDGE_FAIL_AT_CAP for g in out.knowledge_gaps), (
        f"expected JUDGE_FAIL_AT_CAP gap, got {[g.reason for g in out.knowledge_gaps]}"
    )

    # Retrieval attempts must NOT have increased beyond the cap
    assert final_sq.retrieval_attempts <= 2, (
        f"retrieval_attempts must be ≤ max_retrieval_loops=2, got {final_sq.retrieval_attempts}"
    )


# ===========================================================================
# 10. test_confidence_is_min
# ===========================================================================

def test_confidence_is_min():
    """turn_confidence == min(sub-question confidences) — node-level test on assess_confidence."""
    # Set up: one HIGH, one MEDIUM, one LOW sub-question
    sq_h = SubQuestion(
        id="sq1",
        text="High confidence part",
        proposed_source=DocSource.MAINTENANCE_MANUALS,
        routed_source=DocSource.MAINTENANCE_MANUALS,
        retrieved=[_chunk("c1", score=0.95)],
        retrieval_attempts=1,
        judge_verdict=JudgeVerdict.PASS,
        supporting_chunk_ids=["c1"],
    )
    sq_m = SubQuestion(
        id="sq2",
        text="Medium confidence part",
        proposed_source=DocSource.SAFETY_PROCEDURES,
        routed_source=DocSource.SAFETY_PROCEDURES,
        retrieved=[_chunk("c2", source=DocSource.SAFETY_PROCEDURES, score=0.55)],
        retrieval_attempts=1,
        judge_verdict=JudgeVerdict.PASS,
        supporting_chunk_ids=["c2"],
    )
    sq_l = SubQuestion(
        id="sq3",
        text="Low confidence part",
        proposed_source=DocSource.QUALITY_CONTROL,
        routed_source=DocSource.QUALITY_CONTROL,
        retrieved=[_chunk("c3", source=DocSource.QUALITY_CONTROL, score=0.3)],
        retrieval_attempts=2,
        judge_verdict=JudgeVerdict.FAIL,
        supporting_chunk_ids=[],
    )

    state = _make_state([sq_h, sq_m, sq_l])
    state.current_turn.status = TurnStatus.JUDGED

    out = assess_confidence(state)

    confidences = [sq.confidence for sq in out.current_turn.sub_questions]
    assert ConfidenceLevel.HIGH in confidences
    assert ConfidenceLevel.MEDIUM in confidences
    assert ConfidenceLevel.LOW in confidences

    # turn_confidence must be the minimum
    assert out.current_turn.turn_confidence == ConfidenceLevel.LOW, (
        f"turn_confidence must be LOW (min), got {out.current_turn.turn_confidence}"
    )

    # Verify the min logic with 2 HIGH + 1 MEDIUM case
    sq_h2 = SubQuestion(
        id="sqA",
        text="Another high",
        proposed_source=DocSource.MAINTENANCE_MANUALS,
        routed_source=DocSource.MAINTENANCE_MANUALS,
        retrieved=[_chunk("cA", score=0.9)],
        retrieval_attempts=1,
        judge_verdict=JudgeVerdict.PASS,
        supporting_chunk_ids=["cA"],
    )
    sq_m2 = SubQuestion(
        id="sqB",
        text="A medium",
        proposed_source=DocSource.SAFETY_PROCEDURES,
        routed_source=DocSource.SAFETY_PROCEDURES,
        retrieved=[_chunk("cB", source=DocSource.SAFETY_PROCEDURES, score=0.6)],
        retrieval_attempts=1,
        judge_verdict=JudgeVerdict.PASS,
        supporting_chunk_ids=["cB"],
    )
    state2 = _make_state([sq_h2, sq_m2])
    state2.current_turn.status = TurnStatus.JUDGED
    out2 = assess_confidence(state2)
    assert out2.current_turn.turn_confidence == ConfidenceLevel.MEDIUM, (
        f"min of HIGH+MEDIUM must be MEDIUM, got {out2.current_turn.turn_confidence}"
    )


# ===========================================================================
# 11. test_conversation_memory
# ===========================================================================

def test_conversation_memory():
    """Two turns on one thread_id; turn 1 is present in state.turns after turn 2.

    LangGraph's conversation memory contract: the checkpointer stores state keyed by
    thread_id. Turn 2 MUST be invoked by loading the checkpointed state and updating
    only current_turn — passing a completely fresh state object would overwrite the
    persisted turns list, which is the expected LangGraph Pydantic-state behaviour
    (the framework replaces, not merges, list fields when a new root state is passed).
    The correct pattern is app.get_state(config) → mutate current_turn → re-invoke.
    """
    thread_id = str(uuid.uuid4())
    app = build_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": thread_id}}

    # --- Turn 1: high-confidence answer ---
    sq1 = _sq_high("sq1", "c1")
    state1 = _make_state(
        sub_questions=[sq1],
        conversation_id=thread_id,
        question_text="What is the bolt torque?",
    )
    result1 = app.invoke(state1, config=config)
    out1 = ConversationState.model_validate(result1)

    assert out1.current_turn is not None
    assert out1.current_turn.status == TurnStatus.ANSWERED
    # Turn 1 is appended to persisted turns
    assert len(out1.turns) >= 1
    assert any("bolt torque" in t.question_text for t in out1.turns)

    # --- Turn 2: different question on the SAME thread_id ---
    # Correct pattern: load checkpointed state, update only current_turn, re-invoke.
    # This preserves the accumulated turns history held by the checkpointer.
    cp_state = app.get_state(config)
    assert len(cp_state.values.get("turns", [])) >= 1, (
        "checkpointed state should already hold turn 1"
    )

    sq2 = SubQuestion(
        id="sq1",
        text="What is the pressure limit?",
        proposed_source=DocSource.QUALITY_CONTROL,
        routed_source=DocSource.QUALITY_CONTROL,
        retrieved=[_chunk("c2", source=DocSource.QUALITY_CONTROL, score=0.88)],
        retrieval_attempts=1,
        judge_verdict=JudgeVerdict.PASS,
        judge_reasons=["forced PASS"],
        supporting_chunk_ids=["c2"],
    )
    from src.state import Turn as _Turn
    turn2 = _Turn(
        turn_id=str(uuid.uuid4()),
        question_text="What is the pressure limit?",
        sub_questions=[sq2],
        status=TurnStatus.RECEIVED,
        ts=_now(),
    )
    # Build turn-2 state dict from the checkpoint values (preserves turns history)
    state2_values = dict(cp_state.values)
    state2_values["current_turn"] = turn2

    result2 = app.invoke(state2_values, config=config)
    out2 = ConversationState.model_validate(result2)

    # Turn 2 should be answered
    assert out2.current_turn is not None
    assert out2.current_turn.status == TurnStatus.ANSWERED

    # The persisted turns list must contain BOTH turns (checkpointer round-trip)
    assert len(out2.turns) >= 2, (
        f"expected >=2 turns after two invocations on same thread, got {len(out2.turns)}"
    )
    question_texts = [t.question_text for t in out2.turns]
    assert any("bolt torque" in q for q in question_texts), (
        f"turn 1 question missing from turn history: {question_texts}"
    )
    assert any("pressure limit" in q for q in question_texts), (
        f"turn 2 question missing from turn history: {question_texts}"
    )
