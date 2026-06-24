// ---------------------------------------------------------------------------
// dataSource.ts — THE read seam (single import site for all pages).
//
// Role:     load the recorded conversations + the KB index, and expose typed read-only
//           getters; plus the `ask()` action (mock today, live `fetch` when VITE_API_URL
//           is set). Pages NEVER import the raw JSON or call the agents — they go through here.
// Contract: getters return the contract sub-shapes from lib/types.ts; `ask()` returns a
//           ConversationState (the export_data_out shape). See findings.md (2a/2b).
// Failure:  mock getters are validated-by-construction. `ask()` live throws on !ok/401;
//           the Ask page surfaces that (clears the key on 401).
//
// >>> TO GO LIVE <<< set VITE_API_URL → `ask()` POSTs to `${VITE_API_URL}/ask` with the
//     session bearer. Same getter shapes, zero page rework.
// ---------------------------------------------------------------------------

import type {
  AuditEntry, CacheStats, ConversationState, ConversationSummary, Event, KbCorpus,
  KnowledgeGap, KnowledgeIndex, Metrics, RetrievalDemoQuery, Turn,
} from "./types";

import realConv from "../../public/conversation_real.json";
import safetyConv from "../../public/conversation_safety.json";
import qualityConv from "../../public/conversation_quality.json";
import kbIndexJson from "../../public/kb_index.json";

// Recorded conversations (playback). Order = display order in the Ask rail.
const STATES: ConversationState[] = [realConv, safetyConv, qualityConv] as unknown as ConversationState[];
const BY_ID = new Map(STATES.map((s) => [s.conversation_id, s]));
const KB = kbIndexJson as unknown as KnowledgeIndex;

let selectedId = STATES[0].conversation_id;
export function selectConversation(id: string): void { if (BY_ID.has(id)) selectedId = id; }
export function getSelectedId(): string { return selectedId; }

function resolve(id?: string): ConversationState {
  return BY_ID.get(id ?? selectedId) ?? STATES[0];
}

const CONF_RANK: Record<string, number> = { HIGH: 3, MEDIUM: 2, LOW: 1 };

function summarize(s: ConversationState): ConversationSummary {
  let worst: Turn | undefined;
  for (const t of s.turns) {
    if (!worst) { worst = t; continue; }
    const a = t.turn_confidence ? CONF_RANK[t.turn_confidence] : 0;
    const b = worst.turn_confidence ? CONF_RANK[worst.turn_confidence] : 0;
    if (a < b) worst = t;
  }
  return {
    id: s.conversation_id,
    supervisor_id: s.supervisor_id,
    title: s.turns[0]?.question_text ?? "New conversation",
    turn_count: s.turns.length,
    worst_status: worst?.status ?? "RECEIVED",
    worst_confidence: worst?.turn_confidence ?? null,
    status: s.status,
  };
}

// --- recorded-conversation getters (id defaults to the selected conversation) ---
export function getConversations(): ConversationSummary[] { return STATES.map(summarize); }
export function getState(id?: string): ConversationState { return resolve(id); }
export function getConversation(id?: string): Pick<ConversationState, "conversation_id" | "supervisor_id" | "status" | "config"> {
  const s = resolve(id);
  return { conversation_id: s.conversation_id, supervisor_id: s.supervisor_id, status: s.status, config: s.config };
}
export function getTurns(id?: string): Turn[] { return resolve(id).turns; }
export function getCurrentTurn(id?: string): Turn | null { return resolve(id).current_turn; }
export function getEvents(id?: string): Event[] { return resolve(id).events; }
export function getMetrics(id?: string): Metrics { return resolve(id).metrics; }
export function getKnowledgeGaps(id?: string): KnowledgeGap[] { return resolve(id).knowledge_gaps; }
export function getAuditLog(id?: string): AuditEntry[] { return resolve(id).audit_log; }

// --- Knowledge Base / cache (from kb_index.json) ---
export function getCorpus(): KbCorpus { return KB; }
export function getRetrievalDemo(): RetrievalDemoQuery[] { return KB.retrieval_demo; }
export function getCacheStats(): CacheStats { return KB.cache; }

// --- the live ask action (mock ↔ fetch) ---
const API = import.meta.env.VITE_API_URL as string | undefined;
export function isLive(): boolean { return !!API; }

export async function ask(question: string, threadId: string): Promise<ConversationState> {
  if (API) {
    const key = sessionStorage.getItem("demo_access_key") ?? "";
    const res = await fetch(`${API}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
      body: JSON.stringify({ question, thread_id: threadId }),
    });
    if (res.status === 401) throw new Error("unauthorized");
    if (!res.ok) throw new Error(`ask failed (${res.status})`);
    return (await res.json()) as ConversationState;
  }
  return mockAsk(question, threadId);
}

/** Mock: echo the recorded turn whose question best matches (so offline dev demos a real answer). */
async function mockAsk(question: string, threadId: string): Promise<ConversationState> {
  const words = new Set(question.toLowerCase().split(/\W+/).filter((w) => w.length > 3));
  let best: { turn: Turn; src: ConversationState } | null = null;
  let bestScore = -1;
  for (const s of STATES) {
    for (const t of s.turns) {
      const tw = t.question_text.toLowerCase().split(/\W+/);
      const overlap = tw.filter((w) => words.has(w)).length;
      if (overlap > bestScore) { bestScore = overlap; best = { turn: t, src: s }; }
    }
  }
  const matched = best!.turn;
  const turn: Turn = { ...matched, turn_id: "t1", question_text: question };
  await new Promise((r) => setTimeout(r, 350)); // simulate latency
  return {
    conversation_id: threadId,
    supervisor_id: "demo-user",
    status: "ACTIVE",
    turns: [turn],
    current_turn: turn,
    knowledge_gaps: best!.src.knowledge_gaps.filter((g) => g.turn_id === matched.turn_id),
    config: STATES[0].config,
    audit_log: [],
    events: best!.src.events,
    metrics: STATES[0].metrics,
  } as ConversationState;
}
