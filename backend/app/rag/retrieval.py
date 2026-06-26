"""
backend/app/rag/retrieval.py
pgvector cosine similarity search via Supabase RPC.

Requires this SQL function in your Supabase project (run setup.sql once):

    CREATE OR REPLACE FUNCTION match_chunks(
      query_embedding vector(384),
      match_threshold float,
      match_count int
    )
    RETURNS TABLE (
      id bigint,
      content text,
      page_number int,
      chunk_index int,
      similarity float
    )
    LANGUAGE sql STABLE
    AS $$
      SELECT id, content, page_number, chunk_index,
             1 - (embedding <=> query_embedding) AS similarity
      FROM textbook_chunks
      WHERE 1 - (embedding <=> query_embedding) > match_threshold
      ORDER BY embedding <=> query_embedding
      LIMIT match_count;
    $$;
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from app.config.supabase_client import supabase
from app.rag.embeddings import embed_one

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    id: int
    content: str
    page_number: int
    chunk_index: int
    similarity: float

    def excerpt(self, max_chars: int = 300) -> str:
        """Return a truncated excerpt of the content for the UI."""
        if len(self.content) <= max_chars:
            return self.content
        return self.content[:max_chars].rsplit(" ", 1)[0] + "…"


def _search_sync(
    query_embedding: list[float],
    match_count: int,
    match_threshold: float,
) -> list[RetrievedChunk]:
    """Synchronous pgvector cosine search via Supabase RPC."""
    try:
        result = supabase.rpc(
            "match_chunks",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
            },
        ).execute()

        chunks = []
        for row in result.data or []:
            chunks.append(RetrievedChunk(
                id=row["id"],
                content=row["content"],
                page_number=row.get("page_number", 0),
                chunk_index=row.get("chunk_index", 0),
                similarity=float(row.get("similarity", 0.0)),
            ))
        return chunks

    except Exception as e:
        logger.warning(f"pgvector search failed: {e}. Falling back to keyword search.")
        return _keyword_fallback(query_embedding, match_count)


def _keyword_fallback(
    query_embedding: list[float],
    match_count: int,
) -> list[RetrievedChunk]:
    """
    Fallback: fetch all chunks and return first N.
    Used when match_chunks RPC isn't deployed yet.
    """
    try:
        result = (
            supabase.table("textbook_chunks")
            .select("id, content, page_number, chunk_index")
            .limit(match_count)
            .execute()
        )
        return [
            RetrievedChunk(
                id=row["id"],
                content=row["content"],
                page_number=row.get("page_number", 0),
                chunk_index=row.get("chunk_index", 0),
                similarity=0.5,
            )
            for row in (result.data or [])
        ]
    except Exception as e:
        logger.error(f"Keyword fallback also failed: {e}")
        return []


async def retrieve(
    question: str,
    match_count: int = 5,
    match_threshold: float = 0.35,
) -> list[RetrievedChunk]:
    """
    Embed the question and retrieve the top-k most similar chunks.
    Returns an empty list if the textbook_chunks table is empty.
    """
    try:
        embedding = await asyncio.to_thread(embed_one, question)
        chunks = await asyncio.to_thread(
            _search_sync, embedding, match_count, match_threshold
        )
        return chunks
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return []
