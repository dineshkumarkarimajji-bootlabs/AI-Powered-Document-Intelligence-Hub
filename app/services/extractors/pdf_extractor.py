from PyPDF2 import PdfReader
from .base_extractor import BaseExtractor
from .image_extractor import ImageExtractor


class PDFExtractor(BaseExtractor):

    def extract(self, path: str) -> str:
        try:
            reader = PdfReader(path)

            text = "\n".join([
                page.extract_text() or ""
                for page in reader.pages
            ])

            # If text exists → return it
            if text.strip():
                return text

            # OCR fallback for scanned PDFs
            return ImageExtractor().extract(path)

        except Exception:
            # Fallback even if PDF parsing fails
            return ImageExtractor().extract(path)

            return ImageExtractor().extract(path)
