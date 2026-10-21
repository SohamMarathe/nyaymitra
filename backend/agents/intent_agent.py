"""
Intent Agent — understands what the user is actually asking.

Also doubles as the "resume a follow-up conversation" handler: if the
previous turn was awaiting an answer to a clarifying question, this agent
merges the new message into collected_context first, then re-decides
whether enough information now exists to move to retrieval.
"""
from typing import List
from pydantic import BaseModel, Field

from backend.config import settings
from backend.graph.state import NyayaMitraState
from backend.agents.llm_client import call_llm_json

_SYSTEM_INSTRUCTION = """You are the Intent Agent for NyayaMitra, an Indian legal \
information assistant. Given a user's message (and any context already collected \
from earlier in the conversation), determine:

The conversation may already be in progress.

The user's latest message may simply be an answer to a previous follow-up question such as "yes", "2 months", "private company", or "Mumbai".

Always interpret the latest message together with the previous conversation and any structured facts already collected.

Never treat a short follow-up reply as a completely new legal query.

- legal_domain: exactly one of consumer, labour, cyber, property, family, criminal
- user_intent: exactly one of know_rights, understand_procedure, general_info, applicable_laws
- jurisdiction: an Indian state name if the user mentioned one or it's clearly \
implied, otherwise null
- needs_followup: true only if the question CANNOT be meaningfully answered without \
more specific facts (e.g. "my employer hasn't paid my salary" needs: how long unpaid, \
what kind of employment). A general question like "what are my rights if my salary is \
delayed" does NOT need follow-up — it can be answered generally.
- missing_info: if needs_followup is true, a short list (max 3) of the SPECIFIC facts \
still needed — not vague categories. Ask for what changes the legal answer, not \
everything you could possibly know.

Never assume facts the user hasn't stated. If uncertain about the domain, pick the \
closest match rather than leaving it null."""


class IntentResult(BaseModel):
    legal_domain: str
    user_intent: str
    jurisdiction: str | None = None
    needs_followup: bool
    missing_info: List[str] = Field(default_factory=list)


def _build_context_summary(state: NyayaMitraState) -> str:
    parts = []

    if state.get("messages"):
        parts.append("Recent conversation:")

        for msg in state["messages"][-6:]:
            role = msg["role"].capitalize()
            parts.append(f"{role}: {msg['content']}")

    parts.append(f"\nCurrent user message:\n{state['current_query']}")

    if state.get("collected_context"):
        parts.append(
            f"\nStructured facts collected so far:\n{state['collected_context']}"
        )

    if state.get("legal_domain"):
        parts.append(
            f"\nPreviously identified legal domain:\n{state['legal_domain']}"
        )

    return "\n".join(parts)


def run_intent_agent(state: NyayaMitraState) -> NyayaMitraState:
    result = call_llm_json(
        prompt=_build_context_summary(state),
        system_instruction=_SYSTEM_INSTRUCTION,
        schema=IntentResult,
        model=settings.MODEL_FAST,
    )

    state["legal_domain"] = result.legal_domain if result.legal_domain in settings.VALID_DOMAINS else None
    state["user_intent"] = result.user_intent
    state["jurisdiction"] = result.jurisdiction or state.get("jurisdiction")
    state["needs_followup"] = result.needs_followup
    state["missing_info"] = result.missing_info
    return state


def route_after_intent(state: NyayaMitraState) -> str:
    if not state.get("legal_domain"):
        # Couldn't confidently classify a domain at all — safer to ask a
        # clarifying question than to guess and retrieve from the wrong collection.
        return "followup_agent"
    if state["needs_followup"] and state.get("followup_round", 0) < 2:
        # Cap follow-up rounds at 2 — after that, answer with what we have
        # rather than interrogating the user indefinitely.
        return "followup_agent"
    return "retrieval_agent"
