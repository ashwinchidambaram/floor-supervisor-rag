"""observability.py — the cross-cutting node template + data-out layer (per OBSERVABILITY.md).

Role:     One wrapper every node inherits, so emit/audit/cost/failure are written ONCE. Plus
          the trace sink (sqlite), the metrics rollup, and the JSON data-out export the UI reads.
Contract:
  @traced_node(name, deterministic=?)  — decorate a `fn(state, span) -> state` to get a LangGraph
      node that: times itself, appends an AuditEntry, emits exactly ONE Event, computes cost, and
      on any exception records the error + marks the turn FAILED (degrade, never crash).
  record_gap(state, gap)               — append a KnowledgeGap to state AND the durable sqlite sink.
  metrics_rollup(state) -> Metrics     — what the observability UI screen reads.
  export_data_out(state) -> dict       — the JSON the UI loads (state + events + metrics + gaps + audit).
Failure:  the sink is best-effort (a sqlite error never breaks a run); a node exception is caught,
          recorded, and routed to the safe/abstain path by marking `current_turn.status = FAILED`.

Cost:     cost_usd = tokens_in*price_in + tokens_out*price_out (PRICES, per 1M, from MODELS.md).
          Deterministic nodes pass no usage -> cost_usd = 0.0, surfaced explicitly.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

from src.state import (
    AuditEntry,
    ConversationState,
    Event,
    KnowledgeGap,
    Metrics,
    TurnStatus,
)

# --- cost (per 1M tokens, in/out) — snapshot from MODELS.md; finalized at the model gate ---
PRICES: dict[str, tuple[float, float]] = {
    "google/gemini-3-flash-preview": (0.50, 3.0),
    "google/gemini-3.1-pro-preview": (2.0, 12.0),
    "anthropic/claude-haiku-4.5": (1.0, 5.0),
    "anthropic/claude-sonnet-4.6": (3.0, 15.0),
    "anthropic/claude-opus-4.8": (5.0, 25.0),
}


def compute_cost(model: str | None, tokens_in: int, tokens_out: int) -> float:
    """Deterministic $0 (no model). LLM nodes priced from the table; unknown model -> $0 (surfaced)."""
    if not model or model not in PRICES:
        return 0.0
    pin, pout = PRICES[model]
    return tokens_in / 1e6 * pin + tokens_out / 1e6 * pout


# --- the span a node records into (the only channel for instrumentation) ---
class Span:
    """Per-node scratch the wrapper reads to build the Event + AuditEntry. Deterministic nodes
    touch only `summary`/`note`; LLM nodes also call `record_usage`."""

    def __init__(self, node: str) -> None:
        self.node = node
        self.model: str | None = None
        self.tokens_in = 0
        self.tokens_out = 0
        self.retries = 0
        self.cache_hit = False  # set True when the node reused a cached result (retrieve/assemble)
        self.summary = ""
        self.delta: dict = {}
        self.action = node
        self.before: dict = {}
        self.after: dict = {}
        self.error: str | None = None

    def record_usage(self, model: str, tokens_in: int, tokens_out: int) -> None:
        self.model, self.tokens_in, self.tokens_out = model, tokens_in, tokens_out

    def note(self, action: str, before: dict, after: dict, detail: str = "") -> None:
        """Record a decision for the audit log (actor/action/before->after)."""
        self.action, self.before, self.after = action, before, after
        if detail:
            self.summary = detail


def traced_node(name: str, deterministic: bool = True):
    """Decorate `fn(state, span) -> ConversationState` into a LangGraph node `state -> state`
    that emits one Event, appends one AuditEntry, prices itself, and degrades safely on error."""

    def decorator(fn):
        def wrapped(state: ConversationState) -> ConversationState:
            span = Span(name)
            t0 = time.perf_counter()
            try:
                state = fn(state, span)
                status = state.current_turn.status.value if state.current_turn else state.status.value
            except Exception as e:  # degrade: record + mark FAILED, never crash the graph
                span.error = f"{type(e).__name__}: {e}"
                if state.current_turn is not None:
                    state.current_turn.status = TurnStatus.FAILED
                status = TurnStatus.FAILED.value

            latency_ms = (time.perf_counter() - t0) * 1000
            cost = 0.0 if deterministic else compute_cost(span.model, span.tokens_in, span.tokens_out)
            event = Event(
                thread_id=state.conversation_id,
                node=name,
                status=status,
                model=span.model,
                tokens_in=span.tokens_in,
                tokens_out=span.tokens_out,
                latency_ms=latency_ms,
                retries=span.retries,
                cost_usd=cost,
                cache_hit=span.cache_hit,
                summary=span.summary or f"{name} → {status}",
                state_delta=span.delta,
                error=span.error,
            )
            state.events.append(event)
            state.audit_log.append(
                AuditEntry(actor=name, action=span.action, before=span.before,
                           after=span.after, detail=span.summary or status)
            )
            _sink_write_event(event)
            return state

        wrapped.__name__ = name
        return wrapped

    return decorator


# --- durable sinks (sqlite trace store + knowledge-gaps table) ---
_DB_PATH = Path(__file__).resolve().parents[1] / "var" / "trace.db"
_conn: sqlite3.Connection | None = None
_conn_lock = threading.Lock()


def _db() -> sqlite3.Connection | None:
    """Return (or lazily create) the module-level sqlite connection.

    Double-checked locking: the fast path (conn already set) avoids acquiring the lock;
    the slow path (first call or after a creation failure) holds the lock while it
    creates the connection and tables, so two FastAPI worker threads can never both
    attempt creation concurrently.
    """
    global _conn
    if _conn is None:
        with _conn_lock:
            if _conn is None:  # re-check: another thread may have set it while we waited
                try:
                    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
                    _conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
                    _conn.execute(
                        "CREATE TABLE IF NOT EXISTS events (thread_id, node, ts, status, model, "
                        "tokens_in, tokens_out, latency_ms, retries, cost_usd, summary, error)"
                    )
                    _conn.execute(
                        "CREATE TABLE IF NOT EXISTS knowledge_gaps (ts, turn_id, sub_question_id, "
                        "question_text, attempted_source, reason, top_score)"
                    )
                    _conn.commit()
                except sqlite3.Error:
                    _conn = None  # best-effort: no sink rather than a crash
    return _conn


def _sink_write_event(e: Event) -> None:
    conn = _db()
    if conn is None:
        return
    try:
        conn.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                     (e.thread_id, e.node, e.ts.isoformat(), e.status, e.model, e.tokens_in,
                      e.tokens_out, e.latency_ms, e.retries, e.cost_usd, e.summary, e.error))
        conn.commit()
    except sqlite3.Error:
        pass


def record_gap(state: ConversationState, gap: KnowledgeGap) -> None:
    """Append a knowledge gap to state AND the durable sqlite table — non-blocking telemetry."""
    state.knowledge_gaps.append(gap)
    conn = _db()
    if conn is not None:
        try:
            conn.execute("INSERT INTO knowledge_gaps VALUES (?,?,?,?,?,?,?)",
                         (gap.ts.isoformat(), gap.turn_id, gap.sub_question_id, gap.question_text,
                          gap.attempted_source.value, gap.reason.value, gap.top_score))
            conn.commit()
        except sqlite3.Error:
            pass


def reset_sink() -> None:
    """Drop the sqlite tables (used by run_demo / tests for a clean trace)."""
    conn = _db()
    if conn is not None:
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM knowledge_gaps")
        conn.commit()


# --- rollups + data-out ---
def metrics_rollup(state: ConversationState) -> Metrics:
    """Compute the metrics the UI screen reads, from the recorded events + turns."""
    events = state.events
    tokens_total = sum(e.tokens_in + e.tokens_out for e in events)
    cost_total = sum(e.cost_usd for e in events)
    cost_by_agent: dict[str, float] = {}
    stage_dwell: dict[str, float] = {}
    for e in events:
        cost_by_agent[e.node] = cost_by_agent.get(e.node, 0.0) + e.cost_usd
        stage_dwell[e.node] = stage_dwell.get(e.node, 0.0) + e.latency_ms

    answered = [t for t in state.turns if t.status == TurnStatus.ANSWERED]
    partial = [t for t in state.turns if t.status == TurnStatus.ANSWERED_PARTIAL]
    abstained = [t for t in state.turns if t.status == TurnStatus.ABSTAINED]
    n_turns = max(len(state.turns), 1)

    judged = [sq for t in state.turns for sq in t.sub_questions if sq.judge_verdict is not None]
    rejects = [sq for sq in judged if sq.judge_verdict and sq.judge_verdict.value == "FAIL"]

    return Metrics(
        cycle_time=sum(stage_dwell.values()) / 1000.0,
        stage_dwell=stage_dwell,
        tokens_total=tokens_total,
        cost_total=cost_total,
        cost_by_agent=cost_by_agent,
        retries=sum(e.retries for e in events),
        judge_reject_rate=(len(rejects) / len(judged)) if judged else 0.0,
        straight_through_pct=len(answered) / n_turns * 100.0,
        partial_rate=len(partial) / n_turns * 100.0,
        abstain_rate=len(abstained) / n_turns * 100.0,
        knowledge_gap_count=len(state.knowledge_gaps),
    )


def export_data_out(state: ConversationState) -> dict:
    """The single JSON surface the UI loads (Q3: JSON fixtures behind a swappable read module)."""
    state.metrics = metrics_rollup(state)
    return json.loads(state.model_dump_json())
