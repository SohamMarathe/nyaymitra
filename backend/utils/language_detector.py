"""
Detects which of the 8 supported languages a query is in.
Falls back to English on short/ambiguous input rather than guessing wildly —
single-word queries like "help" are not reliably detectable, and the
frontend's manual language selector (see LanguageSelector.tsx) is the
proper fallback for those, not this heuristic.
"""
from langdetect import detect, LangDetectException, DetectorFactory

from backend.config import settings

# Make detection deterministic across runs (langdetect is seeded randomly by default).
DetectorFactory.seed = 0

_MIN_CHARS_FOR_DETECTION = 4


def detect_language(text: str, ui_selected: str | None = None) -> str:
    """
    ui_selected takes priority if the user explicitly picked a language in
    the UI — never override an explicit human choice with a guess.
    """
    if ui_selected and ui_selected in settings.SUPPORTED_LANGUAGES:
        return ui_selected

    cleaned = text.strip()
    if len(cleaned) < _MIN_CHARS_FOR_DETECTION:
        return "en"

    try:
        code = detect(cleaned)
    except LangDetectException:
        return "en"

    return code if code in settings.SUPPORTED_LANGUAGES else "en"
