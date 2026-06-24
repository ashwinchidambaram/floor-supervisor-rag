# CC Handover — wire & test the agents (paste into Claude Code)

You're implementing the three LLM agents for the floor-supervisor documentation Q&A system and baking
in observability. The orchestration is frozen and the deterministic nodes + walking skeleton are
built. **Read `CLAUDE.md`, `docs/SPEC.md`, and `docs/AGENTS-SPEC.md` before you start**, including the
new "Parallelizing agent builds" protocol in `CLAUDE.md`.

## 0. Pre-flight (before any agent code)
- **Land the schema deltas.** Confirm `src/state.py` carries the two additions from AGENTS-SPEC.md: the `JudgeFailureMode` enum (`IRRELEVANT` · `UNGROUNDED` · `VALUE_NOT_FOUND`) and the two `SubQuestion` fields `supporting_chunk_ids: list[str]` and `judge_failure_mode: JudgeFailureMode | None`. If missing, add them and **re-run the state round-trip validation**. The schema is the freeze point; agents build against it, so this is first and non-negotiable.
- **Confirm the skeleton is green:** graph renders, `run_demo.py` prints the event feed, and the offline orchestration tests (SPEC.md §11) pass with the LLM nodes as stubs. If any of that is red, fix it before adding agents.

## 1. Model gate — STOP for ONE approval
Before wiring **any** model: run the `.claude/context/MODELS.md` verification pass (ping each candidate, confirm IDs resolve + current pricing). Then propose all four picks in a **single table** and wait for one approval:

| agent | model | reasoning (1–2 lines) | cost (in/out per 1M) | alternative |
|---|---|---|---|---|
| decompose_question (cheap→mid) | | | | |
| judge_grounding (capable) | | | | |
| assemble_answer (mid) | | | | |
| embedder (embedding — pinned identical at ingest + query) | | | | |

Do not build until I approve the table. Record `{agent, model, tier, rationale, eval_metric}` per agent.

## 2. Build the three agents — in parallel, against frozen contracts
Contracts are frozen and disjoint, so build concurrently per the `CLAUDE.md` parallelization protocol — **one subagent per agent**, each scoped to ONLY its own contract:

- **`decompose_question`** — resolve coreference against `turns`, split along source lines (one `DocSource` per sub-question), classify, cap at 6 (overflow → log a gap, never drop), ambiguous → `UNKNOWN`. Reads `current_turn.question_text` + `turns`; writes `sub_questions[].{text, proposed_source}`.
- **`judge_grounding`** — fail-closed `PASS/FAIL` + `judge_reasons` + `judge_failure_mode` + `supporting_chunk_ids` (deterministically checked ⊆ retrieved ids); for `TABLE` chunks, PASS only if the asked-for value is unambiguously present.
- **`assemble_answer`** — HIGH/MEDIUM parts only, grounded strictly in `supporting_chunk_ids`; table values verbatim; figures cited by `figure_ref`; emits answer fragments + `citations[]`; **never sees conversation history**.

Each agent file carries header comments (role · contract · failure). On completion per agent: **one-paragraph summary · open the file · run its eval · report**. Keep `graph.py` wiring sequential and reviewable against the mermaid render — don't farm the wiring out.

**Golden sets** via the `synthetic-data` subagent — small, realistic; confirm before running. Load-bearing cases (they prove the invariants, not filler): the **table value-present vs value-absent pair**, off-topic retrieval (`IRRELEVANT`), related-but-not-answering (`UNGROUNDED`), coref follow-ups, and an **exact-identifier (part/tag) query** to confirm hybrid/BM25 surfaces it. Note provenance in `RESULTS.md`.

## 3. Observability & monitoring — bake into the node template once
Cross-cutting, baked into the node-template wrapper so **every** node (agent and deterministic) inherits it — not a separate phase. Per `.claude/context/OBSERVABILITY.md`:

- **Node-template wrapper** around every node: a tracing span · an audit-log append (`actor / action / before→after`) · a `try/except` that degrades safely (record the error, route to the safe/abstain path — never silently swallow) · exactly **one** typed event emit.
- **Event (one per node):** `{ thread_id, node, ts, status, model, tokens_in, tokens_out, latency_ms, retries, cost_usd, summary, state_delta, error? }`. Flows to (a) the append-only audit log, (b) the trace store (a sqlite events table), (c) the UI event feed.
- **Cost:** `cost_usd = tokens_in×price_in + tokens_out×price_out` from the MODELS.md price table. **Deterministic nodes emit `cost_usd = 0` — surface that explicitly** (it's a headline of the agency-line design). The **judge is the most expensive node** (capable tier) — the rollup must show the most-expensive node and tokens-by-agent.
- **Metrics rollup** (what the metrics UI screen reads): `{ cycle_time, stage_dwell{}, tokens_total, cost_total, cost_by_agent{}, retries, judge_reject_rate, straight_through_pct, partial_rate, abstain_rate, knowledge_gap_count }`.
- **Knowledge-gaps sink:** `assess_confidence` appends every LOW/UNKNOWN part to `knowledge_gaps` AND to a durable sqlite table — non-blocking telemetry for the doc team. Wire it now; it's part of observability, not a stretch.
- **Debuggability:** every event keyed by `thread_id + node + ts` so any item's full path reconstructs from events + audit log; support replay-from-checkpoint by `thread_id`.
- **Monitoring signals to surface** (metrics screen + end-of-run summary): judge reject rate and, on the golden set, **false-PASS rate**; **cost per item + most expensive node**; straight-through / partial / abstain rates; retries; knowledge-gap count + top gap reasons. These are the "is it working / where's the cost / where's the documentation thin" answers — the narration leans on them.

The UI is **deterministic playback** of this recorded feed (no live inference). Don't build live inference into the screens.

## 4. Eval & verify — STOP if red
- Run each agent's eval vs its golden set; capture **REAL** output into `RESULTS.md` per the per-agent table `{ agent · model · metric · golden N · result · pass? }`. Hard targets: **judge near-zero false-PASS**, **assembler zero unsupported claims** (faithfulness), decompose routing accuracy + coref pass.
- Re-run the offline orchestration tests (SPEC.md §11) — they stay stub-driven and must remain green. Add one **integration smoke pass** with the approved models over the golden questions that prints the event feed + the metrics rollup.
- If any eval can't pass, **STOP and report exactly what and why.** Never fake a number, never green-wash.

## 5. Autonomy
After the model-gate approval (step 1), run to completion **unattended**: parallel agent builds → observability baked in → evals → `RESULTS.md` with real output. The only stop after approval is a red you genuinely can't make green — then stop and report it.
