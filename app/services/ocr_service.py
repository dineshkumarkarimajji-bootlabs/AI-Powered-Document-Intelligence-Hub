import os
from .extractors.extractor_factory import ExtractorFactory


def extract_text(file_path: str) -> str:
    """
    Unified text extractor for PDF, DOCX, TXT, Images, Audio.
    Uses ExtractorFactory to pick the correct extractor.
    """
    
    ext = os.path.splitext(file_path)[1].lower()

    
    extractor = ExtractorFactory.get_extractor(file_path)

    if extractor is None:
        raise ValueError(f"No extractor found for file type: {ext}")

    return extractor.extract(file_path)
