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

- [x] **P3 · Parallel fan-out (4 subagents)** — status: COMPLETE (all 4 built; build green; backend boots).

- [x] **P4 · Integration** — status: COMPLETE (VITE_API_URL live-swap; 3-surface nav; ask end-to-end cited).

- [x] **P4.5 · MIGRATE repo → /Users/ashwinchidambaram/dev/projects/floor-supervisor-rag/** — status: COMPLETE.

- [x] **P5 · Deploy (HF Space backend + Vercel frontend)** — status: COMPLETE.
      LIVE: UI https://floor-supervisor-rag.vercel.app · backend https://axchidam-floor-supervisor-rag.hf.space
      (index_loaded:true). Password-gated; /ask → 401 w/o key; happy + bad-path verified. Pretty URL + maker-mark removed.

- [x] **P6 · Full verification + code review + Playwright (FINAL GATE)** — status: COMPLETE
      6a pytest — **18/18 passed.**
      6b 4 parallel review agents → docs/CODE_REVIEW.md. Agency line CLEAN · brand/status CLEAN · auth sound.
          Tier-1 fixes + Tier-2 prompt edits APPLIED (commit 8b6361c); table_summary edit deferred-w/-rationale.
      6c Playwright e2e (LIVE stack) — **15/15** (scripts/e2e_playwright.py; screenshots var/e2e/).
      6d Evidence → **docs/RESULTS.md** (real test output, curl evidence, confidence-calibration note).
      Redeployed both (HF + Vercel) after fixes; re-verified 15/15 + curl happy/bad/401. DONE.

## Errors encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |
