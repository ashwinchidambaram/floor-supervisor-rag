// ---------------------------------------------------------------------------
// ChunkInspector — the shared chunk-detail renderer (Browse + Retrieval reuse it).
//
// Role:     Render one knowledge-base chunk faithfully. A TABLE chunk's
//           `table_markdown` is rendered VERBATIM as a real <table> via the shared
//           parseMarkdownTable; a PROSE chunk renders its `text`. The element type
//           is tagged (TABLE = sage outline) so the operator can see corpus shape.
// Contract: <ChunkInspector chunkId elementType text tableMarkdown /> — pure render.
// Failure:  Malformed/absent table markdown falls back to a raw <pre> of the source
//           string; it NEVER throws and never silently drops the content.
// ---------------------------------------------------------------------------

import { parseMarkdownTable } from "@/components/qna/markdownTable";
import type { ElementType } from "@/lib/types";
import { cn } from "@/lib/utils";

export interface ChunkInspectorProps {
  chunkId: string;
  elementType: ElementType;
  text: string | null;
  tableMarkdown: string | null;
}

/** Sage outline for TABLE (structured), quiet border for PROSE. */
function ElementTag({ type }: { type: ElementType }) {
  const isTable = type === "TABLE";
  return (
    <span
      className={cn(
        "label-micro rounded border px-1.5 py-0.5",
        isTable
          ? "border-[rgba(139,157,131,0.5)] bg-[rgba(139,157,131,0.12)] text-[#5D6A53]"
          : "border-border-subtle bg-surface-alt text-ink-faint"
      )}
    >
      {type}
    </span>
  );
}

/** Render a verbatim GFM table. Returns null when the markdown isn't a pipe table. */
function VerbatimTable({ markdown }: { markdown: string }) {
  const parsed = parseMarkdownTable(markdown);
  if (!parsed) return null;
  const { headers, rows } = parsed;
  const headerless = headers.every((h) => h.trim() === "");
  return (
    <div className="scroll-quiet overflow-x-auto rounded-lg border border-border-subtle">
      <table className="w-full border-collapse text-left text-meta tabular-nums">
        {!headerless && (
          <thead>
            <tr className="bg-surface-alt">
              {headers.map((h, i) => (
                <th
                  key={i}
                  className="border-b border-border px-3 py-2 font-mono text-micro font-semibold uppercase tracking-wide text-ink-muted"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {rows.map((row, r) => (
            <tr key={r} className="border-t border-border-subtle even:bg-surface-alt/40">
              {row.map((cell, c) => (
                <td
                  key={c}
                  className={cn(
                    "px-3 py-1.5 align-top text-ink",
                    c === 0 && "font-medium text-ink-muted"
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
  );
}

export function ChunkInspector({ chunkId, elementType, text, tableMarkdown }: ChunkInspectorProps) {
  const isTable = elementType === "TABLE";
  // Verbatim table when it parses; otherwise honest raw <pre> fallback (never throws).
  const parsed = isTable && tableMarkdown ? parseMarkdownTable(tableMarkdown) : null;

  return (
    <div className="rounded-lg border border-border bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-border-subtle px-4 py-2.5">
        <span className="truncate font-mono text-micro text-ink-muted" title={chunkId}>
          {chunkId}
        </span>
        <ElementTag type={elementType} />
      </div>
      <div className="px-4 py-3.5">
        {isTable && tableMarkdown ? (
          parsed ? (
            <VerbatimTable markdown={tableMarkdown} />
          ) : (
            // Malformed table markdown: show the source verbatim rather than crash.
            <pre className="scroll-quiet overflow-x-auto rounded-lg border border-border-subtle bg-surface-alt px-3 py-2 font-mono text-micro text-ink-muted">
              {tableMarkdown}
            </pre>
          )
        ) : (
          <p className="max-w-reading whitespace-pre-wrap text-meta leading-relaxed text-ink">
            {text?.trim() || <span className="text-ink-faint">No text captured for this chunk.</span>}
          </p>
        )}
      </div>
    </div>
  );
}
