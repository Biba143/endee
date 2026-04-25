"""
Chunker — splits extracted page text into overlapping token-aware chunks.

Target chunk size: 300–500 tokens (approximated as words, since we avoid
a heavy tokeniser dependency here; sentence-transformers handles real
tokenisation internally).
"""

from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_CHUNK_SIZE = 400   # target words per chunk
DEFAULT_OVERLAP    = 50    # words of overlap between consecutive chunks
MIN_CHUNK_WORDS    = 30    # discard chunks shorter than this


def chunk_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Convert a list of page dicts (from pdf_loader) into a flat list of chunks.

    Each chunk dict contains:
        {
            "chunk_id":   str,   # "<doc_name>_p<page>_c<chunk_index>"
            "text":       str,   # chunk text
            "page":       int,   # source page number
            "chunk_index": int,  # 0-based index within the page
            "word_count": int,
        }

    Args:
        pages:      Output of pdf_loader.load_pdf() or load_text_file().
        chunk_size: Target number of words per chunk.
        overlap:    Number of words to repeat at the start of the next chunk.

    Returns:
        List of chunk dicts.
    """
    chunks: List[Dict[str, Any]] = []

    for page_dict in pages:
        page_num = page_dict["page"]
        text     = page_dict["text"].strip()

        if not text:
            continue

        page_chunks = _split_text(text, chunk_size, overlap)

        for idx, chunk_text in enumerate(page_chunks):
            word_count = len(chunk_text.split())
            if word_count < MIN_CHUNK_WORDS:
                continue

            chunks.append({
                "chunk_id":    f"p{page_num}_c{idx}",
                "text":        chunk_text,
                "page":        page_num,
                "chunk_index": idx,
                "word_count":  word_count,
            })

    return chunks


def _split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Slide a window of `chunk_size` words over `text` with `overlap` words
    of context carried forward.
    """
    words = text.split()
    if not words:
        return []

    result: List[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        result.append(chunk)

        if end == len(words):
            break

        start += chunk_size - overlap  # slide forward

    return result


def chunk_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Convenience wrapper: accepts a list of document dicts, each with a
    'pages' key (output of pdf_loader) and an optional 'doc_name' key.

    Returns a flat list of chunks with an added 'doc_name' field.
    """
    all_chunks: List[Dict[str, Any]] = []

    for doc in documents:
        doc_name = doc.get("doc_name", "unknown")
        pages    = doc.get("pages", [])

        doc_chunks = chunk_pages(pages, chunk_size, overlap)

        for chunk in doc_chunks:
            chunk["doc_name"] = doc_name
            chunk["chunk_id"] = f"{doc_name}_{chunk['chunk_id']}"

        all_chunks.extend(doc_chunks)

    return all_chunks
