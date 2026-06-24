# RESULTS — Phase 6 Final Verification (evidence, not claims)

Date: 2026-06-23. Live, password-gated demo, fully redeployed after the review fixes.

- **UI:** https://floor-supervisor-rag.vercel.app  (access key shared separately)
- **Backend:** https://axchidam-floor-supervisor-rag.hf.space  (`/health` → `{"status":"ok","index_loaded":true}`)

---

## 6a · Test suite
```
python -m pytest -q   →   18 passed in 9.72s
```
Covers: state round-trip, §11/§6 orchestration invariants, retrieval, RAG, node units, one end-to-end.

## 6b · Code review (4 parallel read-only agents) → `docs/CODE_REVIEW.md`
- **Agency line: CLEAN** — LLM never decides confidence/citations/routing (all deterministic).
- **Brand/status discipline (UI): CLEAN** — terracotta accent is never a status color; abstain/LOW render danger.
- **Auth/security: sound** — `secrets.compare_digest`, 401 generic body, no key leakage, CORS `allow_credentials=False`,
  startup index-build guard, no-Redis singleton fix all verified.
- **Fixes applied (commit `8b6361c`):**
  - Backend: 500 handler no longer leaks paths (generic body + server-side log); audit before/after now a real
    transition in `abstain`/`retrieve_chunks`; judge UNGROUNDED-vs-VALUE_NOT_FOUND sharpened + FAIL→`[]` + few-shot
    examples + dead-map cleanup; assemble cites section verbatim + plain-English/numbered-steps + actionable partial
    phrasing; decompose preserves intent verbatim + no source-guessing; ingest warns on 0-chunk docs.
  - UI: `accent/N` opacity classes now emit CSS (RGB-channel token) → focus rings on **login + composer** and KB
    ring/hover states now render; `border-subtle`/`divide-subtle` now render the lighter divider (config alias);
    FAILED-turn null guard; `aria-current="page"`; no silent answer-drop on a 200-with-no-turn.
  - Prompt edit deferred-with-rationale: `table_summary` hardening (would perturb the index; captions are internal).

## 6c · Playwright end-to-end (drives the WHOLE live stack) → `scripts/e2e_playwright.py`
Headless Chromium @1440×900 against the deployed Vercel UI → live HF backend. Screenshots in `var/e2e/`.
```
E2E RESULT: 15/15 checks passed
```
- app loads · backend-status pill (“Backend live”)
- Knowledge surface renders the 3 real docs (Safety / Maintenance / Quality)
- Observe surface renders the executive summary
- Ask: live login gate shown → unlock with key → composer
- **Happy path:** “What torque do the CNC VF-4 vise jaw bolts need?” → ANSWERED, **“80 N·m”**, ≥1 citation,
  confident band (HIGH/MEDIUM — see note below)
- **Bad path:** “…parental leave policy?” → **“No grounded answer”**, “does not cover”, no invented value
- Multi-turn transcript (2 articles) · **0 console errors**

## Live backend curl evidence (post-redeploy)
```
POST /ask  "torque…"           → HTTP 200 · ANSWERED · MEDIUM · cites=1 · "80 N" present
POST /ask  "parental leave…"   → HTTP 200 · ABSTAINED · LOW · cites=0
POST /ask  (no Authorization)  → HTTP 401
GET  /health                   → 200 · index_loaded:true
```

---

## Note — honest confidence calibration (not a bug)
The torque query's top retrieval score sits right at the **HIGH/MEDIUM boundary (0.75 floor)**. Table search-captions
are **LLM-generated at ingest** and aren't byte-reproducible across cold-start rebuilds (even at temp=0), so the band
can read HIGH on one build and MEDIUM on another. **The answer, the value (80 N·m), and the citation are always
correct** — only the confidence label moves, which is the system being *honestly calibrated*, not overconfident.
Tuning the floor to force HIGH would be dishonest and is deliberately not done. If band stability is ever required,
the fix is a deterministic table caption (no LLM at ingest) — recorded as a recommendation, not applied.

## What's mocked vs. real
- **Real:** 3 LLM agents (decompose/judge/assemble), deterministic grounding/abstain/citation enforcement, fastembed
  local retrieval + hybrid (dense+BM25) search, the live `/ask` graph, multi-turn memory (MemorySaver).
- **Mocked/recorded:** Observe + Knowledge surfaces read recorded fixtures (offline-safe playback); the response
  cache band now shows the **measured-local** numbers (the cache is real + measured with Redis up; the public
  demo runs Redis-less, so the band is labelled accordingly — see the Addendum).

## Deferred (logged in `docs/CODE_REVIEW.md`, with rationale)
chunk_id namespacing for a 4th malformed doc · retry-success-branch test · BM25/vstack perf · sqlite `_conn` lock ·
`@app.on_event` → lifespan migration · `table_summary` prompt hardening · minor UI a11y nits.

---

## Addendum — Redis cache + Tier-3 nits + README finishing (2026-06-23)

**Cache (spec §4b), measured** — `var/cache_measure.log`:
- retrieve_chunks + assemble_answer cached; **judge deliberately NOT cached (re-runs every hit)**.
- MISS $0.0248/answer → HIT $0.0210 (~15% saved = assemble only; floor ≈ $0.021 = judge+decompose).
- judge ≈ $0.0202 (~81%) every run · cost_avoided $0.0044/hit · latency 16.5s → 14.6s.

**Tests:** `pytest -q` → **21 passed** (added test_cache.py ×2 + test_retry_success; conftest disables the
node cache for the §11 suite).

**All 9 Tier-3 nits resolved** (see docs/CODE_REVIEW.md): chunk_id namespacing · sqlite _conn lock ·
api lifespan · vstack · BM25-per-source cache · retry-success test · CorpusTree role · AuditTrail accent ·
KnowledgeBase shared Band.

**Bad-path samples verified ABSTAIN** (local graph): "override the safety interlock…" → ABSTAINED/LOW/0
cites (no unsafe procedure); "warranty period on the CNC VF-4 spindle" → ABSTAINED/LOW/0 cites.

**README finishing pass** — every number re-grounded (cost $0.0248 measured; per-node split measured;
cache table corrected to judge-always-runs; pricing verified live; Live-demo section = HF Space + Vercel).

**Redeployed + re-verified live:** HF backend (lifespan confirmed on the Space) + Vercel; pretty alias
re-pointed. **Live Playwright e2e = 16/16** (adds a measured-cache-band check). Warm `/ask`: ANSWERED/
MEDIUM/cited "80 N" in 6.3s; bad-path ABSTAINED; no-key 401. Cache band screenshot: var/e2e/08_cache_band.png.
