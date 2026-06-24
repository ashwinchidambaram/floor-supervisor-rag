# Interview Scaffold — GenAI / Forward Deployed Engineer (live build)

This is the **pre-built starter** for the 2.5-hour recorded live-build interview. The kit is the
allowed "pre-built customization." The rule is *nothing completely custom built* — so the
**scaffolding is ready, the solution is built live**.

## Layout

**Root = machine-facing (what Claude Code reads/resolves by name):**
- `CLAUDE.md` — the build constitution. CC reads this automatically.
- `.claude/context/` — CC-facing reference docs:
  - `MODELS.md` — grounded OpenRouter model menu + the verification pass.
  - `OBSERVABILITY.md` — the cross-cutting event/cost/audit/metrics template.
  - `ui-build-doc.md` — the contract-driven UI spec (the `ui-builder` subagent reads this).
  - `BUILD-SPEC-TEMPLATE.md` — copy to `docs/SPEC.md` and fill it live during the design pass.
- `.claude/agents/` — the three subagents: `scorecard-auditor`, `ui-builder`, `synthetic-data`.
- `src/` — **empty skeleton** (structure only). Build into it live, in the order in CLAUDE.md.
- `run_demo.py`, `requirements.txt`, `.env.example`, `mock_data/`, `tests/`, `ui/`.

**`docs/` = your prep reading (not built, not shipped):**
- `INTERVIEW-PLAYBOOK.md` — **start here.** The minute-by-minute walkthrough.
- `agentic-systems-design-field-guide.md` — the 7-phase design method (the spine).
- `agent-design-runbook.md` — the per-agent card you use while filling the spec.
- `slide-runbook.md` — how to build the two slides.
- `RESEARCH-REPORT.md` — deep background / evidence base.
- `HANDOFF-PROMPT.md` — paste into a fresh Claude chat to run a graded dry-run.
- `loan-system-deck.pptx` — *(add from your Downloads — the example deck)*.

## Interview-day flow (condensed — see `docs/INTERVIEW-PLAYBOOK.md`)
1. **Listen + frame** → restate, 2–3 load-bearing clarifying questions, name the KPI.
2. **Design out loud** → the 7 phases from the field guide; draw the agency line.
3. **Freeze the spec** → `cp .claude/context/BUILD-SPEC-TEMPLATE.md docs/SPEC.md` and fill it; confirm the state schema.
4. **Build** → walking skeleton first → freeze contracts → vertical slices → cross-cutting baked in.
5. **Audit** → run the `scorecard-auditor` subagent; fix the top 3.
6. **Slides** → two slides from `docs/slide-runbook.md`.
7. **Present** → exec story, then depth on the agency line.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your OPENROUTER_API_KEY
```
Night before: run the `.claude/context/MODELS.md` verification pass (ping each model you'd pick, confirm IDs resolve),
confirm Claude Code reads `CLAUDE.md`, and test pptx generation.

> The example deck is a binary and wasn't copied here automatically — drop `loan-system-deck.pptx`
> into `docs/` from your Downloads if you want it alongside the kit.
