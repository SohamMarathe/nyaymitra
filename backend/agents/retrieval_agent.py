"""
Retrieval Agent — the RAG step. Deliberately dumb: it does not reason about
the law, it just finds the most relevant chunks from ONE domain collection
and hands them to the Reasoning & Validation Agent. See
backend/knowledge_base/retrieval/retriever.py for the actual FAISS search.
"""
from backend.config import settings
from backend.graph.state import NyayaMitraState
from backend.knowledge_base.retrieval.retriever import search_domain


def run_retrieval_agent(state: NyayaMitraState) -> NyayaMitraState:
    domain = state.get("legal_domain")
    if not domain:
        state["retrieved_chunks"] = []
        return state

    query = state["current_query"]
    chunks = search_domain(domain=domain, query=query, top_k=settings.TOP_K_CHUNKS)
    state["retrieved_chunks"] = chunks
    return state
