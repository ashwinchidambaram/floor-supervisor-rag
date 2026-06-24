// ---------------------------------------------------------------------------
// ThreadRow — one turn in the THREADS band, expand-in-place + deep-link.
//   Role:     Collapsed: status dot · question · confidence pill · cost · latency · a
//             danger gap-indicator. Expanded (accordion, one open): the node-trace strip,
//             a per-sub-question EvidencePanel each, and the answer + citations OR the
//             honest abstain panel.
//   Contract: { group, config, open, onToggle }. The header is a real <button>.
//   Failure:  a FAILED/error turn reads danger dot + surfaces the error.
// ---------------------------------------------------------------------------

import type { Citation, ConfidenceLevel, RunConfig, TurnStatus } from "@/lib/types";
import type { TurnEventGroup } from "@/lib/observability";
import { cn } from "@/lib/utils";
import { confidenceColor } from "@/lib/tokens";
import { sourceLabel } from "@/components/qna/sourceLabel";
import { AlertTriangle, ChevronRight } from "lucide-react";
import { NodeTrace } from "./NodeTrace";
import { EvidencePanel } from "./EvidencePanel";
import { Pill, StatusDot, money, ms, type Tone } from "./primitives";

/** Map a turn outcome to a dot tone, by SHAPE not color alone. */
function dotTone(status: TurnStatus, conf: ConfidenceLevel | null): Tone {
  if (status === "FAILED") return "danger";
  if (status === "ABSTAINED") return "danger";
  if (conf === "HIGH") return "sage";
  if (conf === "MEDIUM") return "gold";
  return "danger";
}

export function ThreadRow({
  group,
  config,
  open,
  onToggle,
}: {
  group: TurnEventGroup;
  config: RunConfig;
  open: boolean;
  onToggle: () => void;
}) {
  const { turn } = group;
  const tone = dotTone(turn.status, turn.turn_confidence);
  const conf = confidenceColor(turn.turn_confidence);
  const errEvent = group.events.find((e) => e.error);

  return (
    <div
      className={cn(
        "rounded-lg border bg-surface transition-colors",
        open ? "border-border shadow-card" : "border-subtle hover:border-border",
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        <ChevronRight
          className={cn(
            "h-4 w-4 shrink-0 text-ink-faint transition-transform duration-150 ease-out-quart",
            open && "rotate-90",
          )}
          strokeWidth={2}
        />
        <StatusDot tone={tone} label={conf.label} />

        <span className="min-w-0 flex-1 truncate text-meta text-ink">{turn.question_text}</span>

        {group.gapCount > 0 && (
          <span className="inline-flex shrink-0 items-center gap-1 font-mono text-micro tabular-nums text-danger">
            <AlertTriangle className="h-3 w-3" strokeWidth={2.25} aria-hidden />
            {group.gapCount} gap{group.gapCount === 1 ? "" : "s"}
          </span>
        )}

        <span
          className={cn(
            "hidden shrink-0 rounded-md border px-1.5 py-0.5 font-mono text-micro font-medium uppercase tracking-[0.06em] sm:inline-flex",
            conf.text,
            conf.bg,
            conf.border,
          )}
        >
          {turn.turn_confidence ?? "—"}
        </span>

        <span className="hidden w-16 shrink-0 text-right font-mono text-micro tabular-nums text-ink-muted md:inline-block">
          {money(group.cost)}
        </span>
        <span className="w-16 shrink-0 text-right font-mono text-micro tabular-nums text-ink-muted">
          {ms(group.latencyMs)}
        </span>
      </button>

      {open && (
        <div className="space-y-6 border-t border-subtle px-4 py-5">
          {errEvent && (
            <div className="rounded-md border border-[rgba(216,86,80,0.40)] bg-danger-soft px-3 py-2 font-mono text-micro text-danger">
              error in {errEvent.node}: {errEvent.error}
            </div>
          )}

          {/* (a) node-trace pipeline strip */}
          <div>
            <h4 className="label-micro mb-2 text-ink-faint">Pipeline trace</h4>
            <NodeTrace events={group.events} />
          </div>

          {/* (b) per-sub-question evidence */}
          <div>
            <h4 className="label-micro mb-2 text-ink-faint">Grounding evidence</h4>
            <div className="space-y-3">
              {turn.sub_questions.map((sq) => (
                <EvidencePanel key={sq.id} sq={sq} config={config} />
              ))}
            </div>
          </div>

          {/* (c) the answer + citations, or the honest abstain panel */}
          <div>
            <h4 className="label-micro mb-2 text-ink-faint">Delivered</h4>
            {turn.status === "ABSTAINED" || turn.answer_text == null ? (
              <AbstainPanel />
            ) : (
              <AnswerPanel answer={turn.answer_text} citations={turn.citations} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function AnswerPanel({ answer, citations }: { answer: string; citations: Citation[] }) {
  return (
    <div className="rounded-lg border border-subtle bg-surface-alt/60 p-4">
      <p className="whitespace-pre-wrap text-meta leading-relaxed text-ink">{answer}</p>
      {citations.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5 border-t border-subtle pt-3">
          {citations.map((c, i) => (
            <Pill key={i} tone="neutral">
              {sourceLabel(c.source)} · {c.section}
            </Pill>
          ))}
        </div>
      )}
    </div>
  );
}

function AbstainPanel() {
  return (
    <div className="rounded-lg border border-[rgba(216,86,80,0.40)] bg-danger-soft p-4">
      <div className="flex items-center gap-2">
        <span className="inline-block h-2.5 w-2.5 rounded-[2px] bg-danger" aria-hidden />
        <span className="font-mono text-micro font-semibold uppercase tracking-[0.08em] text-danger">
          Abstained
        </span>
      </div>
      <p className="mt-1.5 text-meta leading-snug text-ink-muted">
        No grounded answer met the confidence floor. The system declined rather than
        guess: an honest abstain over an unsupported claim.
      </p>
    </div>
  );
}
