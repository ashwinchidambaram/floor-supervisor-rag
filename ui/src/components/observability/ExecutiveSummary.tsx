// ---------------------------------------------------------------------------
// ExecutiveSummary — the operator's headline, scanned first.
//   Role:     One divided KPI ribbon that answers "healthy? cost? where thin?" at a
//             glance: outcome mix (stacked sage/gold/danger), total cost + the most
//             expensive node with the deterministic-$0 callout, cycle time, gap count,
//             judge-reject rate, and the derived false-PASS watch.
//   Contract: { metrics, falsePassCount, topCostNode }. Pure render.
//   Failure:  pct() guards divide-by-zero; a 0 false-PASS reads as a calm sage "clean".
// ---------------------------------------------------------------------------

import type { ReactNode } from "react";
import type { Metrics } from "@/lib/types";
import { cn } from "@/lib/utils";
import { money } from "./primitives";

export function ExecutiveSummary({
  metrics,
  falsePassCount,
  topCostNode,
  topCostValue,
}: {
  metrics: Metrics;
  falsePassCount: number;
  topCostNode: string;
  topCostValue: number;
}) {
  const clean = falsePassCount === 0;

  return (
    <section aria-label="Executive summary">
      <span className="eyebrow">◦ EXECUTIVE SUMMARY</span>
      <h1 className="mt-1.5 font-display text-display font-semibold tracking-tight text-ink">
        Run health
      </h1>

      <div className="mt-6 overflow-hidden rounded-xl border border-border bg-surface shadow-card">
        {/* Outcome mix — the full-width band on top, the loudest read. */}
        <div className="border-b border-subtle px-6 py-5">
          <div className="flex items-baseline justify-between">
            <span className="label-micro text-ink-faint">Outcome mix</span>
            <span className="font-mono text-micro tabular-nums text-ink-faint">
              straight-through / partial / abstain
            </span>
          </div>
          <OutcomeBar
            straight={metrics.straight_through_pct}
            partial={metrics.partial_rate}
            abstain={metrics.abstain_rate}
          />
        </div>

        {/* Divided KPI row. */}
        <dl className="grid grid-cols-2 divide-subtle md:grid-cols-3 md:divide-x lg:grid-cols-5">
          <Kpi label="Total cost" value={money(metrics.cost_total)}>
            <span className="font-mono text-micro text-ink-faint">
              top node{" "}
              <span className="text-accent">{topCostNode}</span>{" "}
              {money(topCostValue)}
            </span>
            <span className="mt-0.5 block font-mono text-micro text-[#5D6A53]">
              deterministic nodes $0
            </span>
          </Kpi>

          <Kpi label="Cycle time" value={`${metrics.cycle_time.toFixed(2)}s`}>
            <span className="font-mono text-micro text-ink-faint">
              {metrics.tokens_total.toLocaleString()} tokens · {metrics.retries} retries
            </span>
          </Kpi>

          <Kpi label="Knowledge gaps" value={String(metrics.knowledge_gap_count)}>
            <span className="font-mono text-micro text-ink-faint">
              parts the judge could not ground
            </span>
          </Kpi>

          <Kpi label="Judge reject rate" value={`${(metrics.judge_reject_rate * 100).toFixed(0)}%`}>
            <span className="font-mono text-micro text-ink-faint">
              sub-questions failed on first pass
            </span>
          </Kpi>

          {/* False-PASS watch — derived, the most diagnostic cell. */}
          <div
            className={cn(
              "px-6 py-5",
              clean ? "" : "bg-danger-soft",
            )}
          >
            <dt className="label-micro text-ink-faint">False-PASS watch</dt>
            <dd className="mt-1.5 flex items-baseline gap-2">
              <span
                className={cn(
                  "font-display text-title font-semibold tabular-nums tracking-tight",
                  clean ? "text-[#5D6A53]" : "text-danger",
                )}
              >
                {falsePassCount}
              </span>
              <span
                className={cn(
                  "font-mono text-micro uppercase tracking-[0.08em]",
                  clean ? "text-[#5D6A53]" : "text-danger",
                )}
              >
                {clean ? "clean" : "review"}
              </span>
            </dd>
            <span className="mt-0.5 block font-mono text-micro text-ink-faint">
              judge said PASS, turn resolved LOW
            </span>
          </div>
        </dl>
      </div>
    </section>
  );
}

function Kpi({ label, value, children }: { label: string; value: string; children?: ReactNode }) {
  return (
    <div className="border-b border-subtle px-6 py-5 last:border-b-0 md:border-b-0">
      <dt className="label-micro text-ink-faint">{label}</dt>
      <dd className="mt-1.5 font-display text-title font-semibold tabular-nums tracking-tight text-ink">
        {value}
      </dd>
      <div className="mt-1">{children}</div>
    </div>
  );
}

/** Stacked-segment bar: sage / gold / danger, with a labelled legend below. */
function OutcomeBar({
  straight,
  partial,
  abstain,
}: {
  straight: number;
  partial: number;
  abstain: number;
}) {
  const total = straight + partial + abstain || 1;
  const seg = (v: number) => `${(v / total) * 100}%`;
  return (
    <div className="mt-3">
      <div
        className="flex h-3 w-full overflow-hidden rounded-full bg-surface-alt"
        role="img"
        aria-label={`Outcomes: ${straight}% straight-through, ${partial}% partial, ${abstain}% abstain`}
      >
        {straight > 0 && <span className="h-full bg-sage" style={{ width: seg(straight) }} />}
        {partial > 0 && <span className="h-full bg-gold" style={{ width: seg(partial) }} />}
        {abstain > 0 && <span className="h-full bg-danger" style={{ width: seg(abstain) }} />}
      </div>
      <div className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1">
        <Legend tone="bg-sage" label="straight-through" value={straight} />
        <Legend tone="bg-gold" label="partial" value={partial} />
        <Legend tone="bg-danger" label="abstain" value={abstain} square />
      </div>
    </div>
  );
}

function Legend({
  tone,
  label,
  value,
  square,
}: {
  tone: string;
  label: string;
  value: number;
  square?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-micro tabular-nums text-ink-muted">
      <span className={cn("inline-block h-2 w-2", square ? "rounded-[2px]" : "rounded-full", tone)} />
      {value.toFixed(0)}% {label}
    </span>
  );
}
