"""
InsightAI — Cross-Domain Reasoning & Strategy Engine
Main application entry point.

This module provides the core pipeline:
  1. Document ingestion (PDF → chunks → embeddings → Endee)
  2. Query processing (intent detection → retrieval → reasoning → output)

Run the Streamlit UI with:
    streamlit run ui/streamlit_app.py

Or use this module programmatically:
    from app import InsightAI
    ai = InsightAI()
    ai.ingest_document("report.pdf")
    result = ai.query("Why did I score less?")
"""

import os
import logging
from typing import List, Dict, Any, Optional

from utils.pdf_loader import load_pdf, load_text_file
from utils.chunker import chunk_pages
from utils.embedder import embed_chunks
from utils.endee_client import EndeeClient
from utils.retriever import Retriever
from utils.router import route_query
from utils.reasoning_engine import run_reasoning

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("InsightAI")


# ---------------------------------------------------------------------------
# InsightAI Core Class
# ---------------------------------------------------------------------------

class InsightAI:
    """
    Cross-Domain Reasoning & Strategy Engine.

    Wraps the full pipeline from document ingestion to structured reasoning output.
    Uses Endee as the ONLY vector database for all storage and retrieval.
    """

    def __init__(
        self,
        endee_host: str = "http://localhost:8080",
        index_name: str = "insightai_docs",
        auth_token: Optional[str] = None,
    ):
        """
        Initialise InsightAI.

        Args:
            endee_host:  URL of the running Endee server.
            index_name:  Name of the Endee index to use.
            auth_token:  Optional Endee auth token (or set NDD_AUTH_TOKEN env var).
        """
        self.index_name = index_name

        # Initialise Endee client
        self.endee = EndeeClient(
            host=endee_host,
            auth_token=auth_token or os.getenv("NDD_AUTH_TOKEN", ""),
            index_name=index_name,
        )

        # Initialise retriever
        self.retriever = Retriever(
            endee_client=self.endee,
            index_name=index_name,
        )

        logger.info("InsightAI initialised (index: %s, host: %s)", index_name, endee_host)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(self) -> bool:
        """
        Verify Endee is reachable and ensure the index exists.

        Returns:
            True if setup succeeded, False otherwise.
        """
        if not self.endee.is_healthy():
            logger.error("Endee server is not reachable at %s", self.endee.host)
            return False

        self.endee.ensure_index()
        logger.info("Setup complete — Endee index '%s' is ready.", self.index_name)
        return True

    # ------------------------------------------------------------------
    # Document ingestion
    # ------------------------------------------------------------------

    def ingest_document(
        self,
        file_source,
        doc_name: str = "document",
        file_type: str = "pdf",
        chunk_size: int = 400,
        overlap: int = 50,
    ) -> Dict[str, Any]:
        """
        Full ingestion pipeline: load → chunk → embed → store in Endee.

        Args:
            file_source: File path (str) or file-like object (e.g. Streamlit UploadedFile).
            doc_name:    Human-readable document name (used in metadata and filters).
            file_type:   "pdf" or "text".
            chunk_size:  Target words per chunk (300–500 recommended).
            overlap:     Word overlap between consecutive chunks.

        Returns:
            {
                "doc_name":     str,
                "pages":        int,
                "chunks":       int,
                "vectors_stored": int,
                "status":       "success" | "error",
                "message":      str,
            }
        """
        logger.info("Ingesting document: %s (type=%s)", doc_name, file_type)

        try:
            # Step 1: Extract text
            if file_type == "pdf":
                pages = load_pdf(file_source)
            else:
                pages = load_text_file(file_source)

            if not pages:
                return _error_result(doc_name, "No text could be extracted from the document.")

            logger.info("Extracted %d pages from '%s'.", len(pages), doc_name)

            # Step 2: Chunk
            chunks = chunk_pages(pages, chunk_size=chunk_size, overlap=overlap)
            if not chunks:
                return _error_result(doc_name, "Document produced no usable chunks after splitting.")

            # Attach doc_name to each chunk
            for chunk in chunks:
                chunk["doc_name"] = doc_name
                chunk["chunk_id"] = f"{doc_name}_{chunk['chunk_id']}"

            logger.info("Created %d chunks from '%s'.", len(chunks), doc_name)

            # Step 3: Embed
            chunks = embed_chunks(chunks)
            logger.info("Embedded %d chunks.", len(chunks))

            # Step 4: Store in Endee
            vectors_stored = self.endee.upsert_chunks(chunks, doc_name=doc_name)
            logger.info("Stored %d vectors in Endee index '%s'.", vectors_stored, self.index_name)

            return {
                "doc_name":       doc_name,
                "pages":          len(pages),
                "chunks":         len(chunks),
                "vectors_stored": vectors_stored,
                "status":         "success",
                "message":        f"Successfully ingested '{doc_name}': {len(chunks)} chunks stored.",
            }

        except Exception as e:
            logger.exception("Ingestion failed for '%s': %s", doc_name, e)
            return _error_result(doc_name, str(e))

    def ingest_multiple(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Ingest multiple documents.

        Args:
            documents: List of dicts, each with keys:
                       'file_source', 'doc_name', 'file_type' (optional).

        Returns:
            List of ingestion result dicts.
        """
        results = []
        for doc in documents:
            result = self.ingest_document(
                file_source=doc["file_source"],
                doc_name=doc.get("doc_name", "document"),
                file_type=doc.get("file_type", "pdf"),
            )
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Query processing
    # ------------------------------------------------------------------

    def query(
        self,
        question: str,
        k: int = 10,
        filter_doc: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full query pipeline: route → retrieve → reason → structured output.

        Args:
            question:   Natural language question.
            k:          Number of context chunks to retrieve from Endee.
            filter_doc: Optional document name to restrict retrieval.

        Returns:
            Structured reasoning output dict (see reasoning_engine.py).
        """
        logger.info("Processing query: '%s'", question[:100])

        # Step 1: Route (intent + domain detection + query transformation)
        route = route_query(question)
        intent   = route["intent"]
        domain   = route["domain"]
        transformed_query = route["transformed_query"]

        logger.info("Intent: %s | Domain: %s", intent, domain)

        # Step 2: Retrieve from Endee using transformed query
        chunks = self.retriever.retrieve_with_rerank(
            query=transformed_query,
            k=k * 2,       # fetch more, then rerank
            top_k=k,
            filter_doc=filter_doc,
        )

        if not chunks:
            logger.warning("No chunks retrieved for query: '%s'", question[:80])
            return _no_context_result(question, intent, domain)

        # Step 3: Update domain detection with context
        from utils.router import detect_domain
        domain = detect_domain(question, chunks)

        # Step 4: Run reasoning engine
        result = run_reasoning(
            query=question,
            chunks=chunks,
            intent=intent,
            domain=domain,
        )

        result["route"] = route
        logger.info("Reasoning complete. Returning structured output.")
        return result

    # ------------------------------------------------------------------
    # Index management helpers
    # ------------------------------------------------------------------

    def list_documents(self) -> List[str]:
        """Return a list of document names stored in the index."""
        indexes = self.endee.list_indexes()
        # We store all docs in one index; doc names are in metadata
        # Return index info as a proxy
        return [idx.get("name", "") for idx in indexes]

    def clear_index(self) -> bool:
        """Delete and recreate the index (removes all stored documents)."""
        logger.warning("Clearing Endee index '%s'.", self.index_name)
        self.endee.delete_index()
        self.endee.ensure_index()
        return True

    def get_index_stats(self) -> Dict[str, Any]:
        """Return stats about the current Endee index."""
        indexes = self.endee.list_indexes()
        for idx in indexes:
            if idx.get("name") == self.index_name:
                return idx
        return {}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _error_result(doc_name: str, message: str) -> Dict[str, Any]:
    return {
        "doc_name":       doc_name,
        "pages":          0,
        "chunks":         0,
        "vectors_stored": 0,
        "status":         "error",
        "message":        message,
    }


def _no_context_result(query: str, intent: str, domain: str) -> Dict[str, Any]:
    return {
        "query":           query,
        "intent":          intent,
        "domain":          domain,
        "analysis":        ["No relevant context found. Please upload documents first."],
        "key_issues":      ["No documents have been ingested into the system."],
        "strategy_insight": "Upload relevant documents to enable AI-powered analysis.",
        "improvement_plan": ["Upload a PDF or text document using the file uploader."],
        "sources":         [],
        "chunk_count":     0,
        "context_summary": "No context available.",
        "route":           {"intent": intent, "domain": domain},
    }


# ---------------------------------------------------------------------------
# CLI entry point (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    ai = InsightAI()

    if not ai.setup():
        print("ERROR: Could not connect to Endee. Is the server running?")
        sys.exit(1)

    print("InsightAI is ready.")
    print("Index stats:", ai.get_index_stats())
