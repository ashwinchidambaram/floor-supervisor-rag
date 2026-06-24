# Progress Log

## Session 1 — UI rebrand + 3 surfaces + live Q&A + deploy

### P0 · planning-with-files init — COMPLETE
- Created `task_plan.md`, `findings.md`, `progress.md`. Plan saved to `~/.claude/plans/awesome-ok-let-me-scalable-tome.md`.

### P1 · Rebrand foundation — COMPLETE
- Read source: `personal-website/components/logo.tsx` (Orbit AC) + `lib/tokens.ts` (THEMES.cosmic exact hex).
- Wrote: `ui/src/components/logo.tsx` (OrbitMark/ACMonogram, "use client" removed); `index.html` (Space Grotesk + Inter +
  JetBrains Mono via Google Fonts; title "Floor Docs Q&A · Grounded RAG"); `tailwind.config.js` (accent/sage/gold + fonts +
  glow/card/pop shadows; body bumped to 16px; success→sage / amber→gold aliases); `index.css` (Cosmic-light `:root` hex vars,
  terracotta focus ring + selection, `.eyebrow` util); `tokens.ts` (confidenceColor/abstainTone → sage/gold/danger, terracotta
  forbidden as status); `router.ts` (3 routes + `useHashParam` for `?c=`/`?thread=`); `AppShell.tsx` (sticky glass TOP app-bar,
  Orbit mark + wordmark + 3 tabs + maker's mark; old left teal rail gone); `App.tsx` (3 branches); `pages/KnowledgeBase.tsx`
  placeholder; retinted `components/ui/{button,dialog,tooltip}.tsx`.
- **Verified:** `npm run build` GREEN (tsc + vite). Brand-color grep clean except `pages/QnaPortal.tsx` + `pages/Observability.tsx`
  (carry old `teal`/`#CC2020` classes → unstyled, rewritten in Phase 3 by design — build still green since Tailwind drops unknown classes).
### P2 · Shared read layer + fixtures — COMPLETE
- 2c fixtures: `scripts/make_ui_fixtures.py` → 3 real recorded conversations in `ui/public/` (real/safety/quality) + `kb_index.json`
  (67 chunks). Found + fixed: override question grounds a SAFE refusal (ANSWERED/HIGH, cited) — reclassified as a highlight;
  swapped the quality conv to a groundable first-article-inspection question (HIGH) + a value-not-found (ABSTAIN).
- 2a API contract frozen in findings.md; 2b `types.ts` (+view types) + `dataSource.ts` (multi-conversation getters + `ask()`
  mock↔fetch + KB getters). **`npm run build` GREEN** (bundle now includes the fixtures).

### P3 · Parallel fan-out — IN PROGRESS (4 background subagents launched)
- 3a Backend API + container — ✅ COMPLETE & VERIFIED. `src/api.py` (gated /ask → export_data_out, /health, MemorySaver,
  startup ingest), Dockerfile (bakes fastembed model), .dockerignore, render.yaml. Curl: /health ok (index_loaded true);
  /ask w/ key → ANSWERED/HIGH cited 80 N·m; no bearer → 401; blank → 400.
- 3b Ask portal (impeccable) — conversation rail + login + 6 chips + live ask() + pipeline toggle.
- 3c Observability (impeccable) — exec summary + cost/latency + threaded drill-down + `lib/observability.ts`.
- 3d Knowledge (impeccable) — corpus browse + retrieval demo + cache bands.
- Next: integrate as they land (Phase 4), then deploy (Phase 5), then verification + Playwright (Phase 6).


## Session — 2026-06-23 · Phase 6 (final gate)
- 6a: `pytest` → **18 passed in ~13s**.
- 6b: 4 parallel read-only review subagents (backend core · RAG tools+API/security · UI · LLM prompts).
  - Agency line CLEAN; brand/status discipline CLEAN; auth/security sound; no-Redis singleton fix verified.
  - Findings triaged → `docs/CODE_REVIEW.md` (Tier-1 fixes, Tier-2 prompt edits, Tier-3 deferred-w/-rationale).
- 6c: Playwright e2e driving the LIVE stack (`scripts/e2e_playwright.py`, headless Chromium 1440×900):
  - **15/15 checks PASS.** Load + backend-status pill · Knowledge (3 real docs) · Observe (exec summary) ·
    Ask login gate → unlock → happy ask (HIGH badge + "80 N·m" + citation) → abstain ("No grounded answer",
    "does not cover", no invented value) → multi-turn transcript (2 articles) · 0 console errors.
  - Screenshots: `var/e2e/01..07*.png`.
  - Test-bug fixes en route: (1) waited on a *new* `<article>` not a global text scan (stale-match);
    (2) case-insensitive badge text (CSS uppercases the label); (3) scoped multi-turn check to transcript
    articles (left rail lists recorded titles → false-match). Backend warm /ask latency measured ≈ 6.8s.
- Pending: apply triaged fixes (Tier-1 + Tier-2 prompts) → redeploy → re-verify → write RESULTS.md. Needs user
  steer on redeploy aggressiveness (live demo currently green).

## Session — 2026-06-23 · Phase 6 COMPLETE (fixes applied + redeployed + re-verified)
- Applied Tier-1 review fixes + Tier-2 prompt hardening (commit 8b6361c). Reverted table_summary prompt edit
  (would perturb the LLM-generated index → confidence band) — logged with rationale.
- Re-verified locally: pytest 18/18 · `npm run build` green · graph smoke (happy ANSWERED+cited "80 N·m"; bad ABSTAINED).
- Redeployed HF backend (confirmed new judge prompt present on the Space) + Vercel frontend (re-aliased pretty URL to
  the new build; deployed CSS now contains accent-rgb ×14 → focus rings/dividers render).
- Final LIVE e2e: **15/15**. Curl: happy ANSWERED/MEDIUM/cited "80 N", bad ABSTAINED, no-key 401, /health index_loaded:true.
- FINDING (honest, not a bug): torque query sits at the HIGH/MEDIUM score boundary; LLM-generated ingest captions make
  the band vary across cold-start rebuilds. Value+citation always correct. e2e now asserts the real invariant
  (ANSWERED + correct value + citation + non-LOW band). Documented in RESULTS.md.
- Artifacts: docs/CODE_REVIEW.md, docs/RESULTS.md, scripts/e2e_playwright.py, var/e2e/*.png.
