// ---------------------------------------------------------------------------
// KnowledgeGaps — section 4: where the documentation is thin.
//   Role:     A table from getKnowledgeGaps(): question · attempted source · reason
//             (danger pill) · top score. Filter chips by reason AND by source. A
//             "view thread" link deep-links the THREADS band to that turn.
//   Contract: { gaps, onView }. onView(turnId) deep-links ?thread=<turn_id>.
//   Failure:  empty / over-filtered renders a calm row.
// ---------------------------------------------------------------------------

import { useMemo, useState } from "react";
import type { DocSource, GapReason, KnowledgeGap } from "@/lib/types";
import { cn } from "@/lib/utils";
import { sourceLabel } from "@/components/qna/sourceLabel";
import { Pill } from "./primitives";

export function KnowledgeGaps({
  gaps,
  onView,
}: {
  gaps: KnowledgeGap[];
  onView: (turnId: string) => void;
}) {
  const [reason, setReason] = useState<GapReason | "ALL">("ALL");
  const [source, setSource] = useState<DocSource | "ALL">("ALL");

  const reasons = useMemo(
    () => Array.from(new Set(gaps.map((g) => g.reason))),
    [gaps],
  );
  const sources = useMemo(
    () => Array.from(new Set(gaps.map((g) => g.attempted_source))),
    [gaps],
  );

  const shown = gaps.filter(
    (g) =>
      (reason === "ALL" || g.reason === reason) &&
      (source === "ALL" || g.attempted_source === source),
  );

  if (gaps.length === 0) {
    return (
      <p className="font-mono text-micro text-ink-faint">
        ◦ NO RECORDED GAPS — every part grounded cleanly.
      </p>
    );
  }

  return (
    <div>
      {/* Two chip rows: reason then source. */}
      <div className="mb-3 space-y-2">
        <ChipRow
          label="reason"
          active={reason}
          options={reasons}
          onPick={(v) => setReason(v as GapReason | "ALL")}
        />
        <ChipRow
          label="source"
          active={source}
          options={sources}
          render={(v) => (v === "ALL" ? "all" : sourceLabel(v as DocSource))}
          onPick={(v) => setSource(v as DocSource | "ALL")}
        />
      </div>

      <div className="overflow-hidden rounded-lg border border-border">
        <table className="w-full border-collapse text-meta">
          <thead>
            <tr className="border-b border-border bg-surface-alt text-left">
              <Th>Question</Th>
              <Th>Attempted source</Th>
              <Th>Reason</Th>
              <Th className="text-right">Top score</Th>
              <Th className="text-right">Thread</Th>
            </tr>
          </thead>
          <tbody>
            {shown.map((g, i) => (
              <tr key={i} className="border-b border-subtle last:border-b-0">
                <td className="px-3 py-2.5 text-ink">{g.question_text}</td>
                <td className="px-3 py-2.5 font-mono text-micro text-ink-muted">
                  {sourceLabel(g.attempted_source)}
                </td>
                <td className="px-3 py-2.5">
                  <Pill tone="danger">{g.reason}</Pill>
                </td>
                <td className="px-3 py-2.5 text-right font-mono text-micro tabular-nums text-ink-muted">
                  {g.top_score == null ? "—" : g.top_score.toFixed(3)}
                </td>
                <td className="px-3 py-2.5 text-right">
                  <button
                    type="button"
                    onClick={() => onView(g.turn_id)}
                    className="font-mono text-micro text-accent underline-offset-2 hover:underline"
                  >
                    view →
                  </button>
                </td>
              </tr>
            ))}
            {shown.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-center font-mono text-micro text-ink-faint">
                  no gaps for this filter
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ChipRow({
  label,
  active,
  options,
  onPick,
  render,
}: {
  label: string;
  active: string;
  options: string[];
  onPick: (v: string) => void;
  render?: (v: string) => string;
}) {
  const all = ["ALL", ...options];
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="mr-1 font-mono text-micro uppercase tracking-[0.08em] text-ink-faint">
        {label}
      </span>
      {all.map((opt) => {
        const on = active === opt;
        return (
          <button
            key={opt}
            type="button"
            onClick={() => onPick(opt)}
            aria-pressed={on}
            className={cn(
              "rounded-md border px-2 py-0.5 font-mono text-micro transition-colors",
              on
                ? "border-accent bg-[rgba(212,116,94,0.10)] text-accent"
                : "border-border text-ink-muted hover:text-ink",
            )}
          >
            {render ? render(opt) : opt === "ALL" ? "all" : opt}
          </button>
        );
      })}
    </div>
  );
}

function Th({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <th
      className={cn(
        "px-3 py-2 font-mono text-micro font-semibold uppercase tracking-[0.06em] text-ink-faint",
        className,
      )}
    >
      {children}
    </th>
  );
}
