// ---------------------------------------------------------------------------
// AnswerBody — render an assembled answer verbatim and honestly.
//
// Role:     Walk answer_text top-to-bottom and render each block in place:
//           prose paragraphs (markdown **bold** kept as ink), real verbatim
//           <table>s (parseMarkdownTable, multiple allowed per answer), and any
//           line that starts with ⚠︎ as a calm danger NOTICE block (full border,
//           danger soft bg, alert icon — never a side-stripe, never terracotta).
// Contract: <AnswerBody text={turn.answer_text} />. Empty/null → nothing.
// Failure:  a malformed table falls back to raw <pre>; nothing throws.
// ---------------------------------------------------------------------------

import { Fragment, type ReactNode } from "react";
import { TriangleAlert } from "lucide-react";
import { parseMarkdownTable } from "@/components/qna/markdownTable";

/** Split `**value**` runs into <strong> while keeping them ink-colored. */
function renderInline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    const m = part.match(/^\*\*([^*]+)\*\*$/);
    if (m) {
      return (
        <strong key={i} className="font-semibold text-ink">
          {m[1]}
        </strong>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

/** A separator row `|---|---|` marks the start of a table directly under a header. */
function isSeparator(line: string): boolean {
  return /^\s*\|?[\s:-]*\|[\s:|-]*$/.test(line) && line.includes("-");
}

type Block =
  | { kind: "prose"; lines: string[] }
  | { kind: "table"; markdown: string }
  | { kind: "notice"; text: string };

/** Segment answer_text into ordered prose / table / ⚠︎-notice blocks. */
function segment(text: string): Block[] {
  const lines = text.split("\n");
  const blocks: Block[] = [];
  let prose: string[] = [];

  const flushProse = () => {
    if (prose.length) {
      blocks.push({ kind: "prose", lines: prose });
      prose = [];
    }
  };

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];

    // A ⚠︎ line is an honest-uncertainty notice — its own block.
    if (line.trimStart().startsWith("⚠︎")) {
      flushProse();
      blocks.push({ kind: "notice", text: line.trimStart().replace(/^⚠︎\s*/, "") });
      continue;
    }

    // A header line followed by a |---| separator starts a verbatim table.
    if (line.includes("|") && isSeparator(lines[i + 1] ?? "")) {
      flushProse();
      let end = i + 1;
      while (end + 1 < lines.length && lines[end + 1].trim().startsWith("|")) end += 1;
      blocks.push({ kind: "table", markdown: lines.slice(i, end + 1).join("\n") });
      i = end;
      continue;
    }

    if (line.trim()) prose.push(line);
    else flushProse(); // blank line = paragraph break
  }
  flushProse();
  return blocks;
}

export function AnswerBody({ text }: { text: string | null | undefined }) {
  if (!text?.trim()) return null;
  const blocks = segment(text);

  return (
    <div className="space-y-3">
      {blocks.map((block, i) => {
        if (block.kind === "notice") return <UncertaintyNotice key={i} text={block.text} />;
        if (block.kind === "table") return <AnswerTable key={i} markdown={block.markdown} />;
        return (
          <div key={i} className="space-y-2 text-body text-ink">
            {block.lines.map((line, j) => (
              <p key={j} className="leading-relaxed">
                {renderInline(line)}
              </p>
            ))}
          </div>
        );
      })}
    </div>
  );
}

/** Honest partial-evidence line → a calm danger notice (full border, no alarm). */
function UncertaintyNotice({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-[rgba(216,86,80,0.40)] bg-danger-soft px-3.5 py-3 text-danger">
      <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2} aria-hidden />
      <p className="text-meta leading-relaxed">{text}</p>
    </div>
  );
}

/** A TABLE chunk rendered as a real, verbatim <table>. */
function AnswerTable({ markdown }: { markdown: string }) {
  const parsed = parseMarkdownTable(markdown);
  if (!parsed) {
    return (
      <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg border border-border bg-surface-alt px-3 py-2 font-mono text-meta text-ink-muted">
        {markdown}
      </pre>
    );
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full border-collapse text-meta">
        <thead>
          <tr className="bg-surface-alt">
            {parsed.headers.map((h, i) => (
              <th
                key={i}
                className="border-b border-border px-3 py-2 text-left font-mono text-micro font-semibold uppercase tracking-[0.06em] text-ink"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {parsed.rows.map((row, r) => (
            <tr key={r} className="border-b border-subtle last:border-0">
              {row.map((cell, c) => (
                <td
                  key={c}
                  className={c === 0 ? "px-3 py-2 align-top font-medium text-ink" : "px-3 py-2 align-top text-ink-muted"}
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
