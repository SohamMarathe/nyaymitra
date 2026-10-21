"""
Thin shared wrapper around the Gemini API so every agent calls the model
the same way, with the same retry behaviour and the same JSON-parsing safety
net. Uses the current `google-genai` SDK (NOT the deprecated
`google-generativeai` package — if you see old tutorials using
`import google.generativeai as genai`, that package is legacy).
"""
import json
import time
import logging
from typing import Optional, Type, TypeVar
from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.config import settings, require_api_key

from backend.knowledge_base.ingestion.checkpoint import EmbeddingCheckpoint
logger = logging.getLogger("nyayamitra.llm")

_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        require_api_key()
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


T = TypeVar("T", bound=BaseModel)


def call_llm(
    prompt: str,
    system_instruction: str,
    model: str = settings.MODEL_FAST,
    temperature: float = 0.2,
    max_retries: int = 6,
) -> str:
    """Plain text call with exponential backoff on rate-limit (429) errors."""
    client = get_client()
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=2048,
                ),
            )
            return response.text or ""
        except Exception as exc:  # noqa: BLE001 — SDK raises several exception types for 429s
            last_error = exc
            if "PerDay" in str(exc):
                raise RuntimeError(f"Daily free-tier quota used up for this model — waiting won't help until it resets. {exc}") from exc
            wait = min(2 ** attempt * 3, 30)
            logger.warning("LLM call failed (attempt %d/%d): %s. Retrying in %ds",
                            attempt + 1, max_retries, exc, wait)
            time.sleep(wait)
    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")


def call_llm_json(
    prompt: str,
    system_instruction: str,
    schema: Type[T],
    model: str = settings.MODEL_FAST,
    temperature: float = 0.1,
) -> T:
    """
    Call the model and force structured JSON output, parsed straight into a
    Pydantic model. This is what Intent, Scope Gate, and Reasoning use so
    their outputs are never "almost JSON" — they're guaranteed JSON.
    """
    client = get_client()
    json_instruction = (
        f"{system_instruction}\n\n"
        "Respond with ONLY valid JSON matching this exact structure. "
        "No markdown fences, no preamble, no explanation outside the JSON.\n"
        f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
    )
    last_error = None
    for attempt in range(6):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                system_instruction=json_instruction,
                temperature=temperature,
                response_mime_type="application/json",
            ),
            )
            raw = (response.text or "").strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

            print("\n========== RAW LLM RESPONSE ==========")
            print(raw)
            print("======================================\n")

            parsed = json.loads(raw)
            if (
                isinstance(parsed, dict)
                and "properties" in parsed
                and isinstance(parsed["properties"], dict)
            ):
                parsed = parsed["properties"]

            # Compatibility with models that wrap the entire response
            # inside the first field.
            if (
                isinstance(parsed.get("cleaned_explanation"), dict)
                and "confidence_level" in parsed["cleaned_explanation"]
            ):
                parsed = parsed["cleaned_explanation"]

            print("\n========== PARSED JSON ==========")
            print(parsed)
            print("=================================\n")

            return schema.model_validate(parsed)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if "PerDay" in str(exc):
                raise RuntimeError(f"Daily free-tier quota used up for this model — waiting won't help until it resets. {exc}") from exc
            logger.warning("LLM JSON call failed (attempt %d/6) [%s]: %s", attempt + 1,type(exc).__name__, exc)
            time.sleep(min(2 ** attempt * 3, 30))
    raise RuntimeError(f"LLM JSON call failed after 6 attempts: {last_error}")


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """
    Embed a single piece of text with gemini-embedding-001.
    task_type must be RETRIEVAL_DOCUMENT when embedding knowledge-base chunks
    and RETRIEVAL_QUERY when embedding a user's question — using the matching
    type measurably improves retrieval quality for asymmetric search.
    """
    client = get_client()
    for attempt in range(3):
        try:
            result = client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=settings.EMBEDDING_DIM,
                ),
            )
            return list(result.embeddings[0].values)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Embedding call failed (attempt %d/3): %s", attempt + 1, exc)
            time.sleep(2 ** attempt)
    raise RuntimeError("Embedding call failed after 3 attempts")


def embed_batch(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    checkpoint: EmbeddingCheckpoint | None = None,
) -> list[list[float]]:
    """
    Embed many chunks sequentially while respecting Gemini free-tier
    rate limits.
    """

    vectors = []
    completed = 0

    if checkpoint and checkpoint.exists():
        logger.info("Found checkpoint. Resuming previous embedding session...")

        vectors, completed = checkpoint.load()

        logger.info(
            "Loaded %d existing embeddings. Resuming from chunk %d.",
            completed,
            completed + 1,
        )

    REQUESTS_PER_WINDOW = 90
    COOLDOWN_SECONDS = 40
    requests_since_cooldown = 0

    for i in range(completed, len(texts)):
        vectors.append(
            embed_text(
                texts[i],
                task_type=task_type,
            )
        )

        if checkpoint:
            checkpoint.save(vectors)

        requests_since_cooldown += 1

        if requests_since_cooldown >= REQUESTS_PER_WINDOW:
            logger.info(
                "Embedded %d chunks. Cooling down for %d seconds...",
                i + 1,
                COOLDOWN_SECONDS,
            )
            time.sleep(COOLDOWN_SECONDS)
            requests_since_cooldown = 0

    return vectors
