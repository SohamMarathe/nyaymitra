"""
Loads per-domain FAISS indexes (built by ingestion/run_ingestion.py) and
searches the ONE relevant collection for a query — never the whole
knowledge base at once. Indexes are cached in memory after first load since
FAISS load + a full reload per request would be wasteful.
"""
import json
import logging
import faiss

from backend.config import settings
from backend.agents.llm_client import embed_text
from backend.graph.state import RetrievedChunk

logger = logging.getLogger("nyayamitra.retrieval")

_index_cache: dict[str, faiss.Index] = {}
_metadata_cache: dict[str, list[dict]] = {}


def _load_domain(domain: str) -> tuple[faiss.Index | None, list[dict]]:
    if domain in _index_cache:
        return _index_cache[domain], _metadata_cache[domain]

    index_path = settings.INDEX_DIR / f"{domain}.index"
    meta_path = settings.INDEX_DIR / f"{domain}_metadata.json"

    if not index_path.exists() or not meta_path.exists():
        logger.warning("No index found for domain '%s'. Run ingestion first: "
                        "python -m backend.knowledge_base.ingestion.run_ingestion --domain %s",
                        domain, domain)
        return None, []

    index = faiss.read_index(str(index_path))
    with open(meta_path, encoding="utf-8") as f:
        metadata = json.load(f)

    _index_cache[domain] = index
    _metadata_cache[domain] = metadata
    return index, metadata


def search_domain(domain: str, query: str, top_k: int = 6) -> list[RetrievedChunk]:
    index, metadata = _load_domain(domain)
    if index is None or index.ntotal == 0:
        return []

    query_vector = embed_text(query, task_type="RETRIEVAL_QUERY")
    import numpy as np
    query_matrix = np.array([query_vector], dtype="float32")

    k = min(top_k, index.ntotal)
    distances, indices = index.search(query_matrix, k)
    print("\n========== RETRIEVAL ==========")
    print("Query:", query)
    print("Domain:", domain)
    print("==============================")

    results: list[RetrievedChunk] = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        # Skip weak matches.
        # Lower L2 distance = better semantic similarity.
        if dist > settings.RETRIEVAL_DISTANCE_THRESHOLD:
            continue
        chunk = metadata[idx]
        print(f"\nDistance : {dist:.4f}")
        print(f"Source   : {chunk['source']}")
        print(f"Section  : {chunk['section']}")
        print(f"Type     : {chunk['chunk_type']}")
        print(f"Year     : {chunk['year']}")
        print("----------------------------")
        results.append(RetrievedChunk(
            text=chunk["text"],
            source=chunk["source"],
            section=chunk["section"],
            domain=chunk["domain"],
            chunk_type=chunk["chunk_type"],
            year=chunk["year"],
            distance=float(dist),
        ))
    return results


def clear_cache() -> None:
    """Call after re-running ingestion so the API picks up the new index
    without a server restart."""
    _index_cache.clear()
    _metadata_cache.clear()
