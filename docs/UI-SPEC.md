# UI SPEC — Floor-Supervisor Documentation Q&A

> The UI is a **consumer of the data-out contract only** (state + event feed + metrics rollup +
> `knowledge_gaps` + `audit_log`). Zero knowledge of agent internals; it never calls into the agents.
> It is **deterministic PLAYBACK of the recorded event feed — no live inference.** It builds against
> seeded mock data, self-validates with headless Playwright, and swaps to live data for free.
> **Stretch slice — never blocks the core.** Build with the **`/impeccable` skill**; React + Tailwind
> + shadcn; Perficient brand tokens below.
>
> This system has **no HIL interrupts**, so this spec **supersedes the review-queue / approval
> surfaces** in `.claude/context/ui-build-doc.md`. The two pages below are the surfaces for this build.

## 0. The contract the UI reads (and nothing else)
- **`ConversationState`** — `turns[]`, `current_turn`, `sub_questions[]` (text, routed_source, retrieved, judge fields, confidence), `citations[]`, `turn_confidence`, `status`, `metrics`, `knowledge_gaps[]`, `audit_log[]`, `events[]`.
- **Event feed** — `{ thread_id, node, ts, status, model, tokens_in, tokens_out, latency_ms, retries, cost_usd, summary, state_delta, error? }`.
- **Metrics rollup** — `{ cycle_time, stage_dwell{}, tokens_total, cost_total, cost_by_agent{}, retries, judge_reject_rate, straight_through_pct, partial_rate, abstain_rate, knowledge_gap_count }`.
- **No queue** (no interrupted threads — there are no HIL gates in this system).

Read via a thin read layer over the same store the agents write (the SQLite checkpointer + events table) — never by calling the agents.

## 1. Page A — Q&A portal (the supervisor's surface)
**Purpose:** a floor supervisor asks questions and gets grounded, cited answers with **honest confidence**.

**Layout:** a chat transcript scoped to one conversation (`thread_id`); a simple question input at the bottom; multi-turn history visible (follow-ups demonstrate conversation memory).

**Per turn:**
- Supervisor question bubble.
- Assistant answer, rendered **per sub-question**:
  - Grounded answer text with **inline citation chips** — `source · doc_title · §section · doc_version`. A figure citation renders as a "Figure X" chip; a **table answer renders as an actual table** from `table_markdown` (verbatim, never reformatted). Chips expand to show the supporting chunk snippet (grounding transparency).
  - A **confidence badge** per answer, plus a **turn-level badge = the min** across parts:
    - **HIGH** → green badge, answer shown plainly.
    - **MEDIUM** → amber badge, with the deterministic **"verify against §X" caveat** shown beneath.
    - **LOW / abstain** → **muted red `#B91C1C`** badge with the honest line ("I don't have grounded documentation for this — consult …"). **Never brand red.**
- A mixed multi-part turn shows grounded answers + explicit "unsure here" lines side by side (status `ANSWERED_PARTIAL`).

**States:** empty (no conversation) · playback/"thinking" (optional subtle node-by-node replay driven by the event feed) · answered · partial · abstained · error.

**Playback:** "ask" replays the seeded turn through the recorded event feed (mock) or reads live state (prod) — the page never invokes a model.

**Acceptance (Playwright):** renders a seeded conversation containing ≥1 HIGH turn, ≥1 partial turn, ≥1 abstain turn; citation chips show source + section and expand to a snippet; a table answer renders as a table; **confidence badges use the status palette and LOW ≠ brand red**; a follow-up turn shows prior context; no console errors.

## 2. Page B — Observability console (monitor the system)
**Purpose:** monitor and explain the running system. One page, sections/tabs:

1. **Live pipeline / trace** — render the compiled graph (`draw_mermaid`) and overlay the event feed so nodes light up as a turn flows. Per node: status, latency, tokens, `cost_usd`. **Deterministic nodes show `$0`; the judge shows the highest cost** — surface both explicitly. Selecting a node opens its event detail. *From: graph + event feed.*
2. **Metrics** — the rollup as cards + a small bar/timeline: cycle time, per-stage dwell, tokens + cost (`cost_by_agent`, most-expensive node = judge), retries, judge-reject rate, **straight-through / partial / abstain rates**, knowledge-gap count. *From: metrics rollup.*
3. **Knowledge-gaps log** — read-only table for the documentation team: `ts · question · attempted_source · reason (NO_SOURCE_MATCHED / LOW_RETRIEVAL / JUDGE_FAIL_AT_CAP / VALUE_NOT_FOUND) · top_score`. Filter by reason and source. This is the "where is our documentation thin?" view. *From: `knowledge_gaps`.*
4. **Item / audit detail** (optional) — full state + `audit_log` for one thread (`actor / action / before→after`), with a replay-from-checkpoint affordance. *From: state + audit_log.*

**Acceptance (Playwright):** graph renders N nodes and highlights the active node from a seeded event; metrics displays the seeded numbers including **`$0` deterministic steps and the judge as top cost**; knowledge-gaps table shows seeded rows and filters by reason; no console errors.

## 3. Brand (Perficient) + confidence palette
| Role | Token |
|---|---|
| Structural (nav, headers, chrome) | Deep teal `#154750` |
| Brand pop / primary CTA only (never floods, never status) | Brand red `#CC2020` |
| Page bg | `#F7F8F9` · Border `#E5E7EB` · Body `#1F2937` |

**Confidence / status palette — separate from brand:** HIGH = green · MEDIUM = amber · **LOW / abstain / error = muted red `#B91C1C`**. The hard rule: **LOW/abstain never uses brand red `#CC2020`** — "unsure" must never read as "brand."

**Personal maker's mark:** a small, tasteful non-brand monogram + one line ("crafted by …") in a quiet spot (sidebar or app footer) — never in the header or a brand position.

Build with the **`/impeccable` skill** for design quality on every surface, over React + Tailwind + shadcn.

## 4. Mock data (seeded — drives the background build)
A seeded conversation with: a single-source **HIGH** turn, a multi-part **partial** turn (one grounded + one LOW), an **abstain** turn, a **table** answer, and a **figure-citation** answer. A seeded **event feed** across all nodes (model/tokens/cost incl. `$0` deterministic + judge highest). A seeded **metrics rollup**. Seeded **knowledge-gaps** rows across all four `GapReason`s. Generate via the **`synthetic-data` subagent**; confirm before use.

## 5. Deterministic playback + decoupling
Both pages read recorded state + events through the read layer. "Playback" = stepping the recorded feed; **no model is ever called from the UI.** Built against the frozen contract, the UI works **unchanged** when agents emit live events.

## 6. Build order + guardrail
Kick off **at contract-freeze** (state + event schemas), **in parallel with the agent builds** (see the "Parallelizing the UI build" protocol). Build against mock → self-validate with Playwright → swap to live for free. **Stretch-slice guardrail:** time-box hard; if Playwright can't go green in budget, report which surfaces are green and fall back to `run_demo.py` — never eat into the core build.
