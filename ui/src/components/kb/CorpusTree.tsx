// ---------------------------------------------------------------------------
// CorpusTree — the Document → Section → Chunk disclosure tree (Band B, left).
//
// Role:     Let the operator browse the corpus structure and pick a chunk. Documents
//           and sections are disclosure rows with mono counts; the active node carries
//           a terracotta selection (interactive, never status). Arrow keys move a
//           roving-tabindex cursor; Enter/Space activates; Left/Right collapse/expand.
// Contract: <CorpusTree documents selectedChunkId onSelectChunk /> — selection is owned
//           by the parent so the detail pane and Retrieval demo can drive it too.
// Failure:  Empty documents/sections simply render no children; pure render, no throw.
// ---------------------------------------------------------------------------

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronRight, FileText, Table2 } from "lucide-react";
import type { KbDocument } from "@/lib/types";
import { sourceLabel } from "@/components/qna/sourceLabel";
import { cn } from "@/lib/utils";

type Row =
  | { kind: "doc"; id: string; depth: 0; label: string; count: number; docKey: string }
  | { kind: "section"; id: string; depth: 1; label: string; count: number; docKey: string; sectionKey: string }
  | { kind: "chunk"; id: string; depth: 2; label: string; chunkId: string; isTable: boolean };

interface CorpusTreeProps {
  documents: KbDocument[];
  selectedChunkId: string | null;
  onSelectChunk: (chunkId: string) => void;
  /** When the parent jumps to a doc (Band A card), expand it and reveal it. */
  focusDocSource?: string | null;
}

export function CorpusTree({ documents, selectedChunkId, onSelectChunk, focusDocSource }: CorpusTreeProps) {
  const [openDocs, setOpenDocs] = useState<Set<string>>(() => new Set(documents.slice(0, 1).map((d) => d.source)));
  const [openSections, setOpenSections] = useState<Set<string>>(() => {
    // Open the first section of the first doc so a chunk is visible on load.
    const first = documents[0];
    const firstSec = first?.sections[0];
    return new Set(firstSec ? [`${first.source}::${firstSec.section}`] : []);
  });
  const [cursor, setCursor] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  // A parent "open this doc" request (clicking a Band A card) expands + scrolls to it.
  useEffect(() => {
    if (!focusDocSource) return;
    setOpenDocs((prev) => new Set(prev).add(focusDocSource));
  }, [focusDocSource]);

  const rows = useMemo<Row[]>(() => {
    const out: Row[] = [];
    for (const doc of documents) {
      const docOpen = openDocs.has(doc.source);
      out.push({
        kind: "doc",
        id: `doc:${doc.source}`,
        depth: 0,
        label: sourceLabel(doc.source),
        count: doc.counts.chunks,
        docKey: doc.source,
      });
      if (!docOpen) continue;
      for (const sec of doc.sections) {
        const sectionKey = `${doc.source}::${sec.section}`;
        out.push({
          kind: "section",
          id: `sec:${sectionKey}`,
          depth: 1,
          label: sec.section,
          count: sec.chunks.length,
          docKey: doc.source,
          sectionKey,
        });
        if (!openSections.has(sectionKey)) continue;
        for (const chunk of sec.chunks) {
          out.push({
            kind: "chunk",
            id: `chunk:${chunk.chunk_id}`,
            depth: 2,
            label: chunk.chunk_id.split("#").slice(1).join(" · "),
            chunkId: chunk.chunk_id,
            isTable: chunk.element_type === "TABLE",
          });
        }
      }
    }
    return out;
  }, [documents, openDocs, openSections]);

  const toggleDoc = (key: string) =>
    setOpenDocs((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  const toggleSection = (key: string) =>
    setOpenSections((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });

  const activateRow = (row: Row) => {
    if (row.kind === "doc") toggleDoc(row.docKey);
    else if (row.kind === "section") toggleSection(row.sectionKey);
    else onSelectChunk(row.chunkId);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    const row = rows[cursor];
    if (!row) return;
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setCursor((c) => Math.min(c + 1, rows.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setCursor((c) => Math.max(c - 1, 0));
        break;
      case "ArrowRight":
        e.preventDefault();
        if (row.kind === "doc" && !openDocs.has(row.docKey)) toggleDoc(row.docKey);
        else if (row.kind === "section" && !openSections.has(row.sectionKey)) toggleSection(row.sectionKey);
        else setCursor((c) => Math.min(c + 1, rows.length - 1));
        break;
      case "ArrowLeft":
        e.preventDefault();
        if (row.kind === "doc" && openDocs.has(row.docKey)) toggleDoc(row.docKey);
        else if (row.kind === "section" && openSections.has(row.sectionKey)) toggleSection(row.sectionKey);
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        activateRow(row);
        break;
      case "Home":
        e.preventDefault();
        setCursor(0);
        break;
      case "End":
        e.preventDefault();
        setCursor(rows.length - 1);
        break;
    }
  };

  // Keep the cursor in range as rows expand/collapse, and roving focus on the active row.
  useEffect(() => {
    if (cursor > rows.length - 1) setCursor(Math.max(rows.length - 1, 0));
  }, [rows.length, cursor]);

  useEffect(() => {
    const el = listRef.current?.querySelector<HTMLElement>(`[data-row-index="${cursor}"]`);
    if (el && document.activeElement && listRef.current?.contains(document.activeElement)) {
      el.focus();
    }
  }, [cursor]);

  return (
    <div
      ref={listRef}
      role="tree"
      aria-label="Corpus structure"
      onKeyDown={onKeyDown}
      className="scroll-quiet h-full overflow-y-auto py-1.5"
    >
      {rows.map((row, i) => {
        const isCursor = i === cursor;
        const expanded =
          row.kind === "doc"
            ? openDocs.has(row.docKey)
            : row.kind === "section"
              ? openSections.has(row.sectionKey)
              : undefined;
        const selected = row.kind === "chunk" && row.chunkId === selectedChunkId;
        return (
          <button
            key={row.id}
            type="button"
            data-row-index={i}
            role="treeitem"
            aria-level={row.depth + 1}
            aria-expanded={expanded}
            aria-selected={selected || undefined}
            tabIndex={isCursor ? 0 : -1}
            onClick={() => {
              setCursor(i);
              activateRow(row);
            }}
            className={cn(
              "flex w-full items-center gap-1.5 rounded-md py-1.5 pr-2 text-left transition-colors",
              row.depth === 0 ? "pl-2" : row.depth === 1 ? "pl-6" : "pl-11",
              selected
                ? "bg-accent/12 text-ink"
                : "text-ink-muted hover:bg-surface-alt hover:text-ink"
            )}
          >
            {row.kind !== "chunk" ? (
              <ChevronRight
                className={cn(
                  "h-3.5 w-3.5 shrink-0 text-ink-faint transition-transform duration-150",
                  expanded && "rotate-90"
                )}
                strokeWidth={2.25}
              />
            ) : row.isTable ? (
              <Table2 className="h-3.5 w-3.5 shrink-0 text-[#5D6A53]" strokeWidth={2} />
            ) : (
              <FileText className="h-3.5 w-3.5 shrink-0 text-ink-faint" strokeWidth={1.75} />
            )}

            <span
              className={cn(
                "min-w-0 flex-1 truncate",
                row.kind === "doc" && "text-meta font-semibold text-ink",
                row.kind === "section" && "text-meta",
                row.kind === "chunk" && "font-mono text-micro"
              )}
            >
              {row.label}
            </span>

            {row.kind !== "chunk" && (
              <span className="shrink-0 font-mono text-micro tabular-nums text-ink-faint">{row.count}</span>
            )}
            {selected && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent" aria-hidden />}
          </button>
        );
      })}
    </div>
  );
}
