"""measure_cache.py — MEASURE the cache miss-vs-hit cost on the real graph (spec §4b).

Runs the same question twice with the per-node cache ON and Redis up:
  · run 1 (cold thread, caches flushed)  = MISS  → full per-answer cost
  · run 2 (fresh thread, same question)  = HIT   → retrieve + assemble reused; the JUDGE re-runs
The judge is deliberately NOT cached, so a "hit" still pays the judge (the most expensive node) —
that is the whole point of the cost story in the README. Writes var/cache_measure.log.

Run: RAG env from .env; `python -m scripts.measure_cache "<question>"`
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from src.graph import build_graph  # noqa: E402
from src.ingest import ingest  # noqa: E402
from src.observability import export_data_out  # noqa: E402
from src.state import ConversationState, Turn  # noqa: E402
from src.tools import cache as cache_mod  # noqa: E402
from src.tools.hybrid_search import _store  # noqa: E402

Q = sys.argv[1] if len(sys.argv) > 1 else "What torque do the CNC VF-4 vise jaw bolts need?"
LOG = ROOT / "var" / "cache_measure.log"


def ask(graph, thread_id: str, question: str) -> dict:
    state = ConversationState(conversation_id=thread_id, supervisor_id="measure")
    state.current_turn = Turn(turn_id="t1", question_text=question, sub_questions=[])
    out = ConversationState.model_validate(
        graph.invoke(state, config={"configurable": {"thread_id": thread_id}})
    )
    data = export_data_out(out)
    turn = data["current_turn"] or data["turns"][-1]
    # per-node view from this turn's events
    nodes = [
        {
            "node": e["node"],
            "cost_usd": e["cost_usd"],
            "cache_hit": e.get("cache_hit", False),
            "latency_ms": round(e["latency_ms"], 1),
        }
        for e in data["events"]
    ]
    return {
        "status": turn["status"],
        "confidence": turn["turn_confidence"],
        "cost_total": data["metrics"]["cost_total"],
        "cost_by_agent": data["metrics"]["cost_by_agent"],
        "cycle_time": data["metrics"]["cycle_time"],
        "nodes": nodes,
    }


def fmt(r: dict, label: str) -> str:
    lines = [f"=== {label} ===",
             f"status={r['status']} confidence={r['confidence']} "
             f"cost_total=${r['cost_total']:.4f} cycle_time={r['cycle_time']:.2f}s"]
    lines.append("  per-node: cost_usd | cache_hit | latency_ms")
    for n in r["nodes"]:
        lines.append(f"    {n['node']:<20} ${n['cost_usd']:.4f}  "
                     f"{'CACHED' if n['cache_hit'] else '   -  '}  {n['latency_ms']:>8.1f}")
    return "\n".join(lines)


def main() -> None:
    if _store().count() == 0:
        print("building index…")
        ingest()
    graph = build_graph(checkpointer=MemorySaver())

    # Clean slate: flush the two node namespaces so run 1 is a true MISS.
    cache_mod.flush_namespace("retrieval")
    cache_mod.flush_namespace("llm:assemble")
    cache_mod.reset_stats()

    miss = ask(graph, "measure-miss", Q)
    hit = ask(graph, "measure-hit", Q)  # fresh thread (no history) → same sub-qs → same cache keys
    stats = cache_mod.cache_stats()

    saved = miss["cost_total"] - hit["cost_total"]
    pct = (saved / miss["cost_total"] * 100) if miss["cost_total"] else 0.0

    report = [
        f"CACHE MEASUREMENT — question: {Q!r}",
        f"(index chunks: {_store().count()})",
        "",
        fmt(miss, "RUN 1 · MISS (cold, caches flushed)"),
        "",
        fmt(hit, "RUN 2 · HIT (fresh thread, same question — retrieve+assemble reused; judge re-runs)"),
        "",
        "=== VERDICT ===",
        f"miss cost = ${miss['cost_total']:.4f} | hit cost = ${hit['cost_total']:.4f} | "
        f"saved = ${saved:.4f} ({pct:.0f}%)",
        f"latency: miss {miss['cycle_time']:.2f}s → hit {hit['cycle_time']:.2f}s",
        f"cache stats: {stats}",
        "NOTE: the judge is NOT cached — it re-runs on the hit, so the hit still pays the judge "
        "(the most expensive node). The cache saves the assemble step + retrieval latency.",
    ]
    text = "\n".join(report)
    print(text)
    LOG.write_text(text + "\n")
    print(f"\n→ written to {LOG}")


if __name__ == "__main__":
    main()
