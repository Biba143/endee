"""
PDF Loader — extracts raw text from uploaded PDF files.
Supports multi-page extraction with page-level metadata.
"""

import io
from typing import List, Dict, Any

try:
    import PyPDF2
except ImportError:
    raise ImportError("PyPDF2 is required. Run: pip install PyPDF2")


def load_pdf(file_source) -> List[Dict[str, Any]]:
    """
    Extract text from a PDF file.

    Args:
        file_source: A file path (str) or a file-like object (e.g. BytesIO from Streamlit).

    Returns:
        A list of dicts, one per page:
            {
                "page": int,          # 1-indexed page number
                "text": str,          # extracted text
                "char_count": int     # character count
            }
    """
    pages: List[Dict[str, Any]] = []

    if isinstance(file_source, (str, bytes)):
        if isinstance(file_source, str):
            with open(file_source, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = _extract_pages(reader)
        else:
            reader = PyPDF2.PdfReader(io.BytesIO(file_source))
            pages = _extract_pages(reader)
    else:
        # File-like object (Streamlit UploadedFile, BytesIO, etc.)
        reader = PyPDF2.PdfReader(file_source)
        pages = _extract_pages(reader)

    return pages


def _extract_pages(reader: "PyPDF2.PdfReader") -> List[Dict[str, Any]]:
    """Internal helper: iterate pages and extract text."""
    pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        # Normalise whitespace
        text = " ".join(text.split())

        pages.append({
            "page": page_num,
            "text": text,
            "char_count": len(text),
        })

    return pages


def load_text_file(file_source) -> List[Dict[str, Any]]:
    """
    Load a plain-text file as a single 'page'.

    Args:
        file_source: A file path (str) or file-like object.

    Returns:
        List with one dict matching the same schema as load_pdf().
    """
    if isinstance(file_source, str):
        with open(file_source, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        raw = file_source.read()
        if isinstance(raw, bytes):
            text = raw.decode("utf-8", errors="replace")
        else:
            text = raw

    text = " ".join(text.split())
    return [{"page": 1, "text": text, "char_count": len(text)}]
