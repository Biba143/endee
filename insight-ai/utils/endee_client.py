"""
Endee Client — Python wrapper around Endee's HTTP API.

Endee is the ONLY vector store used in InsightAI.
This module handles:
  - Index creation / deletion / listing
  - Vector upsert (single and batch)
  - Similarity search (top-k retrieval)
  - Health checks

Endee API base: http://localhost:8080/api/v1
Auth: optional Bearer token via NDD_AUTH_TOKEN env var.
Response format for search: MessagePack (decoded here transparently).
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

import requests
import msgpack

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_HOST       = "http://localhost:8080"
DEFAULT_INDEX_NAME = "insightai_docs"
EMBEDDING_DIM      = 384          # all-MiniLM-L6-v2
SPACE_TYPE         = "cosine"
HNSW_M             = 16
HNSW_EF_CON        = 200
PRECISION          = "float32"    # full precision for best recall


class EndeeClient:
    """
    Thin, production-ready client for the Endee vector database.

    Usage:
        client = EndeeClient()
        client.ensure_index()
        client.upsert(vectors)
        results = client.search(query_vector, k=5)
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        auth_token: Optional[str] = None,
        index_name: str = DEFAULT_INDEX_NAME,
        dim: int = EMBEDDING_DIM,
    ):
        self.host        = host.rstrip("/")
        self.index_name  = index_name
        self.dim         = dim
        self.auth_token  = auth_token or os.getenv("NDD_AUTH_TOKEN", "")
        self.session     = requests.Session()

        if self.auth_token:
            self.session.headers.update({"Authorization": self.auth_token})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.host}/api/v1{path}"

    def _raise_for_status(self, resp: requests.Response, context: str = "") -> None:
        if not resp.ok:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(
                f"Endee API error [{resp.status_code}] {context}: {detail}"
            )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> Dict[str, Any]:
        """Ping the Endee health endpoint. Raises on failure."""
        resp = self.session.get(self._url("/health"), timeout=5)
        self._raise_for_status(resp, "health")
        return resp.json()

    def is_healthy(self) -> bool:
        """Return True if Endee is reachable and healthy."""
        try:
            self.health()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def create_index(
        self,
        index_name: Optional[str] = None,
        dim: Optional[int] = None,
        space_type: str = SPACE_TYPE,
        m: int = HNSW_M,
        ef_con: int = HNSW_EF_CON,
        precision: str = PRECISION,
    ) -> bool:
        """
        Create an HNSW index in Endee.

        Returns True if created, False if it already exists.
        Raises RuntimeError on unexpected errors.
        """
        name = index_name or self.index_name
        d    = dim or self.dim

        payload = {
            "index_name": name,
            "dim":        d,
            "space_type": space_type,
            "M":          m,
            "ef_con":     ef_con,
            "precision":  precision,
        }

        resp = self.session.post(
            self._url("/index/create"),
            json=payload,
            timeout=30,
        )

        if resp.status_code == 409:
            logger.info("Index '%s' already exists — skipping creation.", name)
            return False

        self._raise_for_status(resp, f"create_index({name})")
        logger.info("Index '%s' created (dim=%d, space=%s).", name, d, space_type)
        return True

    def ensure_index(self) -> None:
        """Create the default index if it does not already exist."""
        self.create_index()

    def list_indexes(self) -> List[Dict[str, Any]]:
        """Return metadata for all indexes owned by the current user."""
        resp = self.session.get(self._url("/index/list"), timeout=10)
        self._raise_for_status(resp, "list_indexes")
        return resp.json().get("indexes", [])

    def delete_index(self, index_name: Optional[str] = None) -> bool:
        """Delete an index. Returns True on success."""
        name = index_name or self.index_name
        resp = self.session.delete(self._url(f"/index/{name}/delete"), timeout=30)
        if resp.status_code == 404:
            return False
        self._raise_for_status(resp, f"delete_index({name})")
        return True

    # ------------------------------------------------------------------
    # Vector upsert
    # ------------------------------------------------------------------

    def upsert(
        self,
        vectors: List[Dict[str, Any]],
        index_name: Optional[str] = None,
        batch_size: int = 128,
    ) -> int:
        """
        Insert (or overwrite) vectors into Endee.

        Each item in `vectors` must have:
            {
                "id":        str,           # unique document/chunk ID
                "vector":    List[float],   # dense embedding
                "meta":      str,           # serialised metadata (JSON string)
                "filter":    str,           # JSON string for filter fields
            }

        Returns the total number of vectors inserted.
        """
        name  = index_name or self.index_name
        total = 0

        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]

            resp = self.session.post(
                self._url(f"/index/{name}/vector/insert"),
                json=batch,
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
            self._raise_for_status(resp, f"upsert batch {i//batch_size}")
            total += len(batch)
            logger.debug("Upserted batch %d (%d vectors).", i // batch_size, len(batch))

        logger.info("Upserted %d vectors into index '%s'.", total, name)
        return total

    def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        doc_name: str = "unknown",
        index_name: Optional[str] = None,
    ) -> int:
        """
        High-level helper: convert InsightAI chunk dicts (with 'embedding' key)
        into Endee vector objects and upsert them.

        Each chunk must have: chunk_id, text, page, embedding, doc_name (optional).
        """
        vectors = []
        for chunk in chunks:
            # Build a rich metadata JSON string stored in 'meta'
            meta = json.dumps({
                "text":        chunk["text"],
                "page":        chunk.get("page", 1),
                "chunk_index": chunk.get("chunk_index", 0),
                "doc_name":    chunk.get("doc_name", doc_name),
                "word_count":  chunk.get("word_count", 0),
            })

            # Build filter fields for metadata-aware retrieval
            filter_data = json.dumps({
                "doc_name": chunk.get("doc_name", doc_name),
                "page":     chunk.get("page", 1),
            })

            vectors.append({
                "id":     chunk["chunk_id"],
                "vector": chunk["embedding"],
                "meta":   meta,
                "filter": filter_data,
            })

        return self.upsert(vectors, index_name=index_name)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query_vector: List[float],
        k: int = 5,
        index_name: Optional[str] = None,
        ef: int = 100,
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform a top-k similarity search against Endee.

        Args:
            query_vector: Dense query embedding (list of floats).
            k:            Number of results to return.
            index_name:   Override the default index.
            ef:           HNSW ef_search parameter (higher = better recall, slower).
            filter_expr:  Optional JSON filter string, e.g.
                          '[{"doc_name": {"$eq": "report.pdf"}}]'

        Returns:
            List of result dicts:
                {
                    "id":    str,
                    "score": float,
                    "meta":  dict,   # parsed from the stored JSON meta string
                }
        """
        name = index_name or self.index_name

        payload: Dict[str, Any] = {
            "vector": query_vector,
            "k":      k,
            "ef":     ef,
        }
        if filter_expr:
            payload["filter"] = filter_expr

        resp = self.session.post(
            self._url(f"/index/{name}/search"),
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        self._raise_for_status(resp, f"search(k={k})")

        # Endee returns MessagePack for search responses
        raw = msgpack.unpackb(resp.content, raw=False)
        return self._parse_search_response(raw)

    def _parse_search_response(self, raw: Any) -> List[Dict[str, Any]]:
        """
        Parse the MessagePack-decoded search response from Endee.

        Endee returns a ResultSet which msgpack decodes as a list of
        [id, score, vector_bytes, meta_bytes, filter_str] tuples,
        or as a dict/list depending on the msgpack schema version.
        We handle both gracefully.
        """
        results = []

        # Endee packs results as a list of items
        items = raw if isinstance(raw, list) else raw.get("results", [])

        for item in items:
            try:
                if isinstance(item, (list, tuple)):
                    # Actual Endee layout: [rank, id, meta, filter, score, vector]
                    vec_id   = str(item[1]) if len(item) > 1 else ""
                    meta_raw = item[2] if len(item) > 2 else b""
                    score    = float(item[4]) if len(item) > 4 else 0.0
                elif isinstance(item, dict):
                    vec_id   = str(item.get("id", ""))
                    score    = float(item.get("score", 0.0))
                    meta_raw = item.get("meta", b"")
                else:
                    continue

                # Decode meta (stored as JSON string in bytes)
                if isinstance(meta_raw, (bytes, bytearray)):
                    meta_str = meta_raw.decode("utf-8", errors="replace")
                else:
                    meta_str = str(meta_raw)

                try:
                    meta = json.loads(meta_str) if meta_str else {}
                except json.JSONDecodeError:
                    meta = {"raw": meta_str}

                results.append({
                    "id":    vec_id,
                    "score": 1.0 - score,  # convert cosine distance → similarity
                    "meta":  meta,
                })

            except Exception as e:
                logger.warning("Failed to parse search result item: %s", e)
                continue

        return results
