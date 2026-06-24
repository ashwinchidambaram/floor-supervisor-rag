# UI Build Doc: Contract-Driven, Background-Built

> The UI is a **consumer of the data-out contract** (CLAUDE.md), never a participant in the agents.
> Because it's decoupled, it builds and validates *in the background* while the agents are written,
> and is simply *ready* when you present — no "let me build the UI now" pause.

---

## The principle

The UI reads three things and nothing else: the **canonical state object**, the **event feed**
(`{ thread_id, node, ts, status, summary, state_delta }`), and the **queue** (threads in an
interrupted state). It has zero knowledge of agent internals. That decoupling is the whole trick —
the UI can be built against sample data the moment the schemas freeze, long before any agent is done.

*(Note: `frontend-design` is a **skill** — design guidance + tokens — not an agent. You create a
`ui-builder` subagent that *uses* the skill.)*

---

## The background build loop (it runs itself)

1. **Kick off at contract-freeze.** Once the state + event schemas are locked, launch the
   `ui-builder` subagent — in parallel with the agent builds.
2. **Build against mock data.** It uses sample state + a seeded event feed (from the synthetic-data
   subagent) so it never waits on the agents.
3. **Self-validate with headless Playwright.** Each surface must render, show the seeded data, have
   no console errors, and respond to key interactions. The subagent iterates until Playwright is green.
4. **Swap to live data for free.** When agents emit real events, the UI already works — same contract.
5. **Guardrail: the UI is a stretch slice.** It never blocks the core. If Playwright can't get it
   green in the time budget, fall back to the `run_demo.py` script demo. Time-box it hard.

---

## The surfaces (derived from the contract, not hard-coded)

The subagent decides what to build from the spec + contract, by these rules:

- **Pipeline / live graph view** — render the compiled graph (`draw_mermaid`) and overlay the event
  feed so nodes light up as an item flows. *Derived from: the graph + event feed.*
- **Review queue + HIL screens** — **one review screen per HIL gate in the spec.** The queue is
  "threads in an interrupted state." Each screen shows the assembled item + the agent's
  recommendation/rationale + that gate's actions (approve / deny / re-run / escalate), and the action
  fires a `Command(resume=…)`. *Derived from: HIL gates + state.*
- **Observability / metrics screen** — per-stage dwell time, end-to-end cycle time, tokens/cost,
  retries, judge-reject rate. *Derived from: metrics rollup + event feed.*
- **Item detail / audit trail** (optional) — full state + `audit_log` for one item. *Derived from:
  state + audit_log.*

🔑 The rule the subagent follows: *for every HIL gate, generate a review screen; render the graph;
build a metrics screen from the metrics rollup.* Surfaces fall out of the contract — so the subagent
determines what's needed without you hand-listing screens.

---

## Design system — Perficient brand

Tokens (per Brandfetch; verify against Perficient's brand guidelines if you have them):

| Role | Color |
|---|---|
| Brand red ("Thunderbird") | `#CC2020` |
| Deep teal ("Elephant") | `#154750` |
| White | `#FFFFFF` |
| Surface / page bg | `#F7F8F9` |
| Border | `#E5E7EB` |
| Body text | `#1F2937` |

**The one trap to avoid:** brand red and "error/denied" red collide. Resolve it by role —
- **Brand red `#CC2020`** = brand moments only (header accent, primary CTA), used as *pops*, not floods.
- **Deep teal `#154750`** = primary structural color (nav, headers, key UI chrome).
- **Status colors are separate:** green = approved, amber = pending/in-review, and for denied/error
  use a distinct muted red (e.g., `#B91C1C`) — never the bright brand red, so "denied" never reads
  as "brand."

Build with the `frontend-design` skill (React + Tailwind + shadcn). Red is strong — give it room;
let it define hierarchy, not fill blocks.

**Personal maker's mark.** Place a small, tasteful **personal logo** in a quiet spot — the sidebar
footer or the app footer — as a "crafted by [you]" attribution, clearly separate from the client and
Perficient branding (different size, no brand color). It signals ownership and craft without
competing with the client's identity. Keep it subtle: a small monogram or logo + one line of text,
never in the header or a brand position. Swap a real `<img>` logo in where the placeholder mark sits.

---

## Tech choices

- **Polished path (recommended for the background build):** React + Tailwind + shadcn via the
  `frontend-design` skill. Looks like a real product. Because the subagent builds it in the
  background, the heavier build cost doesn't cost *you* time.
- **Fast path (fallback):** Streamlit — reads state/events directly, minimal code. Good if you're
  driving it yourself and want speed over polish.
- Either way it consumes the contract via a thin read layer over the same store (the SQLite
  checkpointer + an events table), not by calling into the agents.

---

## Validation contract (so it can self-verify with Playwright)

Define a per-surface acceptance check the subagent runs headlessly and iterates against:
- **Graph view** renders N nodes and highlights the active node from a seeded event.
- **Queue** shows the seeded interrupted items; opening one shows the item detail.
- **Review screen** approve/deny fires the resume and the item leaves the queue.
- **Metrics screen** displays the seeded numbers (cycle time, dwell, tokens, retries).

When all checks pass on mock data, the UI is "demo-ready" and will work unchanged on live data.

---

## What you actually present

Show the **live graph view** as an item flows, open a **HIL review screen** and approve to resume,
then the **metrics screen**. Narrate what's happening. If anything's not green, the script demo is
your fallback — and saying "the UI's a stretch I validated separately; here's the system running" is
a perfectly senior move.
