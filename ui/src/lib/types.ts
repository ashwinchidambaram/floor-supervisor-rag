// ---------------------------------------------------------------------------
// types.ts — TypeScript mirror of src/state.py (the canonical data-out contract).
//
// Role:     The single typed vocabulary both pages (Q&A portal, Observability
//           console) import. Mirrors the Pydantic schema 1:1 so the UI is a pure
//           consumer of the data-out JSON — zero knowledge of agent internals.
// Contract: A data-out export is one `ConversationState`. The graph processes ONE
//           turn per invocation; `conversation_id === thread_id`. `page` is always
//           `null` in this corpus (no figures), kept for schema fidelity.
// Failure:  These are structural types only. The read layer (dataSource.ts) is the
//           single place that loads + validates shape; nothing here touches I/O.
//
// SOURCE OF TRUTH: src/state.py. If the Pydantic schema changes, change this file.
// ---------------------------------------------------------------------------

// --- Enums (mirror state.py; string unions, no free-text status) -----------

/** RetrievedChunk.source / Citation.source / SubQuestion.routed_source. */
export type DocSource =
  | "SAFETY_PROCEDURES"
  | "MAINTENANCE_MANUALS"
  | "QUALITY_CONTROL"
  | "UNKNOWN";

/** How a retrieved unit / citation renders: prose, a table, or a figure ref. */
export type ElementType = "PROSE" | "TABLE" | "FIGURE";

/** Turn lifecycle. Terminal states the UI keys off: ANSWERED / ANSWERED_PARTIAL / ABSTAINED / FAILED. */
export type TurnStatus =
  | "RECEIVED"
  | "DECOMPOSED"
  | "ROUTED"
  | "RETRIEVED"
  | "JUDGED"
  | "ASSESSED"
  | "ASSEMBLED"
  | "ANSWERED"
  | "ANSWERED_PARTIAL"
  | "ABSTAINED"
  | "FAILED";

/** Conversation-level status. */
export type ConversationStatus = "ACTIVE" | "ENDED";

/** Grounding judge verdict per sub-question. */
export type JudgeVerdict = "PASS" | "FAIL";

/** Typed reason a judge FAILed — drives the deterministic GapReason downstream. */
export type JudgeFailureMode = "IRRELEVANT" | "UNGROUNDED" | "VALUE_NOT_FOUND";

/** Confidence per sub-question and per turn (turn = min across parts). */
export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";

/** Why a part could not be grounded — the knowledge-gaps taxonomy (all four surface in mock). */
export type GapReason =
  | "NO_SOURCE_MATCHED"
  | "LOW_RETRIEVAL"
  | "JUDGE_FAIL_AT_CAP"
  | "VALUE_NOT_FOUND";

// --- Typed sub-objects (mirror state.py) -----------------------------------

/** One retrieved unit. TABLE chunks carry the verbatim table in `table_markdown`. */
export interface RetrievedChunk {
  chunk_id: string;
  source: DocSource;
  doc_title: string;
  doc_version: string;
  section: string;
  page: number | null;
  element_type: ElementType;
  text: string;
  table_markdown: string | null;
  figure_ref: string | null;
  score: number;
}

/** A citable handle on a delivered fragment. `snippet` is the quoted grounding shown on chip-expand. */
export interface Citation {
  chunk_id: string;
  source: DocSource;
  doc_title: string;
  doc_version: string;
  section: string;
  page: number | null;
  element_type: ElementType;
  figure_ref: string | null;
  snippet: string;
}

/** One decomposed part of the supervisor's question, carried through the pipeline. */
export interface SubQuestion {
  id: string;
  text: string;
  proposed_source: DocSource;
  routed_source: DocSource;
  retrieved: RetrievedChunk[];
  retrieval_attempts: number;
  judge_verdict: JudgeVerdict | null;
  judge_reasons: string[];
  judge_failure_mode: JudgeFailureMode | null;
  supporting_chunk_ids: string[]; // judge-approved chunks the assembler may cite
  confidence: ConfidenceLevel | null;
}

/** Append-only telemetry: a part we could not ground. Feedback for the docs team, never an escalation. */
export interface KnowledgeGap {
  ts: string; // ISO-8601
  turn_id: string;
  sub_question_id: string;
  question_text: string;
  attempted_source: DocSource;
  reason: GapReason;
  top_score: number | null;
}

/** One Q->A exchange. The UI derives the supervisor/assistant bubbles from question_text + answer_text. */
export interface Turn {
  turn_id: string;
  question_text: string;
  sub_questions: SubQuestion[];
  answer_text: string | null;
  citations: Citation[];
  turn_confidence: ConfidenceLevel | null;
  status: TurnStatus;
  ts: string; // ISO-8601
}

/** One typed event per node (data-out contract). Deterministic nodes emit cost_usd = 0. */
export interface Event {
  thread_id: string;
  node: string;
  ts: string; // ISO-8601
  status: string;
  model: string | null;
  tokens_in: number;
  tokens_out: number;
  latency_ms: number;
  retries: number;
  cost_usd: number;
  summary: string;
  state_delta: Record<string, unknown>;
  error: string | null;
}

/** Append-only, compliance-grade attribution: who/what did each thing, before -> after. */
export interface AuditEntry {
  ts: string; // ISO-8601
  actor: string;
  action: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  detail: string;
}

/** The rollup the Observability metrics view reads. */
export interface Metrics {
  cycle_time: number;
  stage_dwell: Record<string, number>;
  tokens_total: number;
  cost_total: number;
  cost_by_agent: Record<string, number>;
  retries: number;
  judge_reject_rate: number;
  straight_through_pct: number;
  partial_rate: number;
  abstain_rate: number;
  knowledge_gap_count: number;
}

/** Per-conversation knobs. Floors gate the deterministic confidence decision. */
export interface RunConfig {
  top_k: number;
  max_retrieval_loops: number;
  high_score_floor: number;
  min_score_floor: number;
}

// --- Canonical object (mirror state.py ConversationState) -------------------

/** The single source of truth. One per supervisor conversation; conversation_id === thread_id. */
export interface ConversationState {
  conversation_id: string;
  supervisor_id: string;
  status: ConversationStatus;
  turns: Turn[]; // persisted history = conversation memory
  current_turn: Turn | null; // transient working object for the latest invocation
  knowledge_gaps: KnowledgeGap[];
  config: RunConfig;
  audit_log: AuditEntry[];
  events: Event[];
  metrics: Metrics;
}

// --- UI view types: multi-conversation list (Ask rail) ----------------------
export interface ConversationSummary {
  id: string;
  supervisor_id: string;
  title: string;                       // derived from the first turn's question
  turn_count: number;
  worst_status: TurnStatus;            // worst outcome across turns (rail status dot)
  worst_confidence: ConfidenceLevel | null;
  status: ConversationStatus;
}

// --- Knowledge Base / cache (from public/kb_index.json) ---------------------
export interface KbChunk {
  chunk_id: string;
  element_type: ElementType;
  text: string;
  table_markdown: string | null;
}
export interface KbSection { section: string; chunks: KbChunk[]; }
export interface KbDocument {
  source: DocSource;
  doc_title: string;
  doc_number: string | null;
  doc_version: string;
  effective_date: string | null;
  supersedes: string | null;
  counts: { chunks: number; sections: number; tables: number; prose: number };
  sections: KbSection[];
}
export interface RetrievalDemoResult {
  chunk_id: string;
  section: string;
  element_type: ElementType;
  doc_version: string;
  score: number;
  snippet: string;
  table_markdown: string | null;
}
export interface RetrievalDemoQuery { query: string; source: DocSource; results: RetrievalDemoResult[]; }
export interface CacheNamespace { key: string; purpose: string; entries: number | null; }
export interface CacheStats {
  embedding: {
    status: string; namespace: string; entries: number | null;
    ttl_seconds: number; embedding_model: string; note: string;
  };
  response: {
    status: string; namespaces: CacheNamespace[];
    metrics_preview: { hit_rate: number | null; entries: number | null; cost_avoided_usd: number | null };
    activation_note: string;
  };
}
export interface KbCorpus {
  vector_store: { backend: string; metric: string; embedding_model: string; dim: number };
  totals: { chunks: number; documents: number; sections: number; tables: number; prose: number };
  documents: KbDocument[];
}
export interface KnowledgeIndex extends KbCorpus {
  retrieval_demo: RetrievalDemoQuery[];
  cache: CacheStats;
}
