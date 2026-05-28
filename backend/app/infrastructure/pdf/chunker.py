class Chunker:

    def __init__(self, chunk_size=300):
        self.chunk_size = chunk_size

    def chunk_pages(self, pages):

        chunks = []

        for page_data in pages:

            page_number = page_data["page"]
            text = page_data["text"]

            words = text.split()

            for i in range(0, len(words), self.chunk_size):

                chunk_text = " ".join(
                    words[i:i + self.chunk_size]
                )

                chunks.append({
                    "page": page_number,
                    "chunk_id": len(chunks),
                    "text": chunk_text
                })

        return chunks