// ---------------------------------------------------------------------------
// ScoreBar — a retrieval similarity score as an accessible meter.
//
// Role:     Render a cosine score in [0,1] as a sage fill (healthy retrieval) with a
//           tabular-nums numeric label. The top hit of a query gets a terracotta ring
//           (interactive/selection emphasis, never status). Tailwind divs only — no
//           chart library.
// Contract: <ScoreBar score isTop /> — role="meter" with aria value bounds.
// Failure:  Out-of-range scores are clamped to [0,1] for the fill width.
// ---------------------------------------------------------------------------

import { cn } from "@/lib/utils";

export function ScoreBar({ score, isTop = false }: { score: number; isTop?: boolean }) {
  const pct = Math.max(0, Math.min(1, score)) * 100;
  return (
    <div className="flex items-center gap-2.5">
      <div
        role="meter"
        aria-valuenow={Number(score.toFixed(3))}
        aria-valuemin={0}
        aria-valuemax={1}
        aria-label="Retrieval similarity score"
        className={cn(
          "h-2 w-24 shrink-0 overflow-hidden rounded-full bg-surface-alt ring-1 ring-inset ring-border-subtle",
          isTop && "ring-2 ring-accent/70"
        )}
      >
        <div className="h-full rounded-full bg-sage" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 shrink-0 text-right font-mono text-micro tabular-nums text-ink-muted">
        {score.toFixed(3)}
      </span>
    </div>
  );
}
