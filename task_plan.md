# Task Plan — UI rebrand + 3 surfaces + live Q&A + deploy

**Goal:** Rebrand the grounded-RAG demo UI to the owner's "Warm Frontier" personal style (drop Perficient),
rebuild 3 surfaces (Ask / Observe / Knowledge) for their real personas, make Q&A truly live (FastAPI +
ask→answer), and deploy a password-gated demo (Render + Vercel). Cache + cache-hit notif = NEXT thread.

**Full plan:** `~/.claude/plans/awesome-ok-let-me-scalable-tome.md`. No changes to `src/state.py`/`graph.py`/`nodes/`/`tools/` logic.

## Phases

- [x] **P0 · planning-with-files init** — status: COMPLETE
      task_plan.md / findings.md / progress.md created.

- [x] **P1 · Rebrand foundation (BARRIER)** — status: COMPLETE
      1a Orbit AC mark ported → `logo.tsx` ✓ · 1b tokens (index.css Cosmic-light + tailwind.config.js accent/sage/gold +
      Space Grotesk/Inter/JetBrains Mono + index.html fonts/title) ✓ · 1c `tokens.ts` → sage/gold/danger ✓ ·
      1d `AppShell.tsx` top app-bar + `router.ts` 3 routes + `?c=`/`?thread=` + `App.tsx` 3 branches + KnowledgeBase placeholder ✓ ·
      retinted shadcn primitives (button/dialog/tooltip). **`npm run build` GREEN.** Brand-color residue ONLY in the 2 pages
      (QnaPortal/Observability) — rewritten in Phase 3 by design.

- [x] **P2 · Freeze+implement shared read layer & fixtures (BARRIER)** — status: COMPLETE
      2a API contract → findings.md ✓ · 2b `types.ts` (+ConversationSummary/Kb*/CacheStats) + `dataSource.ts`
      (getConversations/getTurns(id)/getCorpus/getCacheStats/`ask()` mock↔fetch) ✓ · 2c fixtures: 3 real recorded
      conversations (real=HIGH·HIGH·PARTIAL·ABSTAIN, safety=HIGH PPE + HIGH grounded safe-refusal, quality=HIGH FAI + ABSTAIN)
      + `kb_index.json` (67 chunks) ✓. **`npm run build` GREEN.**
      Note: override question → grounded SAFE refusal (ANSWERED/HIGH, cited) — reclassify as a safety highlight, not a bad-path.

- [ ] **P3 · Parallel fan-out (4 subagents)** — status: IN_PROGRESS
      3a Backend API+container (MemorySaver; bad-path verified) · 3b Ask+live wiring · 3c Observe (exec summary+threaded) · 3d Knowledge.
      Exit: all 4 build green; backend boots.

- [ ] **P4 · Integration** — status: pending
      Wire VITE_API_URL + live-swap; 3-surface nav; ask end-to-end. Exit: local ask→answer cited; build green.

- [ ] **P4.5 · MIGRATE repo → /Users/ashwinchidambaram/dev/projects/floor-supervisor-rag/** — status: pending
      Entry: P4 done, NOTHING running (agents/dev server/uvicorn stopped). Steps: (1) grep absolute paths in source;
      (2) move source EXCLUDING `.venv`/`ui/node_modules`/`ui/dist`/`var/`; (3) at dest `uv venv && uv pip install -r
      requirements.txt` + `cd ui && npm install`; (4) re-verify `npm run build` + pytest + `/ask` smoke; (5) continue all
      remaining phases from the new location. Exit: new location builds + tests + api smoke green. (Redis kb index is global →
      survives, or re-run `python -m src.ingest`.)

- [ ] **P5 · Deploy (Render automated via RENDER_API_KEY + Vercel) — FROM THE NEW LOCATION** — status: pending
      Exit: live password-gated URL answers happy + bad-path; /ask 401 w/o key.

- [ ] **P6 · Full verification + code review + Playwright (FINAL GATE)** — status: pending
      6a all pytest+smokes · 6b parallel code-review subagents · 6c Playwright e2e · 6d RESULTS.md evidence.
      Exit: every element verified end-to-end; no green-washing.

## Errors encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |
