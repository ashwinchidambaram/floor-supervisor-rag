// ---------------------------------------------------------------------------
// CostLatency — section 2: where the run spent money and time.
//   Role:     cost-by-node bars (sorted desc; the LLM judge ≈ full terracotta; $0
//             deterministic nodes get a calm sage stub + a literal "$0") and a
//             stage-dwell timeline (ink-muted bars). Both from getMetrics().
//   Contract: { metrics }. Terracotta is CHART-only here, never a status.
//   Failure:  max guarded against 0; empty maps render nothing.
// ---------------------------------------------------------------------------

import type { Metrics } from "@/lib/types";
import { cn } from "@/lib/utils";
import { money, ms } from "./primitives";

export function CostLatency({ metrics }: { metrics: Metrics }) {
  return (
    <div className="grid gap-10 lg:grid-cols-2">
      <CostByNode costByAgent={metrics.cost_by_agent} total={metrics.cost_total} />
      <StageDwell dwell={metrics.stage_dwell} />
    </div>
  );
}

function CostByNode({
  costByAgent,
  total,
}: {
  costByAgent: Record<string, number>;
  total: number;
}) {
  const entries = Object.entries(costByAgent).sort((a, b) => b[1] - a[1]);
  const max = Math.max(...entries.map(([, v]) => v), 1e-9);
  return (
    <div>
      <div className="mb-3 flex items-baseline justify-between">
        <h3 className="label-micro text-ink">Cost by node</h3>
        <span className="font-mono text-micro tabular-nums text-ink-faint">
          total {money(total)}
        </span>
      </div>
      <div className="space-y-2.5">
        {entries.map(([node, cost]) => {
          const det = cost === 0;
          const width = det ? 4 : Math.max((cost / max) * 100, 8);
          return (
            <div key={node} className="flex items-center gap-3">
              <span className="w-40 shrink-0 truncate font-mono text-micro text-ink-muted">
                {node}
              </span>
              <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-alt">
                <div
                  className={cn("h-full rounded-full", det ? "bg-sage/45" : "bg-accent")}
                  style={{ width: `${width}%` }}
                />
              </div>
              <span
                className={cn(
                  "w-16 shrink-0 text-right font-mono text-micro font-medium tabular-nums",
                  det ? "text-[#5D6A53]" : "text-ink",
                )}
              >
                {money(cost)}
              </span>
            </div>
          );
        })}
      </div>
      <p className="mt-3 font-mono text-micro text-ink-faint">
        Deterministic nodes cost <span className="text-[#5D6A53]">$0</span> — the agency
        line, made visible.
      </p>
    </div>
  );
}

function StageDwell({ dwell }: { dwell: Record<string, number> }) {
  // Preserve pipeline order (insertion order of the map), not sorted — this reads as a timeline.
  const entries = Object.entries(dwell);
  const max = Math.max(...entries.map(([, v]) => v), 1e-9);
  return (
    <div>
      <div className="mb-3 flex items-baseline justify-between">
        <h3 className="label-micro text-ink">Stage dwell</h3>
        <span className="font-mono text-micro tabular-nums text-ink-faint">
          wall time per stage
        </span>
      </div>
      <div className="space-y-2.5">
        {entries.map(([node, dwellMs]) => (
          <div key={node} className="flex items-center gap-3">
            <span className="w-40 shrink-0 truncate font-mono text-micro text-ink-muted">
              {node}
            </span>
            <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-alt">
              <div
                className="h-full rounded-full bg-ink-muted/55"
                style={{ width: `${Math.max((dwellMs / max) * 100, 1)}%` }}
              />
            </div>
            <span className="w-16 shrink-0 text-right font-mono text-micro tabular-nums text-ink-muted">
              {ms(dwellMs)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
