"""config.py — settings, the per-agent model map, and the OpenRouter client.

Role:     One place for runtime settings + the LLM client + the model-risk record.
Contract: `get_llm()` -> an OpenAI-compatible client pointed at OpenRouter.
          `complete(agent, messages)` -> str, using that agent's mapped model.
          `MODEL_MAP[agent]` -> the {model, tier, rationale, eval_metric} record.
Failure:  Missing OPENROUTER_API_KEY raises at first LLM use (not at import), so the
          offline/no-key paths (state, chunker, tests) import this module freely.

MODEL_MAP is the model-risk-management artifact (SR 11-7 flavored): every LLM agent's
model choice is recorded with a rationale + how it's evaluated, so each is defensible.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"

# Per-agent model map. Add judge/decompose/assemble here when those LLM nodes go real.
MODEL_MAP: dict[str, dict] = {
    "table_summarizer": {
        "model": "google/gemini-3-flash-preview",
        "tier": "cheap",
        "rationale": "Build-time searchable caption for TABLE chunks. The full table_markdown is "
        "returned verbatim, so the summary affects retrieval RECALL only, never answer correctness "
        "— a cheap model is the right risk/cost trade.",
        "eval_metric": "top-table retrieval hit on the table-value smoke questions",
    },
    # --- the three runtime agents (approved at the model gate) ---
    "decompose_question": {
        "model": "google/gemini-3-flash-preview",
        "tier": "cheap",
        "rationale": "Parse a multi-part question + classify each part to one source + light "
        "coreference resolution against history. Cheap/fast is sufficient; escalate only if coref weak.",
        "eval_metric": "routing accuracy + standalone-coref on hand-picked smoke questions",
    },
    "judge_grounding": {
        "model": "anthropic/claude-opus-4.8",
        "tier": "capable",
        "rationale": "The correctness lynchpin — near-zero false-PASS is the cardinal target "
        "(a false PASS = an ungrounded answer delivered). Strongest groundedness + table-value check.",
        "eval_metric": "near-zero false-PASS + failure-mode accuracy on the value-present/absent pair",
    },
    "assemble_answer": {
        "model": "anthropic/claude-sonnet-4.6",
        "tier": "mid",
        "rationale": "Grounded generation strictly from supplied chunks — faithful, strong "
        "instruction-following; table values are injected verbatim (not model-rewritten).",
        "eval_metric": "zero unsupported claims (faithfulness) + citation correctness on smoke set",
    },
}


@lru_cache(maxsize=1)
def get_llm() -> OpenAI:
    """Process-wide OpenRouter client. Raises only when first used without a key."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in .env")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=key)


def complete(agent: str, messages: list[dict], **kwargs) -> str:
    """Run a chat completion for `agent` using its mapped model. Returns the text content."""
    model = MODEL_MAP[agent]["model"]
    resp = get_llm().chat.completions.create(model=model, messages=messages, **kwargs)
    return resp.choices[0].message.content or ""


def complete_with_usage(agent: str, messages: list[dict], **kwargs) -> tuple[str, dict]:
    """Like `complete`, but also returns usage so a node can price itself:
    -> (content, {"model": str, "tokens_in": int, "tokens_out": int}).
    Pass this to `span.record_usage(**usage)` in the node so the event carries real cost."""
    model = MODEL_MAP[agent]["model"]
    resp = get_llm().chat.completions.create(model=model, messages=messages, **kwargs)
    usage = getattr(resp, "usage", None)
    return resp.choices[0].message.content or "", {
        "model": model,
        "tokens_in": getattr(usage, "prompt_tokens", 0) or 0,
        "tokens_out": getattr(usage, "completion_tokens", 0) or 0,
    }
