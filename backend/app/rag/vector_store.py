"""
backend/app/rag/vector_store.py
Upserts text chunks + embeddings into the Supabase textbook_chunks table.
"""
import logging
from typing import TYPE_CHECKING

from app.config.supabase_client import supabase
from app.rag.chunker import TextChunk

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

TABLE = "textbook_chunks"


def upsert_chunk(chunk: TextChunk, embedding: list[float]) -> dict:
    """
    Insert or update a single chunk with its embedding.
    Uses page_number + chunk_index as a natural composite key.
    """
    row = {
        "page_number":  chunk.page_number,
        "chunk_index":  chunk.chunk_index,
        "content":      chunk.content,
        "embedding":    embedding,   # list[float] → Supabase converts to vector(384)
    }
    result = (
        supabase.table(TABLE)
        .upsert(row, on_conflict="page_number,chunk_index")
        .execute()
    )
    return result.data[0] if result.data else {}


def upsert_chunks_batch(chunks: list[TextChunk], embeddings: list[list[float]]) -> int:
    """
    Batch upsert all chunks. Returns count of rows inserted/updated.
    Supabase REST has a payload limit so we batch in groups of 50.
    """
    if not chunks:
        return 0

    batch_size = 50
    total = 0

    for start in range(0, len(chunks), batch_size):
        batch_chunks = chunks[start:start + batch_size]
        batch_embeds = embeddings[start:start + batch_size]

        rows = [
            {
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "content":     c.content,
                "embedding":   e,
            }
            for c, e in zip(batch_chunks, batch_embeds)
        ]

        result = (
            supabase.table(TABLE)
            .upsert(rows, on_conflict="page_number,chunk_index")
            .execute()
        )
        total += len(result.data or [])
        logger.info(f"Upserted batch {start // batch_size + 1}: {len(rows)} chunks")

    return total


def count_chunks() -> int:
    """Return the number of chunks currently in the table."""
    result = supabase.table(TABLE).select("id", count="exact").execute()
    return result.count or 0
