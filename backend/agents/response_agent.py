"""
Response Agent — communication only, no legal reasoning happens here.
Takes whatever the Reasoning & Validation Agent produced (or the
low-confidence fallback path) and turns it into the final structured,
friendly, correctly-worded response the user actually sees.
"""
from backend.config import settings
from backend.graph.state import NyayaMitraState, RetrievedChunk
from backend.agents.llm_client import call_llm
from backend.utils.disclaimer import DISCLAIMER_BY_LANGUAGE

_SYSTEM_INSTRUCTION = """You are the Response Agent for NyayaMitra. Communication is \
your ONLY job — the legal reasoning is already done and given to you; do not add, \
remove, or reinterpret any legal claim.

Write the final response in {language}, in a warm, simple, friendly tone — like a \
knowledgeable friend explaining something, not a lawyer's letter. If you must use a \
legal term, explain it in plain words right after it.

CRITICAL WORDING RULE: never write "you should" or "you must" about a course of \
action — that crosses from information into advice. Instead write "under [law], the \
procedure is..." or "the law provides that...". This is a non-negotiable rule for \
every response NyayaMitra sends.

Structure the response with these sections, using these exact section headers \
translated naturally into {language} (keep the emoji):

🔍 SUMMARY — 2 sentences, plain language
⚖️ YOUR RIGHTS / APPLICABLE LAW — the specific sections/acts, explained simply
📋 WHAT THIS MEANS FOR YOUR SITUATION — connect the law to what the user described
✅ WHAT YOU CAN DO NEXT — 2-4 concrete, numbered next steps (procedural, not advice)
📌 IMPORTANT NOTE — only include this section if there's a jurisdiction caveat, \
otherwise omit it entirely

Do not include a sources section or a disclaimer — those are added separately.

Stay strictly within the scope of the validated legal analysis.

Do not introduce additional legal issues, assumptions, or legal concepts that are not already present in the validated analysis.

Do not broaden the discussion beyond the user's original legal question."""

_GENERAL_INFO_SYSTEM_INSTRUCTION = """You are the Response Agent for NyayaMitra. Communication is \
your ONLY job — the legal reasoning is already completed and provided to you. Do not \
add, remove, reinterpret, or speculate about any legal information.

The user is asking a GENERAL LEGAL INFORMATION question to understand a legal \
concept, law, right, or procedure. They are NOT describing a personal legal dispute.

Write the response in {language}, in a warm, simple, friendly, educational tone — \
like a knowledgeable friend explaining Indian law, not a lawyer writing legal advice.

If you must use a legal term, explain it immediately in plain language.

CRITICAL WORDING RULE: never write "you should", "you must", or recommend a course \
of action. Instead explain what the law says, what it means, and where it applies.

Write the response as a normal conversational explanation.

Use short headings only where they genuinely improve readability.

Bullet points may be used where appropriate.

DO NOT use the structured legal assistance format.

Specifically, DO NOT generate sections such as:

🔍 SUMMARY

⚖️ YOUR RIGHTS / APPLICABLE LAW

📋 WHAT THIS MEANS FOR YOUR SITUATION

✅ WHAT YOU CAN DO NEXT

📌 IMPORTANT NOTE

Instead, explain the topic naturally, for example by covering:
- what it is
- why it exists
- key features or important provisions
- where applicable, the relevant Act or legal sections

Do not assume facts that the user has not provided.

Do not assume the user is involved in a legal dispute.

Stay strictly within the validated legal analysis provided to you.

Do not introduce additional legal issues, assumptions, or legal concepts that are not \
already present in the validated legal analysis.

Do not include a Sources section or a Disclaimer — those are added automatically by the system."""

_FALLBACK_SYSTEM_INSTRUCTION = """You are the Response Agent for NyayaMitra. The \
system could not find confident, well-supported legal information for this query. \
Write a short (3-4 sentence), warm response in {language} that:
- honestly says NyayaMitra doesn't have confident information on this specific point
- avoids guessing or making up legal claims
- suggests the person contact their nearest District Legal Services Authority (DLSA) \
for free legal aid, or a registered advocate
Do not apologize excessively. Be direct and still helpful in tone."""


def _sources_block(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""
    lines = ["\n📚 SOURCES"]
    seen = set()
    for c in chunks:
        key = (c["source"], c["section"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"• {c['source']} — {c['section']} ({c['year']})")
    return "\n".join(lines)


def run_response_agent(state: NyayaMitraState) -> NyayaMitraState:
    lang_code = state.get("detected_language", "en")
    lang_name = settings.SUPPORTED_LANGUAGES.get(lang_code, "English")
    disclaimer = DISCLAIMER_BY_LANGUAGE.get(lang_code, DISCLAIMER_BY_LANGUAGE["en"])

    print("\n========== RESPONSE AGENT ==========")
    print("Detected language:", state.get("detected_language"))
    print("===================================\n")

    if state.get("route_to_fallback"):
        text = call_llm(
            prompt=f"User's question: {state['current_query']}",
            system_instruction=_FALLBACK_SYSTEM_INSTRUCTION.format(language=lang_name),
            model=settings.MODEL_FAST,
            temperature=0.3,
        )

        # Fallback responses should always render as a simple chat bubble.
        state["response_mode"] = "plain"

        state["final_response"] = f"{text.strip()}\n\n---\n{disclaimer}"
        return state

    jurisdiction_note = (
        f"The user is in {state['jurisdiction']} — flag if any retrieved law is "
        f"state-specific or if central law applies uniformly."
        if state.get("jurisdiction") else
        "No specific state was mentioned — flag in the response if the relevant law "
        "varies by state, so the user knows to check locally."
    )
    laws = state.get("applicable_laws", [])

    formatted_laws = (
        "\n".join(f"- {law}" for law in laws)
        if laws
        else "None"
    )
    # Decide how the frontend should display this response.
    if (
        state.get("user_intent") == "general_info"
        and not state.get("needs_followup")
    ):
        state["response_mode"] = "plain"

        text = call_llm(
            prompt=(
                f"User's question:\n"
                f"{state['current_query']}\n\n"

                f"Validated legal explanation:\n"
                f"{state.get('legal_analysis', '')}\n\n"

                f"Relevant legal provisions:\n"
                f"{formatted_laws}\n\n"

                "The user is asking to understand a legal concept or law.\n"
                "Do NOT assume they are facing a legal dispute.\n"
                "Explain the concept naturally in simple language.\n"
                "Use short headings and bullet points only where useful.\n"
                "Do NOT generate sections like Summary, Your Rights, "
                "What This Means For Your Situation, Next Steps, or Important Note."
            ),
            system_instruction=_GENERAL_INFO_SYSTEM_INSTRUCTION.format(language=lang_name),
            model=settings.MODEL_FAST,
            temperature=0.3,
        )

    else:
        state["response_mode"] = "structured"

        text = call_llm(
            prompt=(
                f"User's original question: {state['current_query']}\n\n"
                f"Grounded legal analysis (already validated, do not change the substance):\n"
                f"{state.get('legal_analysis', '')}\n\n"
                f"Applicable laws:\n{formatted_laws}\n\n"
                f"Confidence: {state.get('confidence_level')} — {state.get('confidence_reason')}\n\n"
                f"Jurisdiction context: {jurisdiction_note}"
            ),
            system_instruction=_SYSTEM_INSTRUCTION.format(language=lang_name),
            model=settings.MODEL_FAST,
            temperature=0.3,
        )

    confidence_line = f"\n\n_Confidence: {state.get('confidence_level', 'medium').upper()}_"
    sources = _sources_block(state.get("retrieved_chunks", []))

    

    state["final_response"] = (
        f"{text.strip()}"
        f"{sources}"
        f"{confidence_line}\n\n---\n{disclaimer}"
    )

    print("\n========== RESPONSE MODE ==========")
    print(state.get("response_mode"))
    print("==================================")

    return state
