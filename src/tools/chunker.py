"""chunker.py — element-aware markdown chunker for the plant-doc corpus.

Role:     Turn a controlled markdown document into typed `RetrievedChunk`s, chunked along
          STRUCTURAL boundaries (heading / prose / table) — never mid-table. This is the
          §5 "element-aware, not size-aware" requirement, built REAL for the actual docs
          (the spec assumed a mocked pre-chunked corpus; these are real documents).
Contract: chunk_markdown(path) -> list[RetrievedChunk]
          - PROSE chunks: one per prose block under a heading (split if very long).
          - TABLE chunks: one per markdown table, the full table in `table_markdown`; `text`
            is a DETERMINISTIC fallback caption (the LLM summarizer upgrades it at ingest).
          - `doc_version` is parsed from the document's header metadata table (load-bearing).
Failure:  A doc with no recognizable header table still chunks; `doc_version` falls back to
          "UNKNOWN" and `source` to `DocSource.UNKNOWN` (flagged, never invented).

Scope note: these docs contain no figures, so no FIGURE chunks are produced. Oversized
            tables (row-group split with header repeated) aren't needed here — the corpus
            tables are small — but the atomic-table rule is what makes that safe to add.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.state import DocSource, ElementType, RetrievedChunk

# Filename -> source (routing to a system of record is explicit, never guessed).
_SOURCE_BY_PREFIX = {
    "01": DocSource.SAFETY_PROCEDURES,
    "02": DocSource.MAINTENANCE_MANUALS,
    "03": DocSource.QUALITY_CONTROL,
}
_PROSE_SPLIT_CHARS = 1800  # split a prose block above this, on paragraph breaks


def _slug(text: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:n] or "x"


def _is_table_row(line: str) -> bool:
    return line.lstrip().startswith("|")


def _source_for(path: Path) -> DocSource:
    return _SOURCE_BY_PREFIX.get(path.name[:2], DocSource.UNKNOWN)


def _parse_header(lines: list[str]) -> tuple[str, str, str]:
    """From the top-of-doc metadata table, return (doc_title, doc_number, doc_version)."""
    title = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), "Untitled")
    number, version = "UNKNOWN", "UNKNOWN"
    for ln in lines:
        cells = [c.strip() for c in ln.split("|")[1:-1]] if _is_table_row(ln) else []
        if len(cells) == 2:
            key = cells[0].lower()
            if "document number" in key:
                number = cells[1]
            elif key in ("revision", "version"):
                version = cells[1]
    return title, number, version


def _table_caption(section: str, block: list[str]) -> str:
    """Deterministic, offline fallback caption: section + column headers + flattened cells.
    The LLM summarizer replaces this at ingest, but this keeps the chunker usable with no key."""
    rows = [[c.strip() for c in ln.split("|")[1:-1]] for ln in block if _is_table_row(ln)]
    rows = [r for r in rows if not all(set(c) <= {"-", ":"} for c in r)]  # drop the |---| separator
    headers = rows[0] if rows else []
    body_terms = [c for r in rows[1:] for c in r if c]
    return f"{section} | columns: {', '.join(headers)} | {'; '.join(body_terms)}"


def chunk_markdown(path: str | Path) -> list[RetrievedChunk]:
    path = Path(path)
    raw = path.read_text(encoding="utf-8").splitlines()
    source = _source_for(path)
    title, number, version = _parse_header(raw)

    chunks: list[RetrievedChunk] = []
    section = "Preamble"
    seen_first_heading = False  # everything before the first '##' is header/foreword metadata
    prose: list[str] = []
    table: list[str] = []
    counters = {"p": 0, "t": 0}

    def flush_prose() -> None:
        text = "\n".join(prose).strip()
        prose.clear()
        if not seen_first_heading or len(text) < 30:
            return  # skip the header block and trivial fragments
        for part in _split_prose(text):
            counters["p"] += 1
            chunks.append(_mk(source, title, version, number, section, ElementType.PROSE,
                             part, counters["p"]))

    def flush_table() -> None:
        if not table:
            return
        block = "\n".join(table)
        table.clear()
        counters["t"] += 1
        chunks.append(_mk(source, title, version, number, section, ElementType.TABLE,
                         _table_caption(section, block.splitlines()), counters["t"],
                         table_markdown=block))

    for line in raw:
        if line.startswith("## ") or line.startswith("### "):
            flush_prose()
            flush_table()
            section = line.lstrip("#").strip()
            seen_first_heading = True
        elif _is_table_row(line):
            flush_prose()
            table.append(line)
        else:
            flush_table()
            if line.strip():
                prose.append(line)
            elif prose:  # blank line ends a prose paragraph group only if long enough later
                prose.append("")
    flush_prose()
    flush_table()
    return chunks


def _split_prose(text: str) -> list[str]:
    """Keep prose blocks whole unless very long; then split on blank lines into ~even parts."""
    if len(text) <= _PROSE_SPLIT_CHARS:
        return [text]
    paras, buf, out = text.split("\n\n"), "", []
    for p in paras:
        if len(buf) + len(p) > _PROSE_SPLIT_CHARS and buf:
            out.append(buf.strip())
            buf = ""
        buf += p + "\n\n"
    if buf.strip():
        out.append(buf.strip())
    return out


def _mk(source, title, version, number, section, element_type, text, n,
        table_markdown=None) -> RetrievedChunk:
    kind = "t" if element_type == ElementType.TABLE else "p"
    return RetrievedChunk(
        chunk_id=f"{number}#{_slug(section)}#{kind}{n}",
        source=source,
        doc_title=title,
        doc_version=version,
        section=section,
        page=None,  # markdown has no pages; section carries the locator
        element_type=element_type,
        text=text,
        table_markdown=table_markdown,
    )
