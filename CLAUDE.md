# CLAUDE.md — Agentic Build Workspace

## What this repo is
A workspace for building a production-style **multi-agent system** live, under time pressure, to
demonstrate end-to-end agentic engineering. Optimize for two things at once: a **working, demoable**
system and **clear, narratable** code. Build to *run* — but never at the cost of being able to
explain it. The human driving you must be able to defend every decision out loud.

## Core philosophy (do not violate)
1. **The agency line.** Use LLMs for unstructured work (read, classify, extract, generate,
   converse). Use **deterministic code** for anything that must be correct, fair, auditable, or
   legally defensible (decisions, math, thresholds, routing, external systems of record, security).
   The LLM may *narrate* a deterministic result; it must never *produce* the result that has to be
   defensible. When unsure: "would I explain this to a regulator?" — if no, make it deterministic.
2. **LLMs are not a security boundary.** Hard controls (validation, auth, the decision itself) live
   in deterministic code around the model.
3. **Generic, not pre-baked.** Build reusable scaffolding; never hard-code a solution to one
   specific business problem. Mock all external systems behind clean interfaces. **Build for the
   domain in the active spec — any loan/BFSI examples in the supporting docs are illustrative of the
   *method*, not the domain to build.**
4. **Comment for review.** Every module/node gets a short header comment: role, contract (in→out),
   failure handling. A reviewer must understand and explain it without reading the whole file.
   (These comments double as the builder's interview talking points.)

## Build order (follow exactly)
1. **State schema first.** Define the canonical typed state object (Pydantic) + the event schema
   (see Data-out contract). Validate it with a tiny round-trip script. **Stop and confirm with the
   human before proceeding.**
2. **Walking skeleton.** Wire every node as a stub that logs its name, emits its event, and returns
   state unchanged. Add the checkpointer. Render the graph with
   `graph.get_graph().draw_mermaid_png()` (or `draw_mermaid()` for offline-safe mermaid *text* if PNG
   rendering needs a network call). Write `run_demo.py` that pushes a sample item through and
   prints the event feed. **Demo this before building any real node.**
3. **Freeze the contracts.** Once the state + per-node I/O contracts are locked, agents can be built
   in parallel against them.
4. **Vertical slices.** Make one node real end-to-end, test it, verify the output, then the next.
   Order by value (headline capability first). Never build all-then-debug.
5. **Cross-cutting, baked in once.** Observability + audit + guardrail hooks live in the node
   template (below) so every node inherits them — not a separate phase.
6. **Stretch slices last.** Richer UI, extra checks — only after the core system + script demo work.

## Parallelization protocol
- Parallelize **only after contracts are frozen** (step 3). Before that, the schema is sequential
  and the human confirms it.
- Farm **isolated leaf modules** (tool mocks, rules engine, individual agents with frozen I/O) to
  subagents. Keep **orchestration wiring** reviewable — wire it with clear comments; the human
  reviews it against the mermaid render.
- When each agent completes: return a **one-paragraph summary**, **open the file** for review, and
  ensure it carries the header comments (role, contract, failure handling).

## Repo structure (scaffold to this)
Structure mirrors the architecture, so a reviewer browsing the repo navigates by concept. CC
scaffolds this on the walking-skeleton step:

```
repo/
├── README.md              # what it is · how to run · architecture-at-a-glance · what's mocked
├── CLAUDE.md              # this file
├── requirements.txt
├── run_demo.py            # pushes a sample item through; prints the event feed
├── .claude/agents/        # scorecard-auditor · ui-builder · synthetic-data
├── .claude/context/       # CC-facing reference: MODELS · OBSERVABILITY · ui-build-doc · BUILD-SPEC-TEMPLATE
├── docs/                  # build spec(s) land here: SPEC.md / AGENTS-SPEC.md (+ prep reading)
├── src/
│   ├── state.py           # canonical typed state + enums + event/audit schemas
│   ├── graph.py           # nodes wired, edges, checkpointer, interrupts (the orchestration)
│   ├── config.py          # per-agent model map, settings, OpenRouter client
│   ├── observability.py   # event emit · cost calc · audit log · metrics rollup
│   ├── nodes/             # one file per node/agent (header: role · contract · failure)
│   ├── tools/             # tool impls, mocked behind clean interfaces
│   └── guardrails/        # validators + the LLM-as-judge
├── mock_data/             # synthetic-data output + a README of what's in it
├── tests/                 # pytest: per-node + one end-to-end
└── ui/                    # stretch slice; consumes the data-out contract only
```

Rules: one node per file in `nodes/`; `state.py` imports nothing and is imported everywhere;
`graph.py` is the *only* place edges/interrupts live (keep it readable — it's what you narrate);
external calls only ever go through `tools/`.

CC-facing reference docs live in `.claude/context/` (MODELS · OBSERVABILITY · ui-build-doc ·
BUILD-SPEC-TEMPLATE). The **build spec(s)** you fill live and build against — `SPEC.md` /
`AGENTS-SPEC.md` — live in `docs/` (copy from `.claude/context/BUILD-SPEC-TEMPLATE.md`).

## Conventions
### State
One canonical typed state object is the single source of truth. Every node reads/writes it. Enums
for status, typed sub-objects for structured data, an append-only `audit_log`, a `metrics` rollup.

### Nodes (the template every node follows)
- Signature: `state -> state` (or a partial update).
- Wrapped with: a **tracing span**, an **audit-log append**, a **try/except** that routes failure to
  a fallback/human path, and an **event emit** (Data-out contract).
- A node never silently swallows an error — it records it and degrades gracefully.

### Tools / ACI
Typed, constrained inputs (enums over free text; absolute over relative). Descriptions written like
prompts. Return typed results + an explicit error surface. Mistake-proof the foot-guns.

### LangGraph
Graph = nodes + typed state + edges. Routing via **deterministic conditional edges** unless judgment
is genuinely required. HIL gates = `interrupt()` + checkpointer; resume via `Command(resume=...)`
keyed by `thread_id` (one per work item). Checkpointer: `SqliteSaver` for the demo; note
`PostgresSaver` for production.

### Failure handling
Retries with backoff (idempotent/infra errors only), timeouts, **max-loop caps**, one fallback
model, and "escalate to human" as the ultimate degradation.

### Models / cost
Tier models: cheap for classify/extract, capable for rationale/judge. Deterministic steps cost
nothing — lean on that.

### Readability (you narrate this live; a reviewer reads it after)
- **Type everything** — Pydantic models for data, typed function signatures. Types are documentation.
- **Small, single-purpose functions.** A node should read top-to-bottom like prose; if it needs a
  paragraph to explain, split it.
- **Name things the way you'd say them out loud** — `assemble_package`, not `process2`. Good names
  beat comments that apologize for bad ones.
- **Obvious over clever.** No dense one-liners you'll have to decode on camera. Optimize for the
  reader — who is you, mid-sentence, under pressure.
- **One way to do the cross-cutting things.** The node template is the single pattern for emit /
  audit / failure, so every file looks the same and a reviewer learns it once.

### Documentation (minimum for legibility — don't gold-plate)
Document the **seams**, not every function; doc effort competes with build time.
- **README.md** (write it early — it orients a reviewer in 30s): one-line what-it-is · the agency
  line + the agent list · `python run_demo.py` to run · what's mocked vs. real.
- **The mermaid graph render**, committed as the architecture picture (free, from the skeleton step).
- **Header comments** per module (role · contract · failure) — already required; they're your
  talking points.
- **A "what's mocked vs. real" note** so a reviewer knows the demo boundary and doesn't read a
  deliberate stub as a gap.

## Default stack (use these unless there's a reason not to)
- **Language:** Python 3.11+
- **Orchestration:** LangGraph
- **Validation / schemas:** Pydantic v2
- **State / checkpoint:** SQLite via `SqliteSaver` (local) → Postgres via `PostgresSaver` (prod)
- **LLM access:** OpenRouter (OpenAI-compatible endpoint, or LangChain `ChatOpenAI` pointed at it)
- **API layer (only if a service/UI needs one):** FastAPI
- **UI:** React + Tailwind + shadcn (polished, via the `frontend-design` skill) or Streamlit (fast) — see UI doc
- **Observability:** lightweight local — structured logs + an events table + cost rollup (see `.claude/context/OBSERVABILITY.md`); Langfuse/LangSmith optional drop-in
- **Testing:** pytest · **Browser validation:** headless Playwright
- **External systems:** mocked behind clean interfaces

Defaults exist to remove dithering — deviate only with a stated reason.

## Model selection (OpenRouter)
Pick a model per agent by task type. **Concrete, grounded model IDs + pricing live in `.claude/context/MODELS.md`
(researched June 2026 — CC runs the verification pass there before building).** The tiers below map
to that menu. **Model IDs and pricing drift — confirm the live catalog at build time.**

| Tier | Use for | Example family (verify current ID) |
|---|---|---|
| Cheap / fast | classification, extraction, routing, simple checks | mini / flash / haiku-class |
| Mid | drafting, summarization, general reasoning | sonnet / gpt-class |
| Capable | rationale, the judge, hard reasoning | opus / gpt-pro-class |
| Vision | OCR / document images (if no dedicated OCR tool) | a vision-capable model |

**Selection protocol (per agent):** (1) identify the agent's task type, (2) review this menu,
(3) recommend a model + tier with a **1–2 line rationale**, (4) **ask for approval before wiring it.**

**Record per agent** (model-risk-management / SR 11-7 flavored): store
`{ agent, model, tier, rationale, eval_metric }` — e.g., *"document_worker · cheap-tier · mechanical
extraction · 94% field accuracy on golden set."* This is what lets you defend each model choice and
its validated performance if asked.

## Data-out contract (this is what enables the parallel UI build)
The UI and the observability layer are **consumers of one surface**, so they build in parallel
against it without touching agent internals:
- **State** — the canonical object is the single source of truth for "what is true now."
- **Event feed** — every node emits **one** typed event. Identity/feed fields:
  `{ thread_id, node, ts, status, summary, state_delta }`, **plus instrumentation fields**
  (`model, tokens_in, tokens_out, latency_ms, retries, cost_usd, error?`) — full shape in
  `.claude/context/OBSERVABILITY.md`. One event is emitted; each consumer reads the subset it needs. These flow to
  (a) the audit log, (b) the trace, (c) a UI event feed.
- **Queue view** — "items awaiting human review" = threads in an interrupted state (from the
  checkpointer).

A UI built against `{ state schema + event schema + queue query }` needs **zero knowledge of agent
internals** — which is exactly why it can build, test (headless Playwright), and validate in the
background while the agents are written. See the UI build doc.

## Guardrails for the build
- Validate the schema before building on it.
- Keep external systems mocked behind interfaces (swap to real later).
- Do **not** build cloud infra. **Local only.** The production/cloud mapping is reference-only
  (see the spec's fenced appendix) — for narration and the slide, never for building.
