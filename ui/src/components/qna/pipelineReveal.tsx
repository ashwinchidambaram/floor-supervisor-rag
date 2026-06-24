// ---------------------------------------------------------------------------
// PipelineReveal — the quiet operator affordance under an answer.
//
// Role:     Replay the agentic spine (decompose → route → retrieve → judge →
//           assemble) for ONE turn, derived deterministically from the turn's own
//           sub_questions (routed_source, retrieved chunks + scores, judge verdict
//           + reasons, confidence). Plus an inline evidence reveal: the top
//           retrieved chunks with scores and the judge verdict per part. This is a
//           muted, monospace operator view — it never colors the supervisor-clean
//           default and only mounts when the global "Show pipeline" toggle is ON.
// Contract: <PipelineReveal turn={Turn} />.
// Failure:  reads only fields present on every Turn; nothing throws.
// ---------------------------------------------------------------------------

import { useState } from "react";
import { Check, ChevronRight, X } from "lucide-react";
import type { Event, SubQuestion, Turn } from "@/lib/types";
import { confidenceColor } from "@/lib/tokens";
import { cn } from "@/lib/utils";
import { sourceLabel } from "@/components/qna/sourceLabel";
import { ConfidenceDot } from "@/components/qna/confidenceBadge";

/** The five spine stages, in deterministic graph order. */
function spineStages(turn: Turn): { node: string; detail: string }[] {
  const parts = turn.sub_questions;
  const routed = [...new Set(parts.map((p) => p.routed_source))];
  const totalHits = parts.reduce((n, p) => n + p.retrieved.length, 0);
  const attempts = Math.max(1, ...parts.map((p) => p.retrieval_attempts || 1));
  const passes = parts.filter((p) => p.judge_verdict === "PASS").length;

  return [
    { node: "decompose", detail: `${parts.length} sub-question${parts.length === 1 ? "" : "s"}` },
    { node: "route", detail: routed.map(sourceLabel).join(", ") || "unrouted" },
    { node: "retrieve", detail: `${totalHits} chunks · ${attempts} attempt${attempts === 1 ? "" : "s"}` },
    { node: "judge", detail: `${passes}/${parts.length} grounded` },
    { node: "assemble", detail: turn.status.toLowerCase().replace("_", " ") },
  ];
}

/** Build a set of node names that had cache_hit=true in this turn's events. */
function buildCacheHitSet(events: Event[]): Set<string> {
  const hits = new Set<string>();
  for (const e of events) {
    if (e.cache_hit === true) hits.add(e.node);
  }
  return hits;
}

export function PipelineReveal({ turn, events = [] }: { turn: Turn; events?: Event[] }) {
  const cacheHits = buildCacheHitSet(events);

  return (
    <section className="mt-4 rounded-lg border border-subtle bg-surface-alt/60 px-4 py-3.5">
      <div className="mb-3 flex items-center gap-2">
        <span className="eyebrow">◦ PIPELINE</span>
        <span className="font-mono text-micro text-ink-faint">
          decompose → route → retrieve → judge → assemble
        </span>
      </div>

      {/* The spine — stages with status + summary, deterministic from the turn. */}
      <ol className="space-y-0">
        {spineStages(turn).map((stage, i, all) => {
          // Map spine stage names to event node names.
          const nodeKey = stage.node === "retrieve" ? "retrieve_chunks"
            : stage.node === "assemble" ? "assemble_answer"
            : stage.node === "judge" ? "judge_grounding"
            : stage.node;
          const isCached = cacheHits.has(nodeKey);
          // The judge always re-runs (grounding is never served stale), even on cache hits.
          const isJudge = stage.node === "judge";

          return (
            <li key={stage.node} className="flex items-center gap-2.5 py-1">
              <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full border border-border bg-surface">
                <Check className="h-3 w-3 text-sage" strokeWidth={2.5} aria-hidden />
              </span>
              <span className="w-24 shrink-0 font-mono text-micro font-semibold uppercase tracking-[0.06em] text-ink">
                {stage.node}
              </span>
              <span className="min-w-0 flex-1 truncate font-mono text-micro text-ink-muted">
                {stage.detail}
              </span>
              {/* Subtle cache marker — neutral ink, never a status color. */}
              {isCached && !isJudge && (
                <span className="shrink-0 font-mono text-micro text-ink-faint" title="Served from cache">
                  ⟳ reused
                </span>
              )}
              {isJudge && cacheHits.size > 0 && (
                <span className="shrink-0 font-mono text-micro text-ink-faint" title="Judge always re-runs — grounding is never served stale">
                  re-ran
                </span>
              )}
              {i < all.length - 1 && (
                <ChevronRight className="h-3 w-3 shrink-0 text-ink-faint/50" aria-hidden />
              )}
            </li>
          );
        })}
      </ol>

      {/* Inline evidence: the retrieved chunks + scores and the judge verdict, per part. */}
      <div className="mt-3 space-y-2 border-t border-subtle pt-3">
        {turn.sub_questions.map((sq) => (
          <EvidenceRow key={sq.id} sq={sq} />
        ))}
      </div>
    </section>
  );
}

function EvidenceRow({ sq }: { sq: SubQuestion }) {
  const [open, setOpen] = useState(false);
  const tone = confidenceColor(sq.confidence);
  const top = [...sq.retrieved].sort((a, b) => b.score - a.score).slice(0, 3);
  const pass = sq.judge_verdict === "PASS";

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-2 text-left"
      >
        <ChevronRight
          className={cn("h-3 w-3 shrink-0 text-ink-faint transition-transform duration-150", open && "rotate-90")}
          aria-hidden
        />
        <ConfidenceDot tone={tone} className="h-1.5 w-1.5" />
        <span className="min-w-0 flex-1 truncate font-mono text-micro text-ink-muted">{sq.text}</span>
        <span
          className={cn(
            "inline-flex items-center gap-1 font-mono text-micro font-semibold uppercase",
            pass ? "text-sage" : "text-danger"
          )}
        >
          {pass ? <Check className="h-3 w-3" strokeWidth={2.5} /> : <X className="h-3 w-3" strokeWidth={2.5} />}
          {sq.judge_verdict ?? "—"}
        </span>
      </button>

      {open && (
        <div className="ml-5 mt-1.5 space-y-2 animate-fade-up">
          {/* Top retrieved chunks with scores. */}
          <ul className="space-y-1">
            {top.map((chunk) => (
              <li key={chunk.chunk_id} className="flex items-center gap-2 font-mono text-micro">
                <span className="w-12 shrink-0 tabular-nums text-accent">{chunk.score.toFixed(3)}</span>
                <span className="min-w-0 flex-1 truncate text-ink-muted">
                  {chunk.section} · {chunk.element_type.toLowerCase()}
                </span>
              </li>
            ))}
          </ul>
          {/* Judge verdict rationale. */}
          {sq.judge_reasons.length > 0 && (
            <p className="border-l-0 text-micro italic leading-relaxed text-ink-faint">
              {sq.judge_reasons[0]}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
