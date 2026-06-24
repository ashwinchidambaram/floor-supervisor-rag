"""Embeddings — fastembed (local ONNX, no PyTorch) behind a tiny typed interface.

Role:     Turn text into vectors for RAG. Local + offline + free, so the demo never
          depends on an embeddings API or a GPU.
Contract:
  embed_texts(list[str]) -> np.ndarray  shape (n, DIM), float32, L2-normalized.
  embed_query(str)       -> np.ndarray  shape (DIM,)   float32, L2-normalized.
  Each unique string is cached in Redis (namespace "emb"), so repeat embeds are free.
Failure:  Model download (first call only) needs network; after that it's fully local.
          Cache errors degrade to recompute (see cache.py). Embedding itself raising is
          a hard error — a RAG step that can't embed should fail loudly, not silently
          return a zero vector.

Model:    BAAI/bge-small-en-v1.5 — 384-dim, ~130MB, strong quality-for-size. Vectors are
          L2-normalized so cosine similarity == dot product (cheaper search).
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from .cache import cache_get, cache_set

MODEL_NAME = "BAAI/bge-small-en-v1.5"
DIM = 384


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    """Load the ONNX model once per process (downloaded on first use, then cached on disk)."""
    return TextEmbedding(model_name=MODEL_NAME)


def _normalize(mat: np.ndarray) -> np.ndarray:
    """L2-normalize rows so cosine similarity reduces to a dot product."""
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    return mat / np.clip(norms, 1e-12, None)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch. Per-text Redis cache; only uncached texts hit the model."""
    if not texts:
        return np.zeros((0, DIM), dtype=np.float32)

    out = np.zeros((len(texts), DIM), dtype=np.float32)
    to_compute: list[tuple[int, str]] = []

    for i, text in enumerate(texts):
        hit = cache_get("emb", {"model": MODEL_NAME, "text": text})
        if hit is not None:
            out[i] = np.asarray(hit["vector"], dtype=np.float32)
        else:
            to_compute.append((i, text))

    if to_compute:
        fresh = np.asarray(list(_model().embed([t for _, t in to_compute])), dtype=np.float32)
        fresh = _normalize(fresh)
        for (i, text), vec in zip(to_compute, fresh):
            out[i] = vec
            cache_set("emb", {"model": MODEL_NAME, "text": text}, {"vector": vec.tolist()})

    return out


def embed_query(text: str) -> np.ndarray:
    """Embed a single query string -> 1-D vector."""
    return embed_texts([text])[0]
