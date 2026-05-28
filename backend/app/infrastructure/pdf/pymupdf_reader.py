import fitz


class PyMuPDFReader:

    def extract_text(self, pdf_path: str):

        doc = fitz.open(pdf_path)

        pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            text = page.get_text("text")

            pages.append({
                "page": page_num + 1,
                "text": text
            })

        doc.close()

        return pages