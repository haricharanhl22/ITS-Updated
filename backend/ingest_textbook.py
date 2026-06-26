"""
backend/ingest_textbook.py
CLI script to ingest the local textbook PDF directly into the Supabase database.
Once executed, the textbook chunks and embeddings are stored in the shared database
and are immediately available for all students.

Usage:
    cd backend
    python ingest_textbook.py
"""

import os
import sys
from pathlib import Path

# Load env variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # Fallback manual parser
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

from app.config.settings import settings
from app.rag.pdf_loader import extract_pages_from_bytes
from app.rag.chunker import chunk_text
from app.rag.embeddings import embed
from app.rag.vector_store import upsert_chunks_batch, count_chunks

DEFAULT_PDF = Path(__file__).parent / "storage" / "pdfs" / "pythonlearn.pdf"

def main():
    print("=" * 60)
    print("HCAI-ITS Textbook Ingestion CLI Tool")
    print("=" * 60)
    
    if not DEFAULT_PDF.exists():
        print(f"ERROR: Default textbook PDF not found at: {DEFAULT_PDF}")
        print("Please place the textbook PDF in backend/storage/pdfs/pythonlearn.pdf")
        sys.exit(1)
        
    print(f"Reading textbook file: {DEFAULT_PDF.name} ({DEFAULT_PDF.stat().st_size / 1024 / 1024:.2f} MB)")
    pdf_bytes = DEFAULT_PDF.read_bytes()
    
    print("\nStep 1: Extracting text from PDF...")
    try:
        pages = extract_pages_from_bytes(pdf_bytes)
        print(f"[OK] Extracted {len(pages)} non-empty pages.")
    except Exception as e:
        print(f"[FAIL] PDF text extraction failed: {e}")
        sys.exit(1)
        
    if not pages:
        print("[WARNING] PDF text extraction yielded 0 pages. Aborting.")
        sys.exit(0)
        
    print("\nStep 2: Building overlapping text chunks...")
    all_chunks = []
    concept_label = DEFAULT_PDF.name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
    
    for page_num, page_text in pages:
        chunks = chunk_text(page_text, page_number=page_num, concept=concept_label)
        all_chunks.extend(chunks)
        
    print(f"[OK] Generated {len(all_chunks)} chunks.")
    
    if not all_chunks:
        print("[WARNING] 0 chunks were built. Aborting.")
        sys.exit(0)
        
    print("\nStep 3: Generating SentenceTransformer embeddings (all-MiniLM-L6-v2)...")
    try:
        texts = [c.content for c in all_chunks]
        embeddings = embed(texts)
        print(f"[OK] Generated {len(embeddings)} vectors of dimension 384.")
    except Exception as e:
        print(f"[FAIL] Embedding generation failed: {e}")
        sys.exit(1)
        
    print("\nStep 4: Upserting to Supabase database (textbook_chunks table)...")
    try:
        saved_count = upsert_chunks_batch(all_chunks, embeddings)
        total_chunks = count_chunks()
        print(f"[OK] Successfully saved {saved_count} chunks.")
        print(f"[OK] Database now contains a total of {total_chunks} chunks.")
    except Exception as e:
        print(f"[FAIL] Database upsert failed: {e}")
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("[SUCCESS] Ingestion complete! The RAG knowledge base is fully populated.")
    print("=" * 60)

if __name__ == "__main__":
    main()
