"""
Scope & Safety Gate — runs before any other agent.

Two questions, answered together in one cheap call:
  1. Is this an Indian-legal-information question at all?
  2. Is it something we can responsibly answer (not a request for help
     committing fraud, evading law, or drafting something we shouldn't)?

Rule-based pre-filter first (free, instant, catches the obvious cases),
LLM classification second (catches the ambiguous ones). This keeps the
common case fast and cheap, and only spends a model call when needed.
"""
import re
from pydantic import BaseModel, Field

from backend.config import settings
from backend.graph.state import NyayaMitraState
from backend.agents.llm_client import call_llm_json

# Obvious non-legal chit-chat — reject without spending an API call.
_GREETING_RE = re.compile(r"^\s*(hi|hello|hey|namaste|ok|okay|thanks|thank you)\s*[.!]?\s*$", re.I)

_SYSTEM_INSTRUCTION = """You are a scope classifier for NyayaMitra, an Indian legal \
information assistant. You decide two things about a user's message:

1. is_legal_query: true only if it is a genuine question about Indian law, legal \
rights, or legal procedure (labour, consumer, cyber, property, family, criminal, or \
similar civil domains). General knowledge, coding help, other countries' law, or \
small talk are all false.

2. is_safe: false if the query asks for help committing fraud, evading a legal \
obligation, forging documents, harassing someone, or otherwise misusing legal \
knowledge to cause harm. A person asking to understand a law that also happens to \
describe a crime (e.g. "what happens if someone doesn't pay maintenance") is SAFE — \
they're asking about consequences, not asking how to get away with something.

If either is false, write a short, polite reason in the user's own language register \
(plain, one or two sentences) explaining what NyayaMitra can help with instead."""


class ScopeCheck(BaseModel):
    is_legal_query: bool
    is_safe: bool
    domain_guess: str = Field(description="best-guess domain, or 'unclear'")
    reason_if_rejected: str = Field(default="")


def run_scope_gate(state: NyayaMitraState) -> NyayaMitraState:
    query = state["current_query"].strip()

    if _GREETING_RE.match(query):
        state["is_in_scope"] = False
        state["rejection_reason"] = (
            "Hi! I'm NyayaMitra — I can help you understand Indian laws, your "
            "rights, and legal procedures. What's the situation you'd like help with?"
        )
        return state

    result = call_llm_json(
        prompt=f"User message: {query}",
        system_instruction=_SYSTEM_INSTRUCTION,
        schema=ScopeCheck,
        model=settings.MODEL_FAST,
    )

    state["is_in_scope"] = result.is_legal_query and result.is_safe
    if not state["is_in_scope"]:
        state["rejection_reason"] = result.reason_if_rejected or (
            "I can only help with questions about Indian law, rights, and legal "
            "procedures. Could you rephrase your question around a legal issue?"
        )
    return state


def route_after_scope_gate(state: NyayaMitraState) -> str:
    return "intent_agent" if state["is_in_scope"] else "rejected"
