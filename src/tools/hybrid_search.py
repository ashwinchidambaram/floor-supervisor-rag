"""hybrid_search.py — the §4b retrieval tool: dense + BM25, fused via RRF, source-filtered.

Role:     Given a sub-question and a routed source, return the top-k most relevant chunks.
          Hybrid because plant queries mix natural language ("how do I clear a way-lube
          alarm") with exact identifiers ("Alarm 144", "M12 grade 8.8", "SP-VF4-DB-22") —
          dense search handles the former, BM25 the latter; RRF fuses them.
Contract: hybrid_search(query_text, source, top_k) -> list[RetrievedChunk]
          - source-filtered (only the routed system of record is searched).
          - each chunk's `score` is its DENSE cosine similarity in [0,1] — the interpretable
            signal the deterministic confidence floors gate on (RRF is used only for ordering).
Failure:  empty index for that source -> [] (EMPTY_INDEX); embed error -> [] (EMBED_ERROR).
          Never raises into the graph — retrieval failure is empty evidence, not a crash.

Index:    the Redis-backed `kb` VectorStore (built by src/ingest.py). Loaded once per process.
"""

from __future__ import annotations

import re
from functools import lru_cache

import numpy as np
from rank_bm25 import BM25Okapi

from src.state import DocSource, RetrievedChunk
from src.tools.embeddings import embed_query
from src.tools.vector_store import VectorStore

KB_INDEX = "kb"
_RRF_K = 60  # standard Reciprocal Rank Fusion constant


@lru_cache(maxsize=1)
def _store() -> VectorStore:
    return VectorStore(index=KB_INDEX)


def _tokenize(text: str) -> list[str]:
    """Lowercase tokens that KEEP identifiers intact (m12-a307, sp-vf4-db-22, 144)."""
    return re.findall(r"[a-z0-9][a-z0-9\-\.]*", text.lower())


def _rrf(rankings: list[list[str]]) -> dict[str, float]:
    """Reciprocal Rank Fusion: sum 1/(k+rank) across each ranker's ordered id list."""
    fused: dict[str, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking):
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (_RRF_K + rank + 1)
    return fused


def hybrid_search(query_text: str, source: DocSource, top_k: int = 5) -> list[RetrievedChunk]:
    ids, texts, metas, mat = _store().subset(where={"source": source.value})
    if not ids:
        return []  # EMPTY_INDEX for this source

    try:
        q = embed_query(query_text)
    except Exception:
        return []  # EMBED_ERROR

    # Dense: cosine of the query against every chunk in this source (normalized -> dot product).
    dense_scores = mat @ q
    dense_rank = [ids[i] for i in np.argsort(-dense_scores)]

    # Sparse: BM25 over the same source-filtered chunk texts.
    bm25 = BM25Okapi([_tokenize(t) for t in texts])
    bm25_scores = bm25.get_scores(_tokenize(query_text))
    bm25_rank = [ids[i] for i in np.argsort(-bm25_scores)]

    # Fuse rankings; carry the interpretable dense cosine as each chunk's score.
    fused = _rrf([dense_rank, bm25_rank])
    cosine_by_id = {ids[i]: float(dense_scores[i]) for i in range(len(ids))}
    meta_by_id = {ids[i]: metas[i] for i in range(len(ids))}

    ordered = sorted(fused, key=lambda c: fused[c], reverse=True)[:top_k]
    return [
        RetrievedChunk(**{**meta_by_id[cid], "score": cosine_by_id[cid]})
        for cid in ordered
    ]
