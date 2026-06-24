"""Vector store — exact cosine KNN over fastembed vectors, persisted in Redis.

Role:     The RAG retrieval surface. Add documents, search by query string, get the
          top-k most similar with scores. Deliberately simple and *exact*: brute-force
          cosine over a numpy matrix — no ANN index, no recall loss. At demo-corpus
          scale (thousands of chunks) this is microseconds and trivially auditable,
          which fits the "deterministic, defensible" line: retrieval is math, not a
          black-box index you have to trust.
Contract:
  store = VectorStore(index="docs")
  store.add(texts, metadatas)        -> ids        (embeds + persists to Redis)
  store.search(query, k) -> list[Hit]  (Hit = {id, score, text, metadata})
  store.count() -> int ; store.clear() -> None
Failure:  Redis unavailable at construction -> documents live in-memory only for the
          session (still fully functional, just not persisted) and a warning is logged.
          Embedding errors propagate (a RAG step that can't embed must fail loudly).

Persistence: each doc is a Redis hash  rag:{index}:{id}  -> {text, metadata, vector(bytes)}.
             On construction we eagerly load the index into a numpy matrix for search.
Upgrade path: swap this class for redis-stack (RediSearch HNSW) or Qdrant behind the same
             add()/search() interface when corpus size demands ANN — callers don't change.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import redis

from .embeddings import DIM, embed_query, embed_texts
from .redis_client import get_redis

log = logging.getLogger(__name__)


@dataclass
class Hit:
    """One retrieval result. score is cosine similarity in [-1, 1] (higher = closer)."""

    id: str
    score: float
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore:
    def __init__(self, index: str = "docs") -> None:
        self.index = index
        self._ids: list[str] = []
        self._texts: list[str] = []
        self._metas: list[dict] = []
        self._matrix = np.zeros((0, DIM), dtype=np.float32)  # (n, DIM), rows L2-normalized
        self._load_from_redis()

    # ---- persistence -------------------------------------------------------
    def _key(self, doc_id: str) -> str:
        return f"rag:{self.index}:{doc_id}"

    def _load_from_redis(self) -> None:
        """Eagerly pull any persisted docs for this index into memory. No-op if Redis is down."""
        try:
            r = get_redis()
            keys = list(r.scan_iter(match=f"rag:{self.index}:*"))
            for key in keys:
                h = r.hgetall(key)
                if not h:
                    continue
                self._ids.append(h[b"id"].decode())
                self._texts.append(h[b"text"].decode())
                self._metas.append(json.loads(h[b"metadata"]))
                vec = np.frombuffer(h[b"vector"], dtype=np.float32)
                self._matrix = (
                    vec.reshape(1, DIM)
                    if self._matrix.shape[0] == 0
                    else np.vstack([self._matrix, vec])
                )
            if keys:
                log.info("vector_store[%s]: loaded %d docs from Redis", self.index, len(keys))
        except redis.RedisError as e:
            log.warning("vector_store[%s]: Redis unavailable, in-memory only (%s)", self.index, e)

    def _persist(self, doc_id: str, text: str, metadata: dict, vector: np.ndarray) -> None:
        """Write one doc to Redis. Silent best-effort — in-memory copy is the source of truth."""
        try:
            get_redis().hset(
                self._key(doc_id),
                mapping={
                    "id": doc_id,
                    "text": text,
                    "metadata": json.dumps(metadata),
                    "vector": vector.astype(np.float32).tobytes(),
                },
            )
        except redis.RedisError:
            pass

    # ---- public API --------------------------------------------------------
    def add(self, texts: list[str], metadatas: list[dict] | None = None) -> list[str]:
        """Embed + store texts. Returns the generated ids (uuid4 hex)."""
        if not texts:
            return []
        metadatas = metadatas or [{} for _ in texts]
        if len(metadatas) != len(texts):
            raise ValueError("texts and metadatas must be the same length")

        vectors = embed_texts(texts)
        new_ids: list[str] = []
        for text, meta, vec in zip(texts, metadatas, vectors):
            doc_id = uuid.uuid4().hex
            new_ids.append(doc_id)
            self._ids.append(doc_id)
            self._texts.append(text)
            self._metas.append(meta)
            self._matrix = (
                vec.reshape(1, DIM)
                if self._matrix.shape[0] == 0
                else np.vstack([self._matrix, vec])
            )
            self._persist(doc_id, text, meta, vec)
        return new_ids

    @staticmethod
    def _matches(meta: dict, where: dict | None) -> bool:
        """True if meta equals every key in `where` (metadata equality filter, e.g. by source)."""
        return where is None or all(meta.get(key) == val for key, val in where.items())

    def search(self, query: str, k: int = 4, where: dict | None = None) -> list[Hit]:
        """Top-k by cosine similarity, optionally filtered by metadata (e.g. {'source': ...})."""
        if self._matrix.shape[0] == 0:
            return []
        idx = [i for i, m in enumerate(self._metas) if self._matches(m, where)]
        if not idx:
            return []
        q = embed_query(query)
        scores = self._matrix[idx] @ q  # cosine over the filtered rows only
        order = np.argsort(-scores)[: min(k, len(idx))]
        return [
            Hit(
                id=self._ids[idx[j]],
                score=float(scores[j]),
                text=self._texts[idx[j]],
                metadata=self._metas[idx[j]],
            )
            for j in order
        ]

    def subset(self, where: dict | None = None) -> tuple[list[str], list[str], list[dict], np.ndarray]:
        """Return (ids, texts, metas, matrix) for rows matching `where`. Powers source-scoped
        hybrid search: the caller runs dense (matrix) + BM25 (texts) over the same filtered slice."""
        idx = [i for i, m in enumerate(self._metas) if self._matches(m, where)]
        ids = [self._ids[i] for i in idx]
        texts = [self._texts[i] for i in idx]
        metas = [self._metas[i] for i in idx]
        mat = self._matrix[idx] if idx else np.zeros((0, DIM), dtype=np.float32)
        return ids, texts, metas, mat

    def count(self) -> int:
        return len(self._ids)

    def clear(self) -> None:
        """Drop this index from memory and Redis."""
        try:
            r = get_redis()
            keys = list(r.scan_iter(match=f"rag:{self.index}:*"))
            if keys:
                r.delete(*keys)
        except redis.RedisError:
            pass
        self._ids, self._texts, self._metas = [], [], []
        self._matrix = np.zeros((0, DIM), dtype=np.float32)
