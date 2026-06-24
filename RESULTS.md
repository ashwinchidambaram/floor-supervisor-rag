# RESULTS — Floor-Supervisor Documentation Q&A (grounded RAG)

Real captured output. Evidence, not claims. Build per `docs/spec.md` + `docs/AGENTS-SPEC.md` + `docs/UI-SPEC.md`.

## System status: WIRED & WORKING end-to-end

The full pipeline runs with the three real LLM agents + six deterministic nodes, producing grounded,
cited answers and honest abstention. Confirmed across all four outcome types in one real conversation
(`python integration_smoke.py`, in-memory checkpointer):

| Question | Status | Confidence | Evidence |
|---|---|---|---|
| Vise jaw bolt torque | `ANSWERED` | HIGH | "80 N·m (59 ft·lb)", M12 grade 8.8 — 1 citation (Maint. Manual §4 v5.4) |
| First action for fault code 144 | `ANSWERED` | HIGH | "refill the reservoir" — 2 citations (exact-identifier → BM25 surfaced the fault table) |
| Torque **+** spindle warranty | `ANSWERED_PARTIAL` | LOW (min) | grounded torque + honest "no grounded documentation" line on warranty |
| Parental leave policy | `ABSTAINED` | LOW | deterministic honest abstention, 0 citations (no source matched) |

**Conversation metrics:** 4 turns · 18,410 tokens · **$0.0904** · 2 knowledge gaps ·
straight-through 50% / partial 25% / abstain 25% · most-expensive node **`judge_grounding` $0.0758**
(capable tier) · all deterministic nodes **$0**.

## Model gate (approved)

| Agent | Model | Tier | Eval metric | Result | Pass? |
|---|---|---|---|---|---|
| `decompose_question` | `google/gemini-3-flash-preview` | cheap | routing accuracy + standalone split | "torque + PPE" → MAINTENANCE + SAFETY; "torque + warranty" → MAINTENANCE + UNKNOWN | ✅ |
| `judge_grounding` | `anthropic/claude-opus-4.8` | capable | near-zero false-PASS + failure-mode | PASS on real torque table; FAIL/`VALUE_NOT_FOUND` on absent M30 bolt | ✅ |
| `assemble_answer` | `anthropic/claude-sonnet-4.6` | mid | faithfulness + citation correctness | "80 N·m" reproduced verbatim; citation ∈ supporting set; LOW parts untouched | ✅ |
| embedder | `fastembed bge-small-en-v1.5` (local) | — | pinned ingest == query | 67-chunk `kb` index; cosine top 0.755 on torque query | ✅ |

## Tests (offline, no API key) — 18 passed

```
$ .venv/bin/python -m pytest tests/ -q
..................                                                       [100%]
18 passed in 12.42s
```
- **`test_orchestration.py` (11)** — the §6/§11 routing invariants with forced stubs:
  grounded-happy-path, partial-answer, all-low-abstain, table-value-not-found, never-answer-ungrounded,
  always-cite, never-guess, route-only-known-sources, max-retrieval-loops, confidence-is-min, conversation-memory.
- **`test_retrieval.py` (4)** — real hybrid retrieval over the `kb` index (table-value hit, exact-identifier/BM25, source filter, doc_version carried).
- **`test_rag.py` (3)** — embeddings + cache + vector store.

State schema round-trips (`python -m src.validate_state`): dict + JSON + bare-defaults all equal.

## Architecture

`docs/architecture.mmd` — the compiled LangGraph render (9 nodes, deterministic conditional edges, no
interrupts). `python run_demo.py` prints a single-turn event feed; `python integration_smoke.py` runs
the multi-turn conversation and exports `mock_data/conversation_real.json` (the UI's data-out fixture).

## UI

React + Tailwind + shadcn (built with the `/impeccable` design system), Perficient brand tokens.
`cd ui && npm run dev` → http://localhost:5173/. Deterministic playback of the recorded data-out JSON
(no live inference); the read layer (`ui/src/lib/dataSource.ts`) swaps mock JSON → a live API with zero
page changes. Two surfaces:
- **Q&A Portal** — transcript with citation chips (expand to snippet), verbatim table answers,
  per-turn confidence badge (= min across parts), per-part breakdown, honest uncertainty/abstain lines
  in muted red `#B91C1C` (never brand red).
- **Observability** — pipeline trace (per-node status/latency/tokens/cost; deterministic $0, judge top
  cost), outcome rates, cost-by-node bars, filterable knowledge-gaps log, audit trail.

The UI now renders the **real** `integration_smoke` conversation.

## Bug found & fixed during integration

**Redis empty-URL crash (silent pipeline degradation).** `.env` carries `REDIS_URL=` (empty). Because
`config.load_dotenv()` runs when the agents import, `os.getenv("REDIS_URL", default)` returned the empty
string (the var *is* set), so `redis.from_url("")` raised — `retrieve_chunks` caught it, marked the turn
FAILED, and the whole pipeline degraded to abstain. It only surfaced in the full chain (in isolation
`config` was never imported, so the default applied). Fixed in `src/tools/redis_client.py`: read the URL
lazily and treat empty/whitespace as the local default. Re-verified: full pipeline → ANSWERED/HIGH with
the 80 N·m citation.

## Documented gaps / scope cuts (agreed)

- **No Redis prompt cache** (SPEC §4b stretch) — dropped for time. The Redis layer exists and is used
  for the vector store; the prompt-cache wrapper was not wired.
- **No golden dataset** — replaced by hand-picked real-corpus smoke questions asserted inline + the
  integration smoke pass (above). The §11/§6 stub-driven invariant tests are kept (they prove the
  grounding/never-guess routing, not retrieval quality).
- **Figures unexercised** — the corpus has no figures, so `FIGURE` handling (cite-by-`figure_ref`) is
  built but not demonstrated end-to-end.
- **`doc_version` ≥2-versions test deferred** — `doc_version` is captured on every chunk/citation, but
  the version-mixing grounding test was not authored (single version per doc).
- **Demos use an in-memory checkpointer** (`MemorySaver`) to avoid on-disk `checkpoints.db` growth;
  `build_graph()` still defaults to `SqliteSaver` (the production-shaped path), `PostgresSaver` in prod.
