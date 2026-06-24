# MODELS.md — OpenRouter Model Menu (grounded, June 2026)

> Real model IDs + pricing as of **June 2026** via OpenRouter. **Prices and IDs drift — CC runs a
> verification pass (below) before the build to confirm each ID resolves and connects.** OpenRouter
> is OpenAI-compatible: set `base_url="https://openrouter.ai/api/v1"` + your key, switch models by
> changing the model string. Supports fallback routing if a provider is down. ~5.5% fee baked into credits.
>
> **Last verified 2026-06-23** against the live `/api/v1/models` catalog via `verify_models.py` —
> all 16 menu IDs resolve and ping green (capable→mid fallback confirmed). Re-run before the build:
> `python verify_models.py`.

---

## The menu (by tier)

### Capable — judgment, the judge, hard reasoning
| Model | OpenRouter ID | $/M in–out | Context | Notes |
|---|---|---|---|---|
| Claude Opus 4.8 | `anthropic/claude-opus-4.8` | 5 / 25 | 1M | Anthropic flagship; strong agentic + reasoning |
| Gemini 3.1 Pro Preview | `google/gemini-3.1-pro-preview` | 2 / 12 | 1M | Frontier reasoning; notably strong in **finance / structured** domains |
| GPT-5.4 | `openai/gpt-5.4` | 2.5 / 15 | 1M | OpenAI flagship |
| OpenAI o3 | `openai/o3` | 2 / 8 | 200K | Reasoning model; price dropped ~80% |

### Mid — drafting, rationale narration, general reasoning
| Model | OpenRouter ID | $/M in–out | Context | Notes |
|---|---|---|---|---|
| Claude Sonnet 4.6 | `anthropic/claude-sonnet-4.6` | 3 / 15 | 1M | The workhorse default |
| Gemini 3 Flash Preview | `google/gemini-3-flash-preview` | 0.50 / 3 | 1M | Near-Pro reasoning, low latency, multimodal |
| Gemini 2.5 Pro | `google/gemini-2.5-pro` | 1.25 / 10 | 1M | Still solid, cheaper than 3.1 Pro |

### Cheap / fast — classification, extraction, routing, simple checks
| Model | OpenRouter ID | $/M in–out | Context | Notes |
|---|---|---|---|---|
| Claude Haiku 4.5 | `anthropic/claude-haiku-4.5` | 1 / 5 | 200K | Near-frontier at low cost; >73% SWE-bench |
| Gemini 3 Flash Preview | `google/gemini-3-flash-preview` | 0.50 / 3 | 1M | Doubles as a cheap multimodal option |
| Gemini 2.5 Flash Lite | `google/gemini-2.5-flash-lite` | 0.10 / 0.40 | 1M | Cheapest Google tier |
| GPT-4.1 mini / o4-mini | `openai/gpt-4.1-mini` / `openai/o4-mini` | 0.4 / 1.6 · 1.1 / 4.4 | 1M · 200K | Cheap OpenAI options (prices: 4.1-mini · o4-mini) |

### Vision / OCR (if not using a dedicated OCR tool)
| Model | OpenRouter ID | Notes |
|---|---|---|
| Gemini 3 Flash | `google/gemini-3-flash-preview` | Multimodal (image/PDF/audio/video), cheap |
| MiniMax M3 | `minimax/minimax-m3` | Multimodal, 1M ctx, $0.30/M in · $1.20/M out — strong cheap vision |

### Cost levers (cheap, but read the caveats)
| Model | OpenRouter ID | Notes |
|---|---|---|
| DeepSeek V4 Pro | `deepseek/deepseek-v4-pro` | 0.435 / 0.87; best value for coding |
| DeepSeek V4 Flash | `deepseek/deepseek-v4-flash` | 1M ctx, very cheap — ⚠️ **hallucinates ~96% when unsure** (confidently wrong over abstaining). Avoid for high-stakes extraction without strong guardrails. |
| Step 3.7 Flash | `stepfun/step-3.7-flash` | 0.2 / 1.15; speed-critical, very cheap |
| NVIDIA Nemotron 3 Super | `nvidia/nemotron-3-super-120b-a12b:free` | Free; ~300 tok/s; testing/fallback |

---

## Recommended default picks for a BFSI / high-stakes build

Lean on the **major providers** for anything defensible (the credit rationale, the judge) — it reads
as more accountable in a regulated demo, and the deterministic core already caps the blast radius.

- **Extraction / classification (cheap):** `anthropic/claude-haiku-4.5` or `google/gemini-3-flash-preview`
- **Rationale narration (mid):** `anthropic/claude-sonnet-4.6`
- **The judge / hard reasoning (capable):** `anthropic/claude-opus-4.8` or `google/gemini-3.1-pro-preview`
- **Vision/OCR (if needed):** `google/gemini-3-flash-preview` (cheap, multimodal)
- **Free fallbacks for testing only:** Nemotron 3 Super, Llama 3.3 70B, Gemma — rate-limited (~20 req/min, 200/day)

The cheap Chinese/open models are real cost levers, but for the *demo* default to provider-major for
trust; mention the cheaper tier as the productionization cost-optimization (with the DeepSeek caveat).

---

## Per-agent record (store this)

For each agent, store `{ agent, model, tier, rationale, eval_metric }`. Example:
`document_worker · anthropic/claude-haiku-4.5 · cheap · mechanical extraction, cost-sensitive · 94% field accuracy on golden set`.
This is your model-risk-management artifact — it lets you defend each choice and its validated performance.

---

## Verification pass (run before the build — don't debug live)

1. List/confirm each selected model ID resolves on OpenRouter (catch renamed/retired IDs now).
2. Send a 1-token ping to each: confirm auth works, the ID returns, log latency.
3. Confirm pricing against the live model page (this file's numbers are June-2026 snapshots).
4. Resolve any 404 / auth / rate-limit issue **now**, not during the interview.
5. Set a fallback chain (e.g., capable → mid) so a provider outage doesn't stall the demo.
