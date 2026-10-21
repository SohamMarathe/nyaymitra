"""
Run this FIRST — before downloading any legal documents, before touching
the database. It only checks one thing: does your API key actually work?

Usage:
    python -m backend.scripts.test_gemini_connection

Takes about 5 seconds and costs a tiny fraction of your free-tier quota.
If this fails, nothing else in the project will work, so it's worth
confirming here rather than debugging it three layers deep inside an agent.
"""
from backend.agents.llm_client import call_llm, embed_text


def main() -> None:
    print("Testing text generation...")
    try:
        reply = call_llm(
            prompt="Reply with exactly: Connection successful",
            system_instruction="You are a test assistant. Follow the instruction exactly.",
        )
        print(f"  Model replied: {reply.strip()}")
        print("  ✅ Text generation works.\n")
    except Exception as exc:  # noqa: BLE001
        print(f"  ❌ Text generation failed: {exc}")
        print("  Check: is GEMINI_API_KEY set correctly in your .env file?")
        return

    print("Testing embeddings...")
    try:
        vector = embed_text("test sentence")
        print(f"  Got a vector of length {len(vector)}.")
        print("  ✅ Embeddings work.\n")
    except Exception as exc:  # noqa: BLE001
        print(f"  ❌ Embeddings failed: {exc}")
        return

    print("Everything works. You're ready to move on to the knowledge base.")


if __name__ == "__main__":
    main()
