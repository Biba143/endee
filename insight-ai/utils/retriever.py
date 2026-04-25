"""
Retriever — orchestrates Endee similarity search and context assembly.

This module:
  - Embeds the user query
  - Searches Endee for relevant chunks
  - Ranks and filters results
  - Assembles context for the reasoning engine
"""

from typing import List, Dict, Any, Optional
import logging
import json

from .embedder import embed_single
from .endee_client import EndeeClient

logger = logging.getLogger(__name__)


class Retriever:
    """
    High-level retriever that combines embedding generation with Endee search.

    Usage:
        retriever = Retriever()
        context = retriever.retrieve("Why did I score less?", k=10)
    """

    def __init__(
        self,
        endee_client: Optional[EndeeClient] = None,
        index_name: str = "insightai_docs",
    ):
        self.client = endee_client or EndeeClient(index_name=index_name)
        self.index_name = index_name

    def retrieve(
        self,
        query: str,
        k: int = 10,
        filter_doc: Optional[str] = None,
        filter_page: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k relevant chunks for a natural-language query.

        Args:
            query:        Natural language question.
            k:            Number of results to fetch.
            filter_doc:   Optional document name to restrict search.
            filter_page:  Optional page number to restrict search.

        Returns:
            List of chunk dicts (each includes 'text', 'score', 'meta', etc.).
        """
        # 1. Embed the query
        query_vector = embed_single(query)
        logger.debug("Query embedded (%d dimensions).", len(query_vector))

        # 2. Build filter expression if needed
        filter_expr = None
        if filter_doc or filter_page:
            filters = []
            if filter_doc:
                filters.append({"doc_name": {"$eq": filter_doc}})
            if filter_page:
                filters.append({"page": {"$eq": filter_page}})
            filter_expr = json.dumps(filters)

        # 3. Search Endee
        try:
            raw_results = self.client.search(
                query_vector,
                k=k,
                index_name=self.index_name,
                ef=200,  # higher recall for reasoning tasks
                filter_expr=filter_expr,
            )
        except Exception as e:
            logger.error("Endee search failed: %s", e)
            return []

        # 4. Enrich results with original text
        enriched = []
        for r in raw_results:
            meta = r.get("meta", {})
            text = meta.get("text", "")
            if not text:
                continue

            enriched.append({
                "chunk_id": r["id"],
                "text": text,
                "score": r["score"],
                "page": meta.get("page", 1),
                "doc_name": meta.get("doc_name", "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "word_count": meta.get("word_count", 0),
            })

        logger.info("Retrieved %d chunks for query: '%s'", len(enriched), query[:80])
        return enriched

    def retrieve_with_rerank(
        self,
        query: str,
        k: int = 20,
        top_k: int = 5,
        filter_doc: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve more chunks (k) then re‑rank them using a simple heuristic:
        - Prefer chunks with higher similarity scores
        - Prefer chunks from the same document (if filter_doc given)
        - Prefer longer chunks (more content)

        Returns the top_k re‑ranked chunks.
        """
        # Fetch more candidates
        candidates = self.retrieve(query, k=k, filter_doc=filter_doc)
        if not candidates:
            return []

        # Simple re‑ranking: score × log(word_count)
        for c in candidates:
            boost = 1.0 + 0.1 * (c.get("word_count", 0) / 100)  # up to +10% for length
            c["rerank_score"] = c["score"] * boost

        # Sort by rerank_score descending (higher similarity = better)
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Return top_k
        return candidates[:top_k]

    def get_context_text(self, chunks: List[Dict[str, Any]], max_words: int = 2000) -> str:
        """
        Concatenate chunk texts into a single context string, respecting a word limit.

        Args:
            chunks:     List of chunk dicts (from retrieve()).
            max_words:  Maximum total words to include.

        Returns:
            A single string with chunk texts separated by "\n---\n".
        """
        context_parts = []
        total_words = 0

        for chunk in chunks:
            text = chunk["text"]
            words = chunk.get("word_count", len(text.split()))
            if total_words + words > max_words:
                # Add partial chunk if we have room
                remaining = max_words - total_words
                if remaining > 30:  # only if we can add a meaningful fragment
                    truncated = " ".join(text.split()[:remaining])
                    context_parts.append(f"{truncated} [...]")
                break

            context_parts.append(text)
            total_words += words

        return "\n---\n".join(context_parts)



