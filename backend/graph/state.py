"""
The State object is the single source of truth that flows through the
entire LangGraph pipeline. Every agent reads from it and writes back to it.

Design note: we deliberately do NOT use LangGraph's built-in checkpointer
(langgraph-checkpoint-postgres) for persistence. That's one more moving part
with its own schema and async setup. Instead we persist the handful of
fields that need to survive between turns (see PERSISTED_FIELDS below)
ourselves, in plain PostgreSQL, via backend/db/models.py. It's a few more
lines of code but every part of it is visible and debuggable — which
matters more than saving 15 lines when you're learning the system.
"""
from typing import TypedDict, List, Optional, Literal, Dict, Any


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str
    language: str


class RetrievedChunk(TypedDict):
    text: str
    source: str          # e.g. "Consumer Protection Act, 2019"
    section: str          # e.g. "Section 35"
    domain: str            # e.g. "consumer"
    chunk_type: str          # act | procedure | judgment | faq
    year: str
    distance: float          # raw FAISS L2 distance, lower = more similar


class NyayaMitraState(TypedDict, total=False):
    # ── Session ──────────────────────────────────────────────────
    session_id: str

    # ── Conversation so far (loaded from DB at the start of each turn) ──
    messages: List[Message]

    # ── This turn's input ────────────────────────────────────────
    current_query: str
    original_query: str
    detected_language: str          # ISO code: en, hi, mr, ta, te, bn, gu, kn

    # ── Turn-entry routing ──────────────────────────────────────
    # True if the PREVIOUS turn ended by asking a follow-up question and is
    # waiting on the user's answer. Loaded from the session row, not set by
    # any node — it's what tells the entry router where to send this turn.
    awaiting_user_reply: bool

    # ── Scope & Safety Gate output ──────────────────────────────
    is_in_scope: bool
    rejection_reason: Optional[str]

    # ── Intent Agent output ──────────────────────────────────────
    legal_domain: Optional[str]      # consumer|labour|cyber|property|family|criminal
    user_intent: Optional[str]       # know_rights|understand_procedure|general_info|applicable_laws
    jurisdiction: Optional[str]      # Indian state name, if mentioned/relevant
    needs_followup: bool
    missing_info: List[str]          # human-readable list of what's still missing

    # ── Follow-up tracking ────────────────────────────────────────
    followup_round: int 
    last_followup_question: str             # how many follow-up rounds have happened
    collected_context: Dict[str, Any]  # accumulated facts gathered via follow-up
    continue_followup: bool

    # ── Retrieval output ──────────────────────────────────────────
    retrieved_chunks: List[RetrievedChunk]

    # ── Reasoning & Validation output ─────────────────────────────
    legal_analysis: Optional[str]
    applicable_laws: List[str]
    confidence_level: Literal["high", "medium", "low"]
    confidence_reason: Optional[str]
    route_to_fallback: bool

    # ── Final output ────────────────────────────────────────────
    final_response: Optional[str]
    response_mode: Literal["plain", "structured"]


# Fields we persist to the `sessions` table between turns.
# Everything else is recomputed fresh each turn.
PERSISTED_FIELDS = [
    "original_query",
    "legal_domain",
    "user_intent",
    "jurisdiction",
    "awaiting_user_reply",
    "followup_round",
    "last_followup_question",
    "collected_context",
    "detected_language",
]


def new_state(session_id: str, query: str) -> NyayaMitraState:
    """Build a fresh state dict for a new turn. `persisted` values (if any)
    should be merged in by the caller (see api/routes/query.py) after this."""
    return NyayaMitraState(
        session_id=session_id,
        messages=[],
        current_query=query,
        original_query=query,
        detected_language="en",
        awaiting_user_reply=False,
        is_in_scope=True,
        rejection_reason=None,
        legal_domain=None,
        user_intent=None,
        jurisdiction=None,
        needs_followup=False,
        missing_info=[],
        followup_round=0,
        last_followup_question="",
        continue_followup=True,
        collected_context={},
        retrieved_chunks=[],
        legal_analysis=None,
        applicable_laws=[],
        confidence_level="low",
        confidence_reason=None,
        route_to_fallback=False,
        final_response=None,
        response_mode="structured",
    )