"""
Splits the Response Agent's emoji-headed text into a structured dict so the
frontend can render a proper card (ResponseCard.tsx) instead of a wall of
markdown. Splitting on the emoji markers is intentional and matches exactly
what response_agent.py's system prompt requires it to produce.
"""
import re

_SECTION_MARKERS = ["🔍", "⚖️", "📋", "✅", "📌", "📚"]


def split_response_sections(text: str) -> dict:
    """Returns {"summary": ..., "law": ..., "situation": ..., "next_steps": ...,
    "note": ..., "sources": ..., "confidence_line": ..., "disclaimer": ...}
    Any section not present in the text is an empty string."""
    disclaimer = ""
    body = text
    if "\n---\n" in text:
        body, disclaimer = text.rsplit("\n---\n", 1)

    confidence_line = ""
    conf_match = re.search(r"_Confidence:.*_", body)
    if conf_match:
        confidence_line = conf_match.group(0)
        body = body.replace(confidence_line, "").strip()

    pattern = "|".join(re.escape(m) for m in _SECTION_MARKERS)
    pieces = re.split(f"({pattern})", body)

    sections = {"summary": "", "law": "", "situation": "", "next_steps": "", "note": "", "sources": ""}
    key_by_marker = {
        "🔍": "summary", "⚖️": "law", "📋": "situation",
        "✅": "next_steps", "📌": "note", "📚": "sources",
    }

    current_key = None
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        if piece in key_by_marker:
            current_key = key_by_marker[piece]
            continue
        if current_key:
            # Drop the header word (e.g. "SUMMARY") that follows the emoji, keep the rest.
            cleaned = re.sub(r"^[A-Z /]+\n?", "", piece, count=1).strip()
            sections[current_key] = cleaned

    return {
        **sections,
        "confidence_line": confidence_line.strip("_"),
        "disclaimer": disclaimer.strip(),
        "raw": text,
    }
