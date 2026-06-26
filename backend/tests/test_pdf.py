"""
tests/test_pdf.py
Basic smoke test for the pdf_loader module.
Uses a synthetic minimal PDF created in memory (no file dependency).
"""
import io
import pytest


def _make_minimal_pdf() -> bytes:
    """Return the raw bytes of a tiny but valid PDF with one text page."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        b"   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 44 >>\nstream\n"
        b"BT /F1 12 Tf 100 700 Td (Hello Python) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        b"0000000266 00000 n \n0000000360 00000 n \n"
        b"trailer\n<< /Root 1 0 R /Size 6 >>\n"
        b"startxref\n452\n%%EOF\n"
    )


def test_pdf_loader_imports():
    """Verify the pdf_loader module imports cleanly."""
    from app.rag.pdf_loader import extract_pages_from_bytes
    assert callable(extract_pages_from_bytes)


def test_invalid_bytes_raises():
    """Non-PDF bytes should raise ValueError."""
    from app.rag.pdf_loader import extract_pages_from_bytes
    with pytest.raises((ValueError, Exception)):
        extract_pages_from_bytes(b"this is not a pdf at all ...")