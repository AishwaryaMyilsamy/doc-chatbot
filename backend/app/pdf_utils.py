from typing import List
from pypdf import PdfReader

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_path (str): Path to the PDF file

    Returns:
        str: Full extracted text
    """
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text (str): Full text to split
        chunk_size (int): Max number of characters per chunk
        overlap (int): Number of characters to overlap between chunks

    Returns:
        List[str]: List of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap  # overlap
    return chunks
