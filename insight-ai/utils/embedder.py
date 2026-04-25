"""
Embedder — generates dense vector embeddings using sentence-transformers.

Model: all-MiniLM-L6-v2
  - 384-dimensional output
  - Fast, lightweight, strong semantic quality
  - Runs entirely locally (no API key required)
"""

from typing import List, Union
import numpy as np

_model = None  # lazy-loaded singleton


def _get_model():
    """Lazy-load the sentence-transformer model (downloaded once, cached)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. Run: pip install sentence-transformers"
            )
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

EMBEDDING_DIM = 384  # dimension of all-MiniLM-L6-v2


def embed_texts(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """
    Embed a list of strings.

    Args:
        texts:      List of text strings to embed.
        batch_size: Number of texts to encode per forward pass.

    Returns:
        List of embedding vectors (each a list of 384 floats).
    """
    if not texts:
        return []

    model = _get_model()
    embeddings: np.ndarray = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,   # cosine similarity works best with L2-normalised vectors
        convert_to_numpy=True,
    )
    return embeddings.tolist()


def embed_single(text: str) -> List[float]:
    """
    Embed a single string.

    Args:
        text: The string to embed.

    Returns:
        A list of 384 floats.
    """
    return embed_texts([text])[0]


def embed_chunks(chunks: List[dict]) -> List[dict]:
    """
    Add an 'embedding' key to each chunk dict in-place.

    Args:
        chunks: List of chunk dicts (from chunker.py).  Each must have a 'text' key.

    Returns:
        The same list with 'embedding' populated.
    """
    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)

    for chunk, vec in zip(chunks, vectors):
        chunk["embedding"] = vec

    return chunks
