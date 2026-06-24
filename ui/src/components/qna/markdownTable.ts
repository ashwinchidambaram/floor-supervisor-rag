// ---------------------------------------------------------------------------
// markdownTable — parse a GitHub-flavored markdown table into header + rows.
//
// Role:     Turn a `table_markdown` string (verbatim from a TABLE chunk) into a
//           typed { headers, rows } shape the <AnswerTable> renders as a real
//           <table>. The contract is "render verbatim, never reformatted" — so
//           this splits on the pipe grid ONLY; it does not rewrite cell content.
// Contract: parseMarkdownTable(md) -> { headers: string[]; rows: string[][] } | null.
//           Returns null when the string isn't a pipe table (caller falls back to
//           rendering the raw text), so a malformed table never throws.
// Failure:  Non-table or empty input -> null. No exceptions cross this seam.
// ---------------------------------------------------------------------------

export interface ParsedTable {
  headers: string[];
  rows: string[][];
}

/** Split one markdown table row `| a | b |` into trimmed cells, dropping the edge pipes. */
function splitRow(line: string): string[] {
  const trimmed = line.trim().replace(/^\|/, "").replace(/\|$/, "");
  return trimmed.split("|").map((cell) => cell.trim());
}

/** A separator row is the `|---|---|` alignment line under the header. */
function isSeparator(line: string): boolean {
  return /^\s*\|?[\s:-]*\|[\s:|-]*$/.test(line) && line.includes("-");
}

/**
 * Parse a GFM pipe table. Returns null if `md` is empty or not a pipe table,
 * letting the caller fall back to plain text. Cell content is preserved verbatim.
 */
export function parseMarkdownTable(md: string | null | undefined): ParsedTable | null {
  if (!md) return null;
  const lines = md.split("\n").filter((l) => l.trim().length > 0);
  if (lines.length < 2) return null;
  if (!lines[0].includes("|")) return null;
  if (!isSeparator(lines[1])) return null;

  const headers = splitRow(lines[0]);
  const rows = lines.slice(2).map(splitRow);
  return { headers, rows };
}

/**
 * Strip a leading markdown table out of an answer so prose + table render as
 * distinct blocks. Returns the prose before the table and the table markdown.
 * If no table is present, `table` is null and `prose` is the whole string.
 */
export function splitProseAndTable(text: string): { prose: string; table: string | null } {
  const lines = text.split("\n");
  const tableStart = lines.findIndex(
    (line, i) => line.includes("|") && isSeparator(lines[i + 1] ?? "")
  );
  if (tableStart === -1) return { prose: text.trim(), table: null };

  // Table runs from its header to the last consecutive pipe line.
  let tableEnd = tableStart + 1;
  while (tableEnd + 1 < lines.length && lines[tableEnd + 1].trim().startsWith("|")) {
    tableEnd += 1;
  }
  const prose = lines.slice(0, tableStart).join("\n").trim();
  const table = lines.slice(tableStart, tableEnd + 1).join("\n");
  return { prose, table };
}
