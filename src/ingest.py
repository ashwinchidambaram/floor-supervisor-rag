"""ingest.py — build the RAG index from the real plant docs. Run: python -m src.ingest

Pipeline (build-time): for each markdown doc ->
  1. element-aware chunk (chunker)               — prose blocks + atomic table chunks
  2. summarize TABLE chunks (LLM, cached)        — searchable caption; full table kept verbatim
  3. embed (fastembed, local) + persist (Redis)  — into the `kb` VectorStore, source in metadata
Then a verification pass runs two sample queries (a semantic one and an exact-identifier one)
so we can SEE retrieval working before wiring it into the graph.

This is the §5 retrieval foundation built REAL on the actual corpus. Query-time retrieval
(`hybrid_search`) reads this index; the §11 graph tests still run offline with forced stubs.
"""

from __future__ import annotations

import glob
import time

from src.state import DocSource, ElementType
from src.tools.chunker import chunk_markdown
from src.tools.hybrid_search import KB_INDEX, _store, hybrid_search
from src.tools.table_summary import summarize_table
from src.tools.vector_store import VectorStore

CORPUS_GLOB = "knowledge_documents_rag/*.md"


def ingest() -> VectorStore:
    # Populate the SAME cached singleton that hybrid_search + /health read, so the index is
    # consistent even without Redis (HF deploy has no Redis; ingest persists in-process).
    store = _store()
    store.clear()  # fresh build — no duplicate chunks across re-runs

    total_prose, total_tables, llm_calls, fallbacks = 0, 0, 0, 0
    for path in sorted(glob.glob(CORPUS_GLOB)):
        chunks = chunk_markdown(path)
        for c in chunks:
            if c.element_type == ElementType.TABLE:
                total_tables += 1
                try:
                    caption = summarize_table(c.section, c.table_markdown or "")["caption"]
                    c.text = f"{c.section} — {caption}"  # section-prefixed for retrievability
                    llm_calls += 1
                except Exception as e:  # LLM/network down -> keep the deterministic caption
                    fallbacks += 1
                    print(f"  ! table summary fell back to deterministic caption ({type(e).__name__})")
            else:
                total_prose += 1

        # one batched embed+persist per doc (fastembed batches internally)
        store.add([c.text for c in chunks], [c.model_dump(mode="json") for c in chunks])
        v = chunks[0].doc_version if chunks else "?"
        src = chunks[0].source.value if chunks else "?"
        print(f"  indexed {path.split('/')[-1]:32s} [{src} v{v}] : {len(chunks)} chunks")

    print(f"\n  totals: {store.count()} chunks ({total_prose} prose, {total_tables} tables) | "
          f"table summaries: {llm_calls} LLM, {fallbacks} fallback")
    return store


def _verify() -> None:
    """Prove retrieval works on the freshly built index — one semantic, one exact-identifier."""
    print("\n--- verification ---")
    # Semantic: natural-language question -> should hit the torque-spec table.
    q1 = "What torque should the CNC vise jaw bolts be tightened to?"
    hits = hybrid_search(q1, DocSource.MAINTENANCE_MANUALS, top_k=3)
    print(f"Q1 (semantic): {q1}")
    for h in hits:
        tag = "TABLE" if h.element_type == ElementType.TABLE else "prose"
        print(f"   [{h.score:.3f}] {tag} · {h.section[:42]} · {h.doc_title} v{h.doc_version}")
    top = hits[0]
    if top.element_type == ElementType.TABLE and "80 N" in (top.table_markdown or ""):
        print("   -> top hit is the torque TABLE; value '80 N·m' present in verbatim markdown ✔")

    # Exact-identifier: BM25 half should surface the fault-code table for "Alarm 144".
    q2 = "Alarm 144 way lube low"
    hits2 = hybrid_search(q2, DocSource.MAINTENANCE_MANUALS, top_k=3)
    print(f"Q2 (exact id): {q2}")
    for h in hits2:
        tag = "TABLE" if h.element_type == ElementType.TABLE else "prose"
        print(f"   [{h.score:.3f}] {tag} · {h.section[:42]}")


def main() -> None:
    t0 = time.perf_counter()
    print("Building RAG index from", CORPUS_GLOB)
    ingest()
    _verify()
    print(f"\nDone in {time.perf_counter()-t0:.1f}s. Index persisted in Redis (VectorStore '{KB_INDEX}').")


if __name__ == "__main__":
    main()
