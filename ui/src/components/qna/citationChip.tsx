// ---------------------------------------------------------------------------
// CitationChip — a clickable handle on the grounding behind an answer.
//
// Role:     Show where a fragment came from (sourceLabel · §section · vVersion),
//           with a terracotta element-type icon. Click expands the verbatim
//           grounding: a quoted PROSE snippet, or a real rendered TABLE when the
//           citation's snippet is markdown-table text.
// Contract: <CitationChip citation={Citation} />.
// Failure:  a non-table snippet always falls back to the quoted-text reveal.
// ---------------------------------------------------------------------------

import { useId, useState } from "react";
import { ChevronDown, FileText, Image, Table as TableIcon } from "lucide-react";
import type { Citation } from "@/lib/types";
import { cn } from "@/lib/utils";
import { parseMarkdownTable } from "@/components/qna/markdownTable";
import { sourceLabel } from "@/components/qna/sourceLabel";

export function CitationChip({ citation }: { citation: Citation }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  const isTable = citation.element_type === "TABLE";
  const isFigure = citation.element_type === "FIGURE";
  const Icon = isTable ? TableIcon : isFigure ? Image : FileText;
  const parsedTable = isTable ? parseMarkdownTable(citation.snippet) : null;

  return (
    <div className="inline-flex max-w-full flex-col">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={panelId}
        className={cn(
          "group inline-flex items-center gap-1.5 rounded-full border bg-surface px-2.5 py-1 text-micro transition-colors duration-150 ease-out-quart",
          open
            ? "border-accent/45 bg-[rgba(212,116,94,0.06)]"
            : "border-border hover:border-accent/40"
        )}
      >
        <Icon className="h-3.5 w-3.5 shrink-0 text-accent" strokeWidth={2} aria-hidden />
        <span className="font-medium text-ink">{sourceLabel(citation.source)}</span>
        <span className="font-mono text-ink-faint">§{citation.section}</span>
        <span className="font-mono text-ink-faint">v{citation.doc_version}</span>
        {isFigure && citation.figure_ref && (
          <span className="font-mono text-ink-faint">{citation.figure_ref}</span>
        )}
        <ChevronDown
          className={cn(
            "h-3 w-3 text-ink-faint transition-transform duration-200 ease-out-quart",
            open && "rotate-180"
          )}
          aria-hidden
        />
      </button>

      {open && (
        <div id={panelId} className="mt-1.5 animate-fade-up">
          {parsedTable ? (
            <div className="overflow-x-auto rounded-lg border border-border bg-surface">
              <table className="w-full border-collapse text-micro">
                <thead>
                  <tr className="bg-surface-alt">
                    {parsedTable.headers.map((h, i) => (
                      <th
                        key={i}
                        className="border-b border-border px-2.5 py-1.5 text-left font-mono font-semibold uppercase tracking-[0.05em] text-ink"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {parsedTable.rows.map((row, r) => (
                    <tr key={r} className="border-b border-subtle last:border-0">
                      {row.map((cell, c) => (
                        <td
                          key={c}
                          className={cn(
                            "px-2.5 py-1.5 align-top",
                            c === 0 ? "font-medium text-ink" : "text-ink-muted"
                          )}
                        >
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <blockquote className="max-w-prose rounded-lg border-l-0 border border-subtle bg-surface-alt px-3 py-2 text-meta italic leading-relaxed text-ink-muted">
              &ldquo;{citation.snippet}&rdquo;
            </blockquote>
          )}
        </div>
      )}
    </div>
  );
}
