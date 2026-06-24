#!/usr/bin/env python3
"""verify_models.py — ground MODELS.md against the live OpenRouter API.

What it does (read-only against the API; never edits MODELS.md):
  1. GET /api/v1/models  -> the live catalog. For each ID in the menu, confirm it
     resolves; if it's an alias the catalog reports a canonical_slug, record that.
  2. POST /api/v1/chat/completions with max_tokens=1 -> confirm auth + routing,
     record HTTP status + round-trip latency.
  3. Pull REAL pricing ($/M in-out) and context length straight from the catalog JSON.

Output: a report table {id, in_catalog, ping_status, latency_ms, old->new price}.
Only facts grounded in the catalog JSON or the ping result are reported.

Run:
  export OPENROUTER_API_KEY=...        # or rely on ../.env / .env auto-load below
  python verify_models.py              # full run (catalog + pings)
  python verify_models.py --no-ping    # catalog/pricing only, skip the 1-token pings
  python verify_models.py --json out.json   # also dump raw results for diffing
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# The menu, as it appears in MODELS.md, plus the live catalog ID to ping/look up.
# old_in / old_out are $/M from the MODELS.md snapshot; None where it said "verify" / "~".
# catalog_id == menu_id unless a verification pass found the menu ID isn't the
# catalog-listed form (e.g. OpenRouter lists Anthropic with dots, not hyphens;
# nemotron-3-super is listed with its full param-count slug).
# Each tuple: (menu_id, catalog_id, tier, old_in, old_out)
MENU = [
    # Capable
    ("anthropic/claude-opus-4-8", "anthropic/claude-opus-4.8", "capable", 5.0, 25.0),
    ("google/gemini-3.1-pro-preview", "google/gemini-3.1-pro-preview", "capable", 2.0, 12.0),
    ("openai/gpt-5.4", "openai/gpt-5.4", "capable", None, None),
    ("openai/o3", "openai/o3", "capable", 2.0, 8.0),
    # Mid
    ("anthropic/claude-sonnet-4-6", "anthropic/claude-sonnet-4.6", "mid", 3.0, 15.0),
    ("google/gemini-3-flash-preview", "google/gemini-3-flash-preview", "mid", 0.50, 3.0),
    ("google/gemini-2.5-pro", "google/gemini-2.5-pro", "mid", 1.25, 10.0),
    # Cheap / fast
    ("anthropic/claude-haiku-4-5", "anthropic/claude-haiku-4.5", "cheap", 1.0, 5.0),
    ("google/gemini-2.5-flash-lite", "google/gemini-2.5-flash-lite", "cheap", 0.10, 0.40),
    ("openai/gpt-4.1-mini", "openai/gpt-4.1-mini", "cheap", None, None),
    ("openai/o4-mini", "openai/o4-mini", "cheap", None, None),
    # Vision / OCR
    ("minimax/minimax-m3", "minimax/minimax-m3", "vision", 0.30, None),
    # Cost levers
    ("deepseek/deepseek-v4-pro", "deepseek/deepseek-v4-pro", "cost-lever", 0.46, 0.92),
    ("deepseek/deepseek-v4-flash", "deepseek/deepseek-v4-flash", "cost-lever", None, None),
    ("stepfun/step-3.7-flash", "stepfun/step-3.7-flash", "cost-lever", None, None),
    ("nvidia/nemotron-3-super", "nvidia/nemotron-3-super-120b-a12b:free", "cost-lever", 0.0, 0.0),
]

# At least one capable + one mid must ping green to prove the fallback chain fires.
# Uses live catalog IDs (matches MENU's catalog_id column).
FALLBACK_CHAIN = ["anthropic/claude-opus-4.8", "anthropic/claude-sonnet-4.6"]


def load_env_key() -> str | None:
    """Prefer the live env var; else read OPENROUTER_API_KEY from .env / ../.env."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    here = Path(__file__).resolve().parent
    for candidate in (here / ".env", here.parent / ".env"):
        if candidate.is_file():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v:
                        return v
    return None


def fetch_catalog(key: str) -> dict[str, dict]:
    """GET /models -> {id: entry}. Index by both id and canonical_slug for alias lookup."""
    req = urllib.request.Request(
        f"{BASE_URL}/models",
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    index: dict[str, dict] = {}
    for entry in data.get("data", []):
        eid = entry.get("id")
        if eid:
            index[eid] = entry
        slug = entry.get("canonical_slug")
        if slug and slug not in index:
            index[slug] = entry
    return index


def to_per_million(price_str) -> float | None:
    """OpenRouter pricing is $/token as a string. Convert to $/M tokens."""
    if price_str is None:
        return None
    try:
        return round(float(price_str) * 1_000_000, 4)
    except (TypeError, ValueError):
        return None


def ping(key: str, model_id: str) -> tuple[str, int | None]:
    """Minimal chat completion. Returns (status_string, latency_ms).

    max_tokens=16: the smallest value OpenAI providers accept (they reject <16).
    Still ~1 token of real generation — enough to prove auth + routing for every
    provider without tripping a provider-specific minimum.
    """
    body = json.dumps(
        {
            "model": model_id,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 16,
        }
    ).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode())
        latency = int((time.monotonic() - start) * 1000)
        if "error" in payload:
            return f"err: {str(payload['error'])[:60]}", latency
        return "200 OK", latency
    except urllib.error.HTTPError as e:
        latency = int((time.monotonic() - start) * 1000)
        detail = ""
        try:
            detail = json.loads(e.read().decode()).get("error", {}).get("message", "")
        except Exception:
            pass
        return f"{e.code} {e.reason}: {detail[:50]}", latency
    except Exception as e:  # network/timeout
        latency = int((time.monotonic() - start) * 1000)
        return f"fail: {str(e)[:50]}", latency


def fmt_price(p_in, p_out) -> str:
    def one(x):
        return "—" if x is None else (f"{x:g}")
    return f"{one(p_in)} / {one(p_out)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ping", action="store_true", help="skip the 1-token pings")
    ap.add_argument("--json", metavar="PATH", help="dump raw results to a JSON file")
    args = ap.parse_args()

    key = load_env_key()
    if not key:
        print("ERROR: OPENROUTER_API_KEY not found in env, .env, or ../.env", file=sys.stderr)
        return 2

    print(f"Fetching catalog from {BASE_URL}/models ...", file=sys.stderr)
    try:
        catalog = fetch_catalog(key)
    except Exception as e:
        print(f"ERROR: could not fetch catalog: {e}", file=sys.stderr)
        return 2
    print(f"Catalog has {len(catalog)} indexed ids.\n", file=sys.stderr)

    results = []
    for menu_id, catalog_id, tier, old_in, old_out in MENU:
        entry = catalog.get(catalog_id)
        in_catalog = entry is not None
        canonical = entry.get("canonical_slug") if entry else None
        id_corrected = catalog_id != menu_id  # menu used a stale/alias form

        new_in = new_out = ctx = None
        if entry:
            pricing = entry.get("pricing", {}) or {}
            new_in = to_per_million(pricing.get("prompt"))
            new_out = to_per_million(pricing.get("completion"))
            ctx = entry.get("context_length")

        status, latency = ("(skipped)", None)
        if not args.no_ping:
            status, latency = ping(key, catalog_id)

        results.append(
            {
                "menu_id": menu_id,
                "catalog_id": catalog_id,
                "id_corrected": id_corrected,
                "tier": tier,
                "in_catalog": in_catalog,
                "canonical_slug": canonical,
                "ping_status": status,
                "latency_ms": latency,
                "old_price": fmt_price(old_in, old_out),
                "new_price": fmt_price(new_in, new_out),
                "new_in": new_in,
                "new_out": new_out,
                "context_length": ctx,
            }
        )

    # ---- Report table ----
    print("=" * 118)
    print("VERIFICATION REPORT — MODELS.md vs live OpenRouter catalog")
    print("=" * 118)
    hdr = f"{'menu id':<32} {'cat':<4} {'ping':<10} {'ms':>6} {'old $/M':>12} {'new $/M':>12} {'ctx':>10}"
    print(hdr)
    print("-" * 118)
    for r in results:
        cat = "✓" if r["in_catalog"] else "✗"
        ctx = f"{r['context_length']:,}" if r["context_length"] else "—"
        price_chg = "" if r["old_price"] == r["new_price"] else "  $"
        print(
            f"{r['menu_id']:<32} {cat:<4} {r['ping_status'][:10]:<10} "
            f"{(r['latency_ms'] if r['latency_ms'] is not None else '—'):>6} "
            f"{r['old_price']:>12} {r['new_price']:>12} {ctx:>10}{price_chg}"
        )
        if r["id_corrected"]:
            print(f"    ↳ live catalog id: {r['catalog_id']}  (menu id is a stale alias)")

    # ---- Fallback-chain assertion ----
    print("-" * 118)
    if not args.no_ping:
        greens = {
            r["catalog_id"]
            for r in results
            if r["catalog_id"] in FALLBACK_CHAIN and r["ping_status"].startswith("200")
        }
        ok = len(greens) >= 2
        print(f"Fallback chain {FALLBACK_CHAIN}: "
              f"{'OK — both ping green' if ok else 'INCOMPLETE — ' + str(greens) + ' green'}")
    print("=" * 118)

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2))
        print(f"\nRaw results -> {args.json}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
