"""table_summary.py — LLM-generated searchable caption for a TABLE chunk (ingest-time).

Role:     Produce the EMBEDDED representation of a table: a short NL description so semantic
          search can find it. The full table is returned verbatim elsewhere (table_markdown),
          so this text affects retrieval RECALL only — never the delivered value.
Contract: summarize_table(section, table_markdown) -> str (the caption to embed).
          Result is cached in Redis (namespace "tablesum"), so re-ingest is free and
          deterministic across runs.
Failure:  Any LLM/network error -> raises to the caller; the ingest orchestrator catches it
          and falls back to the deterministic caption from chunker._table_caption (no key,
          no crash). The summary is an enhancement, never a hard dependency.

Model:    `table_summarizer` in config.MODEL_MAP (cheap tier) — see the model-risk record.
"""

from __future__ import annotations

from src.config import complete
from src.tools.cache import cached

_PROMPT = (
    "You are writing a SEARCH CAPTION for a table from a manufacturing-plant document. "
    "Given the section title and the table, write 1-3 plain sentences describing what the "
    "table contains and the key entities, identifiers, and values a reader might search for "
    "(equipment names, part/fastener codes, fault codes, spec values with units). "
    "Describe only what is present — do NOT invent, interpret, or add values not in the table. "
    "Output only the caption, no preamble."
)


@cached("tablesum", ttl=60 * 60 * 24 * 30)  # 30 days; keyed on (section, table_markdown)
def summarize_table(section: str, table_markdown: str) -> dict:
    """Return {'caption': str}. Cached by the decorator on its arguments."""
    caption = complete(
        "table_summarizer",
        [
            {"role": "system", "content": _PROMPT},
            {"role": "user", "content": f"Section: {section}\n\nTable:\n{table_markdown}"},
        ],
        max_tokens=200,
        temperature=0,
    ).strip()
    return {"caption": caption}
