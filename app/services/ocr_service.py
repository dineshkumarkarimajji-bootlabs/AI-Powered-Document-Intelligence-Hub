import os
from pathlib import Path
from PyPDF2 import PdfReader
import easyocr
from app.services.transcription_service import transcription_service


reader = easyocr.Reader(['en'], gpu=False)

def extract_text(path: str):
    ext = Path(path).suffix.lower()

    # Handle PDF safely
    if ext == ".pdf" or ext == ".docx":
        try:
            reader_pdf = PdfReader(path)
            text = "\n".join([page.extract_text() or "" for page in reader_pdf.pages])
            return text if text.strip() else "[PDF contains no text layer]"
        except Exception:
            # PDF is corrupted OR actually not a PDF
            return extract_image_or_raise(path)

    # Handle text files
    if ext == ".txt" or ext == ".rtf":
        with open(path, "r", errors="ignore") as f:
            return f.read()

    # Handle images
    if ext in [".png", ".jpg", ".jpeg"]:
        return extract_image_or_raise(path)

    if ext in [".mp3", ".wav", ".m4a", ".mp4", ".aac"]:
        try:
            return transcription_service.transcribe(path)
        except Exception:
            return "[Failed to transcribe audio]"

    return "[Unsupported format]"


def extract_image_or_raise(path):
    try:
        result = reader.readtext(path, detail=0)
        if result:
            return "\n".join(result)
    except Exception:
        pass
    return "[Failed to extract text]"
