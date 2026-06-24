// ---------------------------------------------------------------------------
// DocumentCard — one corpus document at a glance (Band A).
//
// Role:     Summarize a KbDocument: title, mono doc_number with a terracotta version
//           chip, effective date, a gold "supersedes" caution chip when present, a
//           stacked prose/table composition mini-bar (sage), and the chunk count.
//           Lifts with shadow-glow-accent on hover (interactive affordance).
// Contract: <DocumentCard doc onOpen /> — onOpen jumps the Browse pane to this doc.
// Failure:  Null doc_number / effective_date render as a quiet em dash; never throws.
// ---------------------------------------------------------------------------

import { ArrowUpRight } from "lucide-react";
import type { KbDocument } from "@/lib/types";
import { sourceLabel } from "@/components/qna/sourceLabel";
import { cn } from "@/lib/utils";

export function DocumentCard({ doc, onOpen }: { doc: KbDocument; onOpen: () => void }) {
  const { counts } = doc;
  const total = Math.max(counts.prose + counts.tables, 1);
  const prosePct = (counts.prose / total) * 100;

  return (
    <button
      type="button"
      onClick={onOpen}
      className={cn(
        "group flex flex-col rounded-xl border border-border bg-surface p-5 text-left",
        "transition-[transform,box-shadow] duration-200 ease-out-quart",
        "hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-glow-accent",
        "focus-visible:-translate-y-0.5"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="eyebrow">◦ {sourceLabel(doc.source)}</span>
        <ArrowUpRight
          className="h-4 w-4 shrink-0 text-ink-faint transition-colors group-hover:text-accent"
          strokeWidth={2}
        />
      </div>

      <h3 className="mt-2 font-display text-lead font-semibold leading-snug tracking-tight text-ink">
        {titleCase(doc.doc_title)}
      </h3>

      <div className="mt-2.5 flex flex-wrap items-center gap-2">
        <span className="font-mono text-meta text-ink-muted">{doc.doc_number ?? "—"}</span>
        <span className="rounded-md border border-accent/40 bg-accent/10 px-1.5 py-0.5 font-mono text-micro font-semibold tabular-nums text-accent">
          v{doc.doc_version}
        </span>
      </div>

      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-micro text-ink-faint">
        <span>Effective {doc.effective_date ?? "—"}</span>
        {doc.supersedes && (
          <span className="rounded border border-[rgba(212,165,116,0.5)] bg-[rgba(212,165,116,0.14)] px-1.5 py-0.5 font-medium text-[#835C39]">
            supersedes {doc.supersedes}
          </span>
        )}
      </div>

      {/* Composition mini-bar: prose vs table, stacked. Sage = indexed/healthy. */}
      <div className="mt-4">
        <div className="flex h-2 overflow-hidden rounded-full bg-surface-alt ring-1 ring-inset ring-border-subtle">
          <div className="h-full bg-sage" style={{ width: `${prosePct}%` }} aria-hidden />
          <div className="h-full bg-[rgba(139,157,131,0.45)]" style={{ width: `${100 - prosePct}%` }} aria-hidden />
        </div>
        <div className="mt-1.5 flex items-center justify-between text-micro text-ink-faint">
          <span className="tabular-nums">
            {counts.prose} prose · {counts.tables} tables
          </span>
          <span className="font-mono tabular-nums text-ink-muted">
            {counts.chunks} chunks
          </span>
        </div>
      </div>
    </button>
  );
}

/** Floor docs ship as SHOUTING titles; soften to title case for the card heading. */
function titleCase(s: string): string {
  return s
    .toLowerCase()
    .replace(/\b([a-z])/g, (m) => m.toUpperCase());
}
