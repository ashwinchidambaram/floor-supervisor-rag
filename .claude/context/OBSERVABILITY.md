# Observability Spec (reusable template)

> The same observability applies to almost any agentic system, so this is a **template, not a
> per-problem design.** It defines what to capture, how to compute cost, how to trace and debug, and
> what the metrics UI screen reads. It builds on the data-out contract in CLAUDE.md.

---

## What every node emits (the event)

Emitted by the node-template wrapper, so every node gets it for free:

```
{ thread_id, node, ts, status, model, tokens_in, tokens_out, latency_ms,
  retries, cost_usd, summary, state_delta, error? }
```

Flows to: (a) the append-only **audit log**, (b) the **trace store** (an events table),
(c) the **UI event feed**.

---

## Tokenomics / cost calculation

- **Per event:** `cost_usd = tokens_in × price_in + tokens_out × price_out`, using a per-model
  price table from the model menu (MODELS.md).
- **Roll up:** per agent, per item (thread), per run. **Deterministic steps = $0** (no tokens) —
  surface that explicitly; it's a headline of the agency-line design.
- **Track:** total cost per item, the most expensive node, tokens by agent. This is your
  "where does the cost go?" answer.

---

## Traceability

- Every event is keyed by `thread_id` (the item) + `node` + `ts`. Reconstruct any item's full path
  from its events + audit log.
- The **audit log** additionally records `actor / action / before→after` for compliance-grade
  attribution — *who or what* did each thing, not just what happened.

---

## Debugging

- **Replay from checkpoint:** load any checkpoint by `thread_id` and resume or inspect — time-travel.
- **Trace view:** the ordered event list for an item shows exactly where it went and where it
  failed. A failure at node N often stems from a bad output at node M — the trace links them.
- Surface errors, retries, and judge rejections explicitly, not buried in logs.

---

## Business metrics (the ROI layer)

Cycle time (received → ready, and → final), per-stage dwell time, throughput, % straight-through,
rework-loop count, and client-response latency where applicable. These drive the exec slide.

---

## The metrics rollup (what the UI screen reads)

A small rollup per run/item — the same shape for any problem, which is why the metrics screen is a
reusable template:

```
{ cycle_time, stage_dwell{}, tokens_total, cost_total, cost_by_agent{},
  retries, judge_reject_rate, straight_through_pct }
```

The observability / metrics UI screen (UI doc) renders this directly.

---

## Implementation note

For a local demo, a structured logger + a SQLite events table + this rollup is enough and fully
controllable. Langfuse / LangSmith are optional OpenTelemetry drop-ins for richer traces — but don't
let wiring them eat your build time. Local-first; talk about the managed tools as the production path.
