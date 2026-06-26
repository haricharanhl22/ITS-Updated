"""
backend/app/rag/ingest.py
CLI ingestion script: chunk markdown lessons, embed, upsert to Supabase.

Usage:
    python -m app.rag.ingest
    python -m app.rag.ingest --corpus backend/app/rag/corpus
    python -m app.rag.ingest --dry-run

This script must be run from the `backend/` directory so that
`app.*` imports resolve correctly.
"""
import argparse
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest markdown lessons into pgvector.")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).parent / "corpus",
        help="Directory containing .md lesson files (default: app/rag/corpus)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print chunks without writing to Supabase",
    )
    args = parser.parse_args()

    corpus_dir: Path = args.corpus
    if not corpus_dir.exists():
        logger.error(f"Corpus directory not found: {corpus_dir}")
        sys.exit(1)

    md_files = sorted(corpus_dir.glob("*.md"))
    if not md_files:
        logger.error(f"No .md files found in {corpus_dir}")
        sys.exit(1)

    logger.info(f"Found {len(md_files)} lesson files in {corpus_dir}")

    # ── Chunking ─────────────────────────────────────────────────────────────
    from app.rag.chunker import chunk_directory

    t0 = time.perf_counter()
    all_chunks = list(chunk_directory(corpus_dir))
    logger.info(f"Chunked {len(md_files)} files → {len(all_chunks)} chunks in {time.perf_counter() - t0:.1f}s")

    if args.dry_run:
        for c in all_chunks:
            print(f"[p{c.page_number} c{c.chunk_index}] {c.concept} | {len(c.content)} chars | {c.content[:80].replace(chr(10), ' ')}…")
        return

    if not all_chunks:
        logger.warning("No chunks produced — nothing to ingest.")
        return

    # ── Embedding ─────────────────────────────────────────────────────────────
    from app.rag.embeddings import embed

    logger.info("Loading embedding model (may download ~90MB on first run)…")
    texts = [c.content for c in all_chunks]
    t1 = time.perf_counter()
    embeddings = embed(texts)
    logger.info(f"Embedded {len(embeddings)} chunks in {time.perf_counter() - t1:.1f}s")

    # ── Upsert to Supabase ────────────────────────────────────────────────────
    from app.rag.vector_store import upsert_chunks_batch, count_chunks

    logger.info("Upserting to Supabase textbook_chunks…")
    t2 = time.perf_counter()
    inserted = upsert_chunks_batch(all_chunks, embeddings)
    logger.info(f"Upserted {inserted} rows in {time.perf_counter() - t2:.1f}s")

    total = count_chunks()
    logger.info(f"✅ Ingestion complete. textbook_chunks now has {total} rows.")


if __name__ == "__main__":
    main()
