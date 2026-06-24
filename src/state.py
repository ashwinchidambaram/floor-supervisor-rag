"""state.py — the canonical typed state (single source of truth).

Role:     One Pydantic v2 object every node reads/writes. Imports nothing from the
          project; imported everywhere. This is the freeze point (§3) — contracts are
          built against it.
Contract: `ConversationState` carries the whole conversation; the graph processes ONE
          turn per invocation. `thread_id == conversation_id`; conversation memory is the
          checkpointer keyed by that id. No interrupts.
Failure:  Validation errors surface at construction. A round-trip parse
          (`ConversationState(**state.model_dump())`) is the freeze gate — see
          `src/validate_state.py`.

Three design decisions locked at freeze (narration points):
  1. A `Turn` is one Q->A EXCHANGE, not a message. We dropped the `role` field/enum that
     the draft spec carried — a Turn already holds both `question_text` and `answer_text`,
     so a single role on it was contradictory. The UI derives the supervisor/assistant
     bubbles from those two fields.
  2. `current_turn` is the TRANSIENT working object for the invocation; it is appended to
     `turns` (the persisted history) ONLY by the terminal nodes (`deliver_answer` /
     `abstain`). `ingest_question` sets `current_turn` but does NOT append — this avoids a
     duplicated-object aliasing bug across the checkpointer's serialize/deserialize cycle.
  3. "Citation coverage" as a HIGH signal in `assess_confidence` means coverage of the
     judged-relevant chunks (every relevant chunk has a citable handle) — computed BEFORE
     assembly. The real, hard citation enforcement (>=1 Citation per delivered fragment)
     lives in `deliver_answer`, AFTER assembly. The two are distinct on purpose.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _now() -> datetime:
    """Timezone-aware UTC timestamp (datetime.utcnow() is deprecated in 3.12)."""
    return datetime.now(timezone.utc)


# --- Enums (no free-text status) -------------------------------------------
class DocSource(str, Enum):
    SAFETY_PROCEDURES = "SAFETY_PROCEDURES"
    MAINTENANCE_MANUALS = "MAINTENANCE_MANUALS"
    QUALITY_CONTROL = "QUALITY_CONTROL"
    UNKNOWN = "UNKNOWN"


class ElementType(str, Enum):
    PROSE = "PROSE"
    TABLE = "TABLE"
    FIGURE = "FIGURE"


class TurnStatus(str, Enum):
    RECEIVED = "RECEIVED"
    DECOMPOSED = "DECOMPOSED"
    ROUTED = "ROUTED"
    RETRIEVED = "RETRIEVED"
    JUDGED = "JUDGED"
    ASSESSED = "ASSESSED"
    ASSEMBLED = "ASSEMBLED"
    ANSWERED = "ANSWERED"
    ANSWERED_PARTIAL = "ANSWERED_PARTIAL"
    ABSTAINED = "ABSTAINED"
    FAILED = "FAILED"


class ConversationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class JudgeVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class JudgeFailureMode(str, Enum):
    """Typed reason a judge FAILs — read by assess_confidence to set GapReason deterministically.
    IRRELEVANT: chunks off-topic · UNGROUNDED: related but don't answer · VALUE_NOT_FOUND: table
    lacks the asked-for value."""

    IRRELEVANT = "IRRELEVANT"
    UNGROUNDED = "UNGROUNDED"
    VALUE_NOT_FOUND = "VALUE_NOT_FOUND"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class GapReason(str, Enum):
    NO_SOURCE_MATCHED = "NO_SOURCE_MATCHED"
    LOW_RETRIEVAL = "LOW_RETRIEVAL"
    JUDGE_FAIL_AT_CAP = "JUDGE_FAIL_AT_CAP"
    VALUE_NOT_FOUND = "VALUE_NOT_FOUND"


# --- Typed sub-objects ------------------------------------------------------
class RetrievedChunk(BaseModel):
    """One retrieved unit. `text` is the EMBEDDED representation; for TABLE chunks the
    full original table rides in `table_markdown` (returned verbatim to the assembler)."""

    chunk_id: str
    source: DocSource
    doc_title: str
    doc_version: str
    section: str
    page: int | None = None
    element_type: ElementType = ElementType.PROSE
    text: str
    table_markdown: str | None = None
    figure_ref: str | None = None
    score: float = 0.0


class Citation(BaseModel):
    """A citable handle attached to a delivered fragment. `snippet` is the quoted grounding."""

    chunk_id: str
    source: DocSource
    doc_title: str
    doc_version: str
    section: str
    page: int | None = None
    element_type: ElementType = ElementType.PROSE
    figure_ref: str | None = None
    snippet: str


class SubQuestion(BaseModel):
    """One decomposed part of the supervisor's question, carried through the pipeline."""

    id: str
    text: str
    proposed_source: DocSource = DocSource.UNKNOWN
    routed_source: DocSource = DocSource.UNKNOWN
    retrieved: list[RetrievedChunk] = Field(default_factory=list)
    retrieval_attempts: int = 0
    judge_verdict: JudgeVerdict | None = None
    judge_reasons: list[str] = Field(default_factory=list)
    judge_failure_mode: JudgeFailureMode | None = None  # typed FAIL reason (AGENTS-SPEC delta)
    supporting_chunk_ids: list[str] = Field(default_factory=list)  # judge-approved chunks; assembler cites ONLY these
    confidence: ConfidenceLevel | None = None


class KnowledgeGap(BaseModel):
    """Append-only telemetry: a part we could not ground. Non-blocking — feedback for the
    documentation team, never an escalation."""

    ts: datetime = Field(default_factory=_now)
    turn_id: str
    sub_question_id: str
    question_text: str
    attempted_source: DocSource
    reason: GapReason
    top_score: float | None = None


class Turn(BaseModel):
    """One Q->A EXCHANGE (see design decision #1). Lifecycle: RECEIVED -> ... -> ANSWERED."""

    turn_id: str
    question_text: str
    sub_questions: list[SubQuestion] = Field(default_factory=list)
    answer_text: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    turn_confidence: ConfidenceLevel | None = None
    status: TurnStatus = TurnStatus.RECEIVED
    ts: datetime = Field(default_factory=_now)


class Event(BaseModel):
    """One typed event per node (data-out contract). Deterministic nodes emit cost_usd=0."""

    thread_id: str
    node: str
    ts: datetime = Field(default_factory=_now)
    status: str
    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    retries: int = 0
    cost_usd: float = 0.0
    summary: str = ""
    state_delta: dict = Field(default_factory=dict)
    error: str | None = None


class AuditEntry(BaseModel):
    """Append-only, compliance-grade attribution: who/what did each thing, before->after."""

    ts: datetime = Field(default_factory=_now)
    actor: str
    action: str
    before: dict = Field(default_factory=dict)
    after: dict = Field(default_factory=dict)
    detail: str = ""


class Metrics(BaseModel):
    """The rollup the metrics UI reads. Defaults to all-zeros so a fresh state validates."""

    cycle_time: float = 0.0
    stage_dwell: dict[str, float] = Field(default_factory=dict)
    tokens_total: int = 0
    cost_total: float = 0.0
    cost_by_agent: dict[str, float] = Field(default_factory=dict)
    retries: int = 0
    judge_reject_rate: float = 0.0
    straight_through_pct: float = 0.0
    partial_rate: float = 0.0
    abstain_rate: float = 0.0
    knowledge_gap_count: int = 0


class RunConfig(BaseModel):
    """Per-conversation knobs. Floors gate the deterministic confidence decision."""

    top_k: int = 5
    max_retrieval_loops: int = 2
    high_score_floor: float = 0.75
    min_score_floor: float = 0.45


# --- Canonical object -------------------------------------------------------
class ConversationState(BaseModel):
    """The single source of truth. One per supervisor conversation; conversation_id == thread_id."""

    conversation_id: str
    supervisor_id: str
    status: ConversationStatus = ConversationStatus.ACTIVE
    turns: list[Turn] = Field(default_factory=list)  # persisted history = conversation memory
    current_turn: Turn | None = None  # transient working object for THIS invocation (decision #2)
    knowledge_gaps: list[KnowledgeGap] = Field(default_factory=list)
    config: RunConfig = Field(default_factory=RunConfig)
    audit_log: list[AuditEntry] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    metrics: Metrics = Field(default_factory=Metrics)
