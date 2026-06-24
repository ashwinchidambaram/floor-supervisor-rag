# BUILD SPEC — <system name>

> Fill this from your design pass (Field Guide + Agent Design cards) and hand it to Claude Code.
> Keep it terse; CC reads it alongside CLAUDE.md. The state schema (§3) is built and confirmed
> FIRST; everything else builds against it.
>
> Interview day: `cp BUILD-SPEC-TEMPLATE.md SPEC.md` and fill SPEC.md (keep this template clean).

## 1. Problem & KPI
- **Problem (one sentence):** …
- **Primary KPI:** … **Counterweight:** … (e.g., cycle time, guarded by decision quality)
- **Users:** internal / customer-facing · **Agent authority:** acts / recommends

## 2. Agency line
| Step | LLM / Deterministic / Hybrid | Why |
|---|---|---|
| … | … | … |

## 3. State schema (BUILD & VALIDATE FIRST — confirm before proceeding)
- **Canonical object** `<Name>` fields (typed): …
- **Status enum:** … → … → …
- **Event schema:** `{ thread_id, node, ts, status, summary, state_delta }` (+ instrumentation fields per OBSERVABILITY.md)
- **Audit log:** append-only `{ ts, actor, action, before→after, detail }`

## 4. Agents (frozen contracts — the parallelization unlock)
For each, one row. Pull from the Agent Design cards.

| Agent | Role / boundary | In → Out (typed) | Tools | Guardrails | Failure handling | Tier |
|---|---|---|---|---|---|---|
| … | … | … → … | … | … | … | … |

### 4b. Tool contracts (freeze these too)
Tools are designed at agent design but their signatures freeze with the schema, so parallel builds
can target them. Implementations are mocked locally (MCP/Gateway is production-only — see the fenced
appendix; do NOT build MCP locally).

| Tool | Input (typed) | Output (typed) | Error surface | Mock or real |
|---|---|---|---|---|
| … | … | … | … | mock |

## 5. Orchestration
- **Topology:** single-agent / orchestrator-worker / …
- **Routing:** deterministic conditional edges? (default yes) / LLM-decided where: …
- **HIL gates (interrupts):** … (trigger → resume action)
- **Checkpointer:** SqliteSaver (demo) → PostgresSaver (prod)

## 6. Guardrails & judge
- **Input/output validation:** …
- **LLM-as-judge over:** … (returns `{pass|fail, reasons[]}`; fail → human)
- **Injection / PII handling:** …

## 7. Observability / data-out
- **Event feed + audit log + metrics** per §3. The UI consumes this surface.
- **Metrics to capture:** cycle time, per-stage dwell, tokens/cost per node, retries, judge-reject rate.

## 8. Build order
1. State schema + validate (confirm). 2. Walking skeleton + graph render + run_demo.
3. Freeze contracts. 4. Vertical slices (ordered by value): … 5. Stretch: UI.

## 9. Mock data
- **Needed:** … (sample documents, API responses, edge cases)
- Generate via the synthetic-data subagent; **confirm before feeding into the system.**

---

## Production mapping (REFERENCE ONLY — DO NOT BUILD)
> Claude Code: ignore this section for the build. **Local only.** This is for narration and the slide.

| Concern | Local (build this) | AWS | Azure |
|---|---|---|---|
| Agent runtime | local process | Bedrock AgentCore Runtime | Foundry Agent Service |
| State / checkpoint | SqliteSaver | AgentCore Memory / DynamoDB | Foundry memory |
| Tools | mocked interfaces | AgentCore Gateway (MCP) | Foundry tools / MCP connectors |
| Identity / auth | n/a | AgentCore Identity | Entra Agent ID |
| Observability | console + sqlite | CloudWatch GenAI / OTel | Foundry observability |
| Guardrails | in-process | Bedrock Guardrails | Foundry content safety / XPIA |
