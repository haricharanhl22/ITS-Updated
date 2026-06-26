"""
backend/app/rag/embeddings.py
SentenceTransformer wrapper for generating 384-dim embeddings.
Model: all-MiniLM-L6-v2 (cached locally after first download ~90MB).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _get_model() -> "SentenceTransformer":
    """Load and cache the embedding model (lazy, on first call)."""
    from sentence_transformers import SentenceTransformer  # noqa: F401
    logger.info(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logger.info("Embedding model loaded successfully.")
    return model


def embed(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts. Returns a list of 384-dim vectors.
    Each vector is a Python list of floats (JSON-serialisable for Supabase).
    """
    if not texts:
        return []
    model = _get_model()
    vectors: np.ndarray = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,   # cosine similarity = dot product
    )
    return vectors.tolist()


def embed_one(text: str) -> list[float]:
    """Embed a single text string."""
    return embed([text])[0]
