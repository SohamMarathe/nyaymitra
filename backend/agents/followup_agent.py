"""
Follow-up Agent — asks only for the specific missing facts, in the user's
own language, in one friendly message. Ends the graph run for this turn
(the answer has to come from the user in their next message).
"""
from pydantic import BaseModel
from backend.config import settings
from backend.graph.state import NyayaMitraState
from backend.agents.llm_client import call_llm, call_llm_json

_SYSTEM_INSTRUCTION = """You are the Follow-up Agent for NyayaMitra, an Indian legal \
information assistant. You've been given a list of specific missing facts. Turn them \
into ONE short, warm, plain-language message asking for exactly that information — \
nothing more. Do not ask questions the user has already answered. Do not lecture or \
add legal information yet; that comes after you have the facts. Write in {language}. \
Keep it to 2-4 short, natural questions.

Ask only for the minimum information genuinely required to answer the user's legal question.

Do not ask for information that is merely helpful or interesting.

Avoid asking about company size, salary amount, income, employment type, location, or similar details unless they directly change the applicable law or legal procedure."""


def run_followup_agent(state: NyayaMitraState) -> NyayaMitraState:
    missing = state.get("missing_info") or ["what state you're in", "roughly when this happened"]
    lang_name = settings.SUPPORTED_LANGUAGES.get(state.get("detected_language", "en"), "English")

    question_text = call_llm(
        prompt=(
            f"User's original message: {state['current_query']}\n"
            f"Domain identified: {state.get('legal_domain', 'unclear')}\n"
            f"Missing information to ask about: {missing}"
        ),
        system_instruction=_SYSTEM_INSTRUCTION.format(language=lang_name),
        model=settings.MODEL_FAST,
        temperature=0.4,
    )

    state["final_response"] = question_text.strip()
    state["last_followup_question"] = question_text.strip()
    state["awaiting_user_reply"] = True
    state["followup_round"] = state.get("followup_round", 0) + 1
    return state


_MERGE_SYSTEM_INSTRUCTION = """You extract structured facts from a user's reply to a \
follow-up question in a legal-information conversation. Merge the new facts into the \
existing known facts. Keep keys short and snake_case (e.g. "employment_type", \
"months_unpaid", "state"). Do not invent facts that weren't stated."""


class ExtractedFacts(BaseModel):
    facts: dict[str, str]


def run_merge_followup_answer(state: NyayaMitraState) -> NyayaMitraState:
    """Called when awaiting_user_reply was True at the start of this turn —
    the current_query is the user's answer to our last follow-up question."""
    existing = state.get("collected_context", {})
    result = call_llm_json(
        prompt=(
            f"Existing known facts: {existing}\n"
            f"User's new reply: {state['current_query']}"
        ),
        system_instruction=_MERGE_SYSTEM_INSTRUCTION,
        schema=ExtractedFacts,
        model=settings.MODEL_FAST,
    )
    merged = {**existing, **result.facts}
    state["collected_context"] = merged
    state["awaiting_user_reply"] = False
    state["last_followup_question"] = ""
    state["needs_followup"] = False
    state["missing_info"] = []
    state["continue_followup"] = True
    # Fold the collected facts into current_query so the Intent Agent (which
    # runs next) sees the full picture, not just the last short reply.
    state["current_query"] = f"""
                            Original legal question:
                            {state["original_query"]}

                            Additional information provided by the user:
                            {merged}
                            """.strip()
    print("\n========== CURRENT QUERY AFTER MERGE ==========")
    print(state["current_query"])
    print("==============================================\n")
    return state
