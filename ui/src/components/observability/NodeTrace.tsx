// ---------------------------------------------------------------------------
// NodeTrace — drill-down part a: the per-turn pipeline strip.
//   Role:     Render this turn's event run as a row of node pills, each carrying
//             status / latency / tokens / cost. Deterministic ($0) nodes read calm;
//             the single highest-cost node (the judge) gets a terracotta "top cost"
//             mark. A node that errored reads danger.
//   Contract: { events }. Terracotta = chart/accent (top cost), never a status.
//   Failure:  empty events render a calm placeholder.
// ---------------------------------------------------------------------------

import type { Event } from "@/lib/types";
import { cn } from "@/lib/utils";
import { money, ms } from "./primitives";

export function NodeTrace({ events }: { events: Event[] }) {
  if (events.length === 0) {
    return (
      <p className="font-mono text-micro text-ink-faint">no events recorded for this turn</p>
    );
  }
  const topCostIdx = events.reduce(
    (best, e, i) => (e.cost_usd > (events[best]?.cost_usd ?? -1) ? i : best),
    -1,
  );
  const topHasCost = topCostIdx >= 0 && events[topCostIdx].cost_usd > 0;

  return (
    <div className="flex flex-wrap gap-1.5">
      {events.map((e, i) => {
        const det = e.cost_usd === 0;
        const topCost = topHasCost && i === topCostIdx;
        const errored = e.error != null && e.error !== "";
        const cached = e.cache_hit === true;
        return (
          <div
            key={i}
            className={cn(
              "rounded-md border px-2.5 py-1.5",
              errored
                ? "border-[rgba(216,86,80,0.40)] bg-danger-soft"
                : topCost
                  ? "border-accent/45 bg-[rgba(212,116,94,0.07)]"
                  : "border-subtle bg-surface",
            )}
          >
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-micro font-medium text-ink">{e.node}</span>
              {topCost && (
                <span className="font-mono text-micro uppercase tracking-[0.06em] text-accent">
                  top cost
                </span>
              )}
              {/* Neutral cache indicator — not a status/confidence color. */}
              {cached && (
                <span
                  className="font-mono text-micro text-ink-faint"
                  title="Served from cache — cost_usd=$0"
                >
                  ⟳
                </span>
              )}
            </div>
            <div className="mt-1 flex items-center gap-2 font-mono text-micro tabular-nums text-ink-faint">
              <span>{ms(e.latency_ms)}</span>
              <span>·</span>
              <span>{(e.tokens_in + e.tokens_out).toLocaleString()}t</span>
              <span>·</span>
              {/* On a cache hit: always $0 (assemble skipped); show it explicitly. */}
              <span className={cached ? "text-[#5D6A53]" : det ? "text-[#5D6A53]" : topCost ? "text-accent" : "text-ink-muted"}>
                {cached ? "$0" : money(e.cost_usd)}
              </span>
            </div>
            {errored && <div className="mt-1 font-mono text-micro text-danger">{e.error}</div>}
          </div>
        );
      })}
    </div>
  );
}
