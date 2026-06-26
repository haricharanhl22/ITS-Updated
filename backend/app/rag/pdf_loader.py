"""
backend/app/rag/pdf_loader.py
Extract text from uploaded PDFs using pypdf (modern successor to PyPDF2).

Returns a list of (page_number, text) tuples — one per PDF page.
Empty pages are skipped. Text is lightly cleaned (collapse whitespace).
"""
from __future__ import annotations

import io
import logging
import re

logger = logging.getLogger(__name__)


def extract_pages_from_bytes(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """
    Parse a PDF from raw bytes and return a list of (page_num, page_text) tuples.
    page_num is 1-indexed.
    Raises ValueError if the file is not a valid PDF.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            # Fallback to PyPDF2 if pypdf not installed yet
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            raise RuntimeError("pypdf is not installed. Add 'pypdf>=4.0.0' to requirements.txt.")

    pages: list[tuple[int, str]] = []

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise ValueError(f"Could not parse PDF: {e}") from e

    total = len(reader.pages)
    logger.info(f"PDF has {total} pages")

    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.warning(f"Failed to extract text from page {i}: ({type(e).__name__}) {e}\n{tb}")
            text = ""

        # Light cleanup: collapse multiple spaces/newlines into single ones
        text = text.replace("\x00", "").replace("\u0000", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        if len(text) > 30:   # skip near-empty pages (headers/footers only)
            pages.append((i, text))
        else:
            logger.debug(f"Skipping page {i} (too short: {len(text)} chars)")

    logger.info(f"Extracted {len(pages)} non-empty pages from {total} total")
    return pages


def extract_pages_from_file(filepath: str) -> list[tuple[int, str]]:
    """Convenience wrapper: read a file from disk and extract pages."""
    with open(filepath, "rb") as f:
        return extract_pages_from_bytes(f.read())
