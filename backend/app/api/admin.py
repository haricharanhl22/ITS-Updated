"""
backend/app/api/admin.py
Admin endpoints — PDF ingestion pipeline + chunk inspection.

Endpoints:
  POST /api/admin/ingest-pdf   — multipart PDF upload → RAG pipeline
  GET  /api/admin/chunks       — return stored chunk count + sample

The ingest pipeline:
  1. Receive PDF bytes via multipart upload
  2. Extract text per page using PyPDF2 (pdf_loader.py)
  3. Chunk each page into ~500-char overlapping segments (chunker.py)
  4. Generate 384-dim SentenceTransformer embeddings (embeddings.py)
  5. Batch-upsert to Supabase textbook_chunks (vector_store.py)

No auth required for admin endpoints (internal/admin tool).
Add bearer token check here if you need access control.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class IngestResponse(BaseModel):
    filename:     str
    pages_found:  int
    chunks_built: int
    chunks_saved: int
    total_chunks: int     # total rows now in textbook_chunks table
    message:      str


class ChunkSample(BaseModel):
    id:          int
    page_number: int
    chunk_index: int
    excerpt:     str


class ChunksResponse(BaseModel):
    total_chunks: int
    samples:      list[ChunkSample]


# ---------------------------------------------------------------------------
# Helper: run the full ingest pipeline in a thread (sync ops)
# ---------------------------------------------------------------------------

def _ingest_pdf_sync(
    pdf_bytes: bytes,
    filename: str,
) -> tuple[int, int, int, int]:
    """
    Synchronous ingest pipeline. Returns (pages_found, chunks_built, chunks_saved, total).
    Runs in asyncio.to_thread so the event loop stays unblocked.
    """
    from app.rag.pdf_loader  import extract_pages_from_bytes
    from app.rag.chunker     import chunk_text, TextChunk
    from app.rag.embeddings  import embed
    from app.rag.vector_store import upsert_chunks_batch, count_chunks

    # 1. Extract pages
    pages = extract_pages_from_bytes(pdf_bytes)
    pages_found = len(pages)
    if not pages:
        return 0, 0, 0, count_chunks()

    # 2. Chunk each page
    all_chunks: list[TextChunk] = []
    for page_num, page_text in pages:
        # Derive a loose concept label from filename (e.g., "python_functions.pdf" → "Python Functions")
        concept_label = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
        chunks = chunk_text(page_text, page_number=page_num, concept=concept_label)
        all_chunks.extend(chunks)

    chunks_built = len(all_chunks)
    if not all_chunks:
        return pages_found, 0, 0, count_chunks()

    # 3. Generate embeddings
    texts = [c.content for c in all_chunks]
    embeddings = embed(texts)   # list[list[float]], each 384-dim

    # 4. Upsert to Supabase
    saved = upsert_chunks_batch(all_chunks, embeddings)
    total = count_chunks()

    return pages_found, chunks_built, saved, total


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/ingest-pdf", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...)):
    """
    Upload a Python textbook PDF and ingest it into the RAG knowledge base.

    The file goes through: PDF extraction → chunking → SentenceTransformer
    embedding → Supabase vector store upsert.

    Returns chunk counts so the frontend can display progress.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted. Upload a .pdf file.",
        )

    try:
        pdf_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {e}",
        )

    if len(pdf_bytes) < 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file appears to be empty or corrupt.",
        )

    logger.info(f"PDF ingest started: {file.filename} ({len(pdf_bytes):,} bytes)")

    try:
        pages_found, chunks_built, chunks_saved, total_chunks = await asyncio.to_thread(
            _ingest_pdf_sync, pdf_bytes, file.filename
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.exception(f"Ingest pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion pipeline error: {e}",
        )

    logger.info(
        f"PDF ingest complete: {file.filename} | "
        f"pages={pages_found} chunks_built={chunks_built} saved={chunks_saved} total={total_chunks}"
    )

    return IngestResponse(
        filename=file.filename,
        pages_found=pages_found,
        chunks_built=chunks_built,
        chunks_saved=chunks_saved,
        total_chunks=total_chunks,
        message=(
            f"Successfully ingested '{file.filename}'. "
            f"Built {chunks_built} chunks from {pages_found} pages. "
            f"Knowledge base now has {total_chunks} chunks."
        ),
    )


@router.get("/chunks", response_model=ChunksResponse)
async def list_chunks(limit: int = 10):
    """
    Return the total chunk count and a sample of stored textbook chunks.
    Useful for verifying the RAG knowledge base is populated.
    """
    from app.config.supabase_client import supabase

    def _query():
        total_res = (
            supabase.table("textbook_chunks")
            .select("id", count="exact")
            .execute()
        )
        sample_res = (
            supabase.table("textbook_chunks")
            .select("id, page_number, chunk_index, content")
            .order("id", desc=True)
            .limit(min(limit, 20))
            .execute()
        )
        return (total_res.count or 0), (sample_res.data or [])

    try:
        total, rows = await asyncio.to_thread(_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    samples = [
        ChunkSample(
            id=r["id"],
            page_number=r.get("page_number", 0),
            chunk_index=r.get("chunk_index", 0),
            excerpt=r["content"][:200].strip() + ("…" if len(r["content"]) > 200 else ""),
        )
        for r in rows
    ]

    return ChunksResponse(total_chunks=total, samples=samples)
