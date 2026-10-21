"""
Run this BEFORE you trust the agent pipeline with real queries.

A well-designed multi-agent system built on a badly-indexed knowledge base
still produces confidently wrong answers — so verify retrieval quality in
isolation first, with plain print statements you can read and judge
yourself, no LLM reasoning involved yet.

Usage:
    python -m backend.scripts.test_retrieval consumer "how do I file a complaint about a defective product"
    python -m backend.scripts.test_retrieval labour "employer not paying salary"

Read each result and ask: does this chunk actually answer (or meaningfully
relate to) the query? If the top results are irrelevant, the problem is
almost always chunking or missing documents — fix the knowledge base
before writing a single agent.
"""
import sys
from backend.knowledge_base.retrieval.retriever import search_domain


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    domain = sys.argv[1]
    query = " ".join(sys.argv[2:])

    print(f"\nDomain: {domain}")
    print(f"Query:  {query}\n{'-' * 60}")

    results = search_domain(domain=domain, query=query, top_k=5)
    if not results:
        print("No results. Either the domain has no index yet (run ingestion "
              "first) or the domain name is wrong.")
        return

    for i, chunk in enumerate(results, 1):
        print(f"\n[{i}] distance={chunk['distance']:.4f}  "
              f"{chunk['source']} — {chunk['section']} ({chunk['year']}, {chunk['chunk_type']})")
        preview = chunk["text"][:280].replace("\n", " ")
        print(f"    {preview}{'...' if len(chunk['text']) > 280 else ''}")

    print(f"\n{'-' * 60}\nLower distance = more similar. If the top 2-3 results "
          f"aren't relevant, revisit your chunking or add more source documents "
          f"for this domain before moving on.")


if __name__ == "__main__":
    main()
