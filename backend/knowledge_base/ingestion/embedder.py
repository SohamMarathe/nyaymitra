"""
Embeds chunks and writes one FAISS index + one metadata JSON file per
domain. Run via run_ingestion.py — you should never need to call this
module directly.
"""
import json
import logging
import faiss
import numpy as np

from backend.config import settings
from backend.agents.llm_client import embed_batch

from backend.knowledge_base.ingestion.checkpoint import EmbeddingCheckpoint
logger = logging.getLogger("nyayamitra.ingestion")


def embed_and_store(chunks: list[dict], domain: str) -> None:
    if not chunks:
        logger.warning("No chunks to embed for domain '%s' — skipping.", domain)
        return

    texts = [c["text"] for c in chunks]
    logger.info("Embedding %d chunks for domain '%s'...", len(texts), domain)
    checkpoint = EmbeddingCheckpoint(
    settings.INDEX_DIR,
    domain,
    )

    vectors = embed_batch(
    texts,
    task_type="RETRIEVAL_DOCUMENT",
    checkpoint=checkpoint,
    )

    matrix = np.array(vectors, dtype="float32")
    index = faiss.IndexFlatL2(matrix.shape[1])
    index.add(matrix)

    settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index_path = settings.INDEX_DIR / f"{domain}.index"
    meta_path = settings.INDEX_DIR / f"{domain}_metadata.json"

    faiss.write_index(index, str(index_path))
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    checkpoint.clear()

    logger.info("Wrote %s (%d vectors, dim=%d) and %s",
                index_path.name, matrix.shape[0], matrix.shape[1], meta_path.name)
