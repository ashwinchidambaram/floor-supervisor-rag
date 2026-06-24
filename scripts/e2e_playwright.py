"""e2e_playwright.py — drive the WHOLE deployed system end-to-end (Phase 6c).

Headless Chromium against the live Vercel UI (which talks to the live HF backend).
Verifies the real user journeys:
  1. App loads; backend-status pill renders.
  2. Knowledge surface renders the real corpus (3 docs).
  3. Observe surface renders the executive summary.
  4. Ask surface shows the live login gate; a bad key is NOT required to proceed
     with the real key; the gate unlocks.
  5. Happy path: ask the torque question -> ANSWERED, "High confidence", "80 N",
     at least one citation chip.
  6. Bad path: ask an out-of-corpus question -> "No grounded answer" (honest abstain,
     no invented value).
  7. Multi-turn: both turns remain in the transcript (thread memory in the UI).

Run: python -m scripts.e2e_playwright
Env: E2E_BASE_URL (default the Vercel URL), DEMO_ACCESS_KEY (default the demo key).
Artifacts: screenshots under var/e2e/.
"""

from __future__ import annotations

import os
import pathlib
import sys

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

BASE = os.getenv("E2E_BASE_URL", "https://floor-supervisor-rag.vercel.app")
KEY = os.getenv("DEMO_ACCESS_KEY", "u75ZYhCMHypsDZs3")
OUT = pathlib.Path("var/e2e")
OUT.mkdir(parents=True, exist_ok=True)

HAPPY_Q = "What torque do the CNC VF-4 vise jaw bolts need?"
ABSTAIN_Q = "What is the company's parental leave policy?"

ANSWER_TIMEOUT = 240_000  # ms — HF free Space can cold-start + run 3 LLM calls

results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f"  · {detail}" if detail else ""), flush=True)


def shot(page, name: str) -> None:
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)


def nav(page, label: str) -> None:
    """Click a primary-nav tab by its label."""
    page.get_by_role("navigation", name="Primary").get_by_role("button", name=label, exact=True).click()
    page.wait_for_timeout(500)


def ask_question(page, question: str) -> str:
    """Type a question into the composer and submit; wait for a NEW answer card to
    appear (article count increases) and resolve, then return that card's text.

    Scoping to the newest <article> avoids matching the prior turn's stale text — the
    transcript keeps every turn, so a global text scan would false-match immediately.
    """
    before = page.locator("article").count()
    box = page.get_by_role("textbox", name="Ask a question")
    box.click()
    box.fill(question)
    # Wait for React to enable the send button (canSend) before clicking.
    send = page.get_by_role("button", name="Send question")
    page.wait_for_function(
        "() => { const b = document.querySelector('button[aria-label=\"Send question\"]'); return b && !b.disabled; }",
        timeout=10_000,
    )
    send.click()
    # 1) a new article appears, then 2) its answer resolves (badge or abstain notice).
    page.wait_for_function(
        f"() => document.querySelectorAll('article').length > {before}",
        timeout=ANSWER_TIMEOUT,
    )
    last = page.locator("article").last
    last.locator(
        "text=/High confidence|Medium confidence|Low confidence|No grounded answer/"
    ).first.wait_for(timeout=ANSWER_TIMEOUT)
    page.wait_for_timeout(400)
    return last.inner_text()


def main() -> int:
    print(f"E2E against {BASE}  (key ****{KEY[-4:]})\n")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        console_errors: list[str] = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)

        # --- 1. Load + backend status -------------------------------------
        page.goto(BASE, wait_until="networkidle", timeout=60_000)
        check("app loads (title)", "Floor Docs Q&A" in page.title() or page.locator("text=Floor Docs").count() > 0,
              page.title())
        # BackendStatus pill: dot always renders; label appears on wide viewport.
        page.wait_for_timeout(2500)  # let /health resolve
        body = page.inner_text("body")
        check("backend status pill present",
              any(s in body for s in ("Backend live", "Backend waking", "Backend offline", "Checking backend")),
              next((s for s in ("Backend live", "Backend waking", "Backend offline", "Checking backend") if s in body), ""))
        shot(page, "01_loaded")

        # --- 2. Knowledge surface -----------------------------------------
        nav(page, "Knowledge")
        page.wait_for_timeout(800)
        kb = page.inner_text("body")
        check("knowledge: route", "#/knowledge-base" in page.url, page.url)
        check("knowledge: 3 real docs render",
              all(d in kb.upper() for d in ("SAFETY", "MAINTENANCE", "QUALITY")))
        shot(page, "02_knowledge")

        # --- 3. Observe surface -------------------------------------------
        nav(page, "Observe")
        page.wait_for_timeout(800)
        ob = page.inner_text("body")
        check("observe: route", "#/observability" in page.url, page.url)
        check("observe: executive summary",
              "EXECUTIVE SUMMARY" in ob.upper() or "Executive summary" in ob)
        shot(page, "03_observe")

        # --- 4. Ask surface: login gate -----------------------------------
        nav(page, "Ask")
        page.wait_for_timeout(600)
        check("ask: login gate shown (live mode)",
              page.locator("#access-key").count() > 0
              and ("RESTRICTED" in page.inner_text("body").upper()))
        shot(page, "04_login_gate")

        page.locator("#access-key").fill(KEY)
        page.get_by_role("button", name="Unlock").click()
        page.wait_for_timeout(800)
        check("ask: unlocked (composer visible)",
              page.get_by_role("textbox", name="Ask a question").count() > 0)
        shot(page, "05_unlocked")

        # --- 5. Happy path -------------------------------------------------
        print(f"\n  asking (happy): {HAPPY_Q}")
        try:
            txt = ask_question(page, HAPPY_Q)
            # Badge label is CSS-uppercased, so inner_text() yields "HIGH CONFIDENCE".
            check("happy: HIGH confidence badge", "high confidence" in txt.lower())
            check("happy: grounded value '80 N' present", "80 N" in txt)
            # citation chip — at least one source label in THIS answer card
            card = page.locator("article").last
            check("happy: at least one citation",
                  card.locator("text=/Maintenance|Safety|Quality|§|Section/i").count() > 0)
        except PWTimeout:
            check("happy: answer resolved", False, "timed out waiting for answer")
        shot(page, "06_happy_answer")

        # --- 6. Bad path (abstain) ----------------------------------------
        print(f"\n  asking (abstain): {ABSTAIN_Q}")
        try:
            txt = ask_question(page, ABSTAIN_Q)
            check("abstain: 'No grounded answer' notice", "no grounded answer" in txt.lower())
            check("abstain: honest non-answer (no invented value)",
                  "does not cover" in txt.lower())
        except PWTimeout:
            check("abstain: answer resolved", False, "timed out waiting for answer")
        shot(page, "07_abstain_answer")

        # --- 7. Multi-turn memory (both turns present in transcript) -------
        # Scope to the transcript articles (not the page body — the left rail also
        # lists recorded conversation titles, which would false-match).
        articles = page.locator("article")
        joined = "\n".join(articles.all_inner_texts())
        check("multi-turn: both turns in transcript",
              articles.count() >= 2 and HAPPY_Q[:24] in joined and ABSTAIN_Q[:24] in joined,
              f"{articles.count()} articles")

        # --- console errors -----------------------------------------------
        real_errs = [e for e in console_errors if "favicon" not in e.lower()]
        check("no console errors", len(real_errs) == 0,
              f"{len(real_errs)} error(s)" + (f": {real_errs[0][:80]}" if real_errs else ""))

        browser.close()

    # --- summary ----------------------------------------------------------
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{'='*52}\n  E2E RESULT: {passed}/{total} checks passed")
    if passed < total:
        print("  FAILURES:")
        for name, ok, detail in results:
            if not ok:
                print(f"   - {name}  {detail}")
    print(f"  screenshots: {OUT}/")
    print("=" * 52)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
