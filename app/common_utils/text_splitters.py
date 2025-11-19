import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    Args:
        text: full text
        chunk_size: number of characters per chunk
        overlap: number of characters to overlap between chunks
    Returns:
        List of text chunks
    """
    # chunks = []
    # start = 0
    # text_length = len(text)

    # while start < text_length:
    #     end = min(start + chunk_size, text_length)
    #     chunk = text[start:end]
    #     chunks.append(chunk)
    #     start += chunk_size - overlap  # move start forward
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(text)
    return chunks