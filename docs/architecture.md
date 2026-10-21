# Architecture

## Pipeline

```
User Query
    │
    ▼
┌─────────────────────┐
│ Scope & Safety Gate  │── out of scope / unsafe ──► polite rejection ──► END
└──────────┬───────────┘
           │ in scope
           ▼
┌─────────────────────┐   ◄── session state persisted in PostgreSQL
│    Intent Agent       │       (domain, jurisdiction, collected facts)
└──────────┬───────────┘
           │
   ┌───────┴────────┐
   │ needs follow-up? │
   └───┬─────────┬────┘
      yes         no
       │           │
       ▼           │
┌──────────────┐    │
│ Follow-up     │    │
│ Agent          │    │
└──────┬───────┘    │
       │ (ends turn, waits for user's reply) │
       └── END       │
                    ▼
           ┌──────────────────┐
           │ Retrieval Agent    │── searches ONE domain-specific FAISS collection
           └─────────┬──────────┘
                     ▼
           ┌──────────────────────┐
           │ Reasoning &            │── draft → self-audit against sources → confidence
           │ Validation Agent        │
           └─────────┬──────────────┘
                     ▼
           ┌──────────────────┐
           │ Response Agent     │── language + tone + structure + disclaimer
           └─────────┬──────────┘
                     ▼
                    END
```

Full node/edge wiring: `backend/graph/workflow.py`.
Full state schema: `backend/graph/state.py`.

## Knowledge base layout (per domain)

```
consumer/
├── acts/          → statutes, chunked by Section
├── procedures/     → step-by-step guides, chunked by paragraph
├── judgments/       → landmark case excerpts, chunked by paragraph
└── faqs/             → plain-language Q&A, chunked by paragraph
        │
        ▼
  ingestion pipeline (loader → chunker → embedder)
        │
        ▼
  indexes/consumer.index + indexes/consumer_metadata.json
```

One FAISS index per domain. The Retrieval Agent only ever opens the index
matching the domain the Intent Agent identified — never a combined,
whole-knowledge-base index.

## Request lifecycle (one HTTP call)

1. `POST /query` receives `{session_id?, message, language?}`
2. Load the session's persisted state (or create a new session)
3. Detect language (or use the explicit UI selection)
4. Build the LangGraph state, invoke the compiled graph
5. Save both the user message and the assistant response to `messages`
6. Persist the small slice of state that needs to survive to the next turn
7. Return the response text, split into structured sections, plus confidence

See `backend/api/routes/query.py` for the exact implementation.

## Why this shape

See `docs/design-decisions.md` for the reasoning behind each choice —
this file is deliberately just the "what," not the "why."
