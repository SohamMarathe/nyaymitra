"""
Follow-up Validator

This node decides whether the user's latest message is:

1. An answer to the assistant's previous follow-up question.
2. A completely new legal query.

It does NOT perform legal reasoning.
It only decides conversation flow.
"""

from pydantic import BaseModel

from backend.config import settings
from backend.graph.state import NyayaMitraState
from backend.agents.llm_client import call_llm_json
import logging

_SYSTEM_INSTRUCTION = """
You are a conversation validator.

The assistant previously asked the user a follow-up question.

Your ONLY task is to determine whether the user's latest message is intended
to answer that previous follow-up question.

Rules:

- Return continue_followup=true if the user is answering the assistant's last question.

- Return continue_followup=false if the user starts a completely different
legal question or changes the topic.

Do NOT classify based on legal domain.

Only determine whether the user's latest message answers the assistant's
previous question.
"""
logger = logging.getLogger("nyayamitra.followup_validator")

class FollowupDecision(BaseModel):
    continue_followup: bool
    reason: str


def run_followup_validator(state: NyayaMitraState) -> NyayaMitraState:

    last_assistant_message = state.get("last_followup_question", "")

    try:
        result = call_llm_json(
            prompt=(
                f"Assistant's previous message:\n"
                f"{last_assistant_message}\n\n"
                f"User's latest message:\n"
                f"{state['current_query']}"
            ),
            system_instruction=_SYSTEM_INSTRUCTION,
            schema=FollowupDecision,
            model=settings.MODEL_FAST,
        )

        state["continue_followup"] = result.continue_followup

        logger.info("Follow-up validator result: %s", result.model_dump())

    except Exception:
        logger.exception("Follow-up validator failed. Falling back to a new conversation.")
        state["continue_followup"] = False

    return state