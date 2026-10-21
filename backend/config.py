"""
Central configuration for NyayaMitra.
Everything that can change between machines/environments lives here,
loaded from environment variables (see .env.example at the repo root).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # ── Gemini API ───────────────────────────────────────────────
    # Get this free at https://aistudio.google.com/apikey
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Model tiering: cheaper/faster model for simple classification steps,
    # stronger model for the steps that actually need reasoning quality.
    # Both are current (July 2026) Flash-tier models on the Gemini free tier.
    # Gemini 2.0 Flash / 2.0 Flash-Lite are DEPRECATED (shut down 1 Jun 2026) — do not use.
    MODEL_FAST: str = os.getenv("MODEL_FAST", "gemini-3.1-flash-lite")   # scope gate, intent, follow-up
    MODEL_REASONING: str = os.getenv("MODEL_REASONING", "gemini-3.1-flash-lite")  # reasoning/validation, response

    # text-embedding-004 was shut down 14 Jan 2026. Current model is gemini-embedding-001.
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
    # 768 keeps the FAISS index small and fast on modest hardware.
    # Google recommends 768 / 1536 / 3072 only (Matryoshka-trained model).
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "768"))

    # ── Paths ────────────────────────────────────────────────────
    RAW_KB_DIR: Path = BASE_DIR / "knowledge_base_raw"
    INDEX_DIR: Path = BASE_DIR / "indexes"

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://nyayamitra:nyayamitra@localhost:5432/nyayamitra",
    )

    # ── Retrieval ────────────────────────────────────────────────
    TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "6"))
    RETRIEVAL_DISTANCE_THRESHOLD: float = float(
    os.getenv("RETRIEVAL_DISTANCE_THRESHOLD", "0.9"))
    VALID_DOMAINS = ["consumer", "labour", "cyber", "property", "family", "criminal"]

    # ── Confidence routing ──────────────────────────────────────
    # Distance threshold below which retrieval is considered "strong enough".
    # FAISS IndexFlatL2 returns squared L2 distance — lower is more similar.
    # Tune this after Phase 0 evaluation against your own KB (see docs/architecture.md).
    RETRIEVAL_DISTANCE_GOOD: float = float(os.getenv("RETRIEVAL_DISTANCE_GOOD", "0.9"))

    # ── App ──────────────────────────────────────────────────────
    APP_ENV: str = os.getenv("APP_ENV", "development")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    SUPPORTED_LANGUAGES = {
        "en": "English", "hi": "Hindi", "mr": "Marathi", "bn": "Bengali",
        "ta": "Tamil", "te": "Telugu", "gu": "Gujarati", "kn": "Kannada",
    }


settings = Settings()


def require_api_key() -> None:
    """Fail loudly and early if the API key is missing, instead of a confusing
    error three layers deep inside an agent call."""
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your "
            "free key from https://aistudio.google.com/apikey"
        )
