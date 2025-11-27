from pathlib import Path
from .pdf_extractor import PDFExtractor
from .docx_extractor import DocxExtractor
from .image_extractor import ImageExtractor
from .text_extractor import TextExtractor
from .audio_extractor import AudioExtractor

class ExtractorFactory:

    @staticmethod
    def get_extractor(path: str):
        ext = Path(path).suffix.lower()

        # Lazy-load imports ONLY when needed
        if ext == ".pdf":
            
            return PDFExtractor()

        if ext == ".docx":
            return DocxExtractor()

        if ext in [".png", ".jpg", ".jpeg"]:
            
            return ImageExtractor()

        if ext in [".txt", ".rtf"]:
            
            return TextExtractor()

        if ext in [".mp3", ".wav", ".m4a", ".mp4", ".aac"]:
            
            return AudioExtractor()

        return None
