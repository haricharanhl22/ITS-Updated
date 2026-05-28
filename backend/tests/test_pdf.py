from app.infrastructure.pdf.pymupdf_reader import PyMuPDFReader
from app.infrastructure.pdf.text_cleaner import TextCleaner
from app.infrastructure.pdf.chunker import Chunker


pdf_path = "storage/pdfs/pythonlearn.pdf"

reader = PyMuPDFReader()
cleaner = TextCleaner()
chunker = Chunker(chunk_size=200)

pages = reader.extract_text(pdf_path)

cleaned_pages = []

for page in pages:
    cleaned_pages.append({
        "page": page["page"],
        "text": cleaner.clean(page["text"])
    })

chunks = chunker.chunk_pages(cleaned_pages)

print("Pages:", len(pages))
print("Chunks:", len(chunks))

print("\nFirst chunk:\n")
print(chunks[7]["text"])