"""
Run this after you've manually downloaded documents into
knowledge_base_raw/<domain>/{acts,procedures,judgments,faqs}/
(see knowledge_base_raw/README.md for exact sources and filenames).

Usage:
    python -m backend.knowledge_base.ingestion.run_ingestion             # all domains
    python -m backend.knowledge_base.ingestion.run_ingestion --domain consumer  # one domain

This is a one-time (or occasional, when you add documents) offline job —
it is NOT called during a normal user query.
"""
import argparse
import logging

from backend.config import settings
from backend.knowledge_base.ingestion.loader import load_document, find_documents
from backend.knowledge_base.ingestion.chunker import chunk_document
from backend.knowledge_base.ingestion.embedder import embed_and_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("nyayamitra.ingestion")


def ingest_domain(domain: str) -> None:
    domain_dir = settings.RAW_KB_DIR / domain
    if not domain_dir.exists():
        logger.error("No folder found at %s — skipping.", domain_dir)
        return

    documents = find_documents(domain_dir)
    if not documents:
        logger.warning("No documents found in %s. Add PDFs/txt files first "
                        "(see knowledge_base_raw/README.md).", domain_dir)
        return

    all_chunks = []
    for doc in documents:
        try:
            text = load_document(doc["path"])
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load %s: %s", doc["path"], exc)
            continue

        chunks = chunk_document(text, doc["path"], domain, doc["chunk_type"])
        logger.info("  %s -> %d chunks", doc["path"].name, len(chunks))
        all_chunks.extend(chunks)

    logger.info("Domain '%s': %d total chunks from %d documents", domain, len(all_chunks), len(documents))
    embed_and_store(all_chunks, domain)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=settings.VALID_DOMAINS, default=None,
                         help="Ingest a single domain. Omit to ingest every domain that has files.")
    args = parser.parse_args()

    domains = [args.domain] if args.domain else settings.VALID_DOMAINS
    for domain in domains:
        logger.info("=== Ingesting domain: %s ===", domain)
        ingest_domain(domain)


if __name__ == "__main__":
    main()
