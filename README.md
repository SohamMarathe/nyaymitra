# NyayaMitra (न्यायमित्र)

**Agentic AI legal information platform for Indian citizens.**
*Nyaya = justice, Mitra = friend — legal help that explains, not lectures.*

NyayaMitra is a six-stage LangGraph pipeline that helps people understand
their legal rights and the procedures that apply to them, in their own
language, grounded in official Indian legal sources — and honest about
when it isn't confident enough to answer.

It is **not** a lawyer replacement and does not claim to reduce judicial
backlog. It aims at a narrower, real problem: legal information in India
is scattered, dense, and mostly in English, and that gap causes real
confusion before people ever reach a lawyer.

---

## Why this exists

Ordinary citizens struggle to understand legal issues, identify the
applicable law, and figure out the correct procedure — not because the
law is unknowable, but because it's written for lawyers and locked behind
language and jargon. NyayaMitra doesn't try to solve the justice system;
it tries to make the first step — understanding what's actually going on —
less confusing.

## Architecture

```
User Query
    │
    ▼
Scope & Safety Gate ──(out of scope/unsafe)──► Rejection
    │
    ▼
Intent Agent  ◄── session state (PostgreSQL)
    │
    ├──(needs more info)──► Follow-up Agent ──► (waits for reply)
    │
    ▼
Retrieval Agent ── searches ONE domain-specific FAISS collection
    │
    ▼
Reasoning & Validation Agent ── grounds answer, self-audits, scores confidence
    │
    ▼
Response Agent ── language, tone, structure, non-negotiable disclaimer
```

Full breakdown: [`docs/architecture.md`](docs/architecture.md)
Why each decision was made: [`docs/design-decisions.md`](docs/design-decisions.md)

## Tech stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph (`StateGraph`, conditional routing) |
| LLM + embeddings | Gemini API (`google-genai` SDK) — `gemini-3.1-flash-lite` / `gemini-3.5-flash` / `gemini-embedding-001` |
| Backend | FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| Vector search | FAISS (per-domain indexes) |
| Frontend | Next.js (App Router), plain CSS |
| PDF parsing | pdfplumber |
| Language detection | langdetect |

All of the above run on the **free tier** — see [`SETUP.md`](SETUP.md) for
API key setup. No paid services required to build or run this locally.

## Languages

English, Hindi, Marathi — the knowledge base stays in English (the authoritative language for Indian
statutes); multilingual support happens at the query and response layer
via cross-lingual embeddings and language-aware generation. See
`docs/design-decisions.md` for why this is more scalable than maintaining
a translated knowledge base per language.

## Domains covered

Consumer, Labour, and Cyber are the Phase 0-2 domains (clearest citizen
value, clearest procedures). Property, Family, and Criminal are structured
identically and can be added by following the same knowledge-base pattern
— see `knowledge_base_raw/README.md`.

## What makes this different from a typical RAG chatbot

1. **Self-auditing reasoning.** The Reasoning & Validation Agent drafts an
   answer, then explicitly checks its own draft against the retrieved
   sources and strips out anything not actually supported — the most
   common failure mode in legal-information tools is a confidently wrong
   answer, and this is the architectural attempt to catch that before the
   user sees it.
2. **Confidence that routes, not just displays.** Low confidence doesn't
   just show a badge — it changes what response the user gets, routing to
   an honest "here's who to actually contact" answer instead of a guess.
3. **Domain-scoped retrieval.** Six FAISS collections, not one. The
   Retrieval Agent never searches the whole knowledge base — only the
   collection matching the identified domain.
4. **Multilingual by architecture, not bolted on.** One knowledge base,
   cross-lingual embeddings, and a Response Agent that generates natively
   in the target language rather than translating a pre-written English
   answer.
5. **A scope gate that says no.** Most student RAG projects assume every
   input is a valid, answerable question. This one explicitly checks
   before doing anything else.

## Project structure

```
nyayamitra/
├── backend/
│   ├── agents/        → the six agents + shared LLM client
│   ├── graph/          → LangGraph state schema + workflow wiring
│   ├── api/routes/       → FastAPI endpoints
│   ├── db/                → SQLAlchemy models
│   ├── knowledge_base/      → ingestion pipeline + retriever
│   ├── utils/                 → language detection, disclaimer, formatting
│   └── scripts/                 → standalone test scripts
├── frontend/          → Next.js chat UI
├── knowledge_base_raw/  → where you put manually-downloaded source documents
├── indexes/               → generated FAISS indexes (gitignored, rebuild locally)
└── docs/                    → architecture + design rationale
```

## Setup

Full step-by-step instructions: **[`SETUP.md`](SETUP.md)**. Short version:

```bash
pip install -r requirements.txt
cp .env.example .env              # add your free Gemini API key
docker compose up -d               # starts PostgreSQL
# download Consumer domain documents into knowledge_base_raw/consumer/ (see its README)
python -m backend.knowledge_base.ingestion.run_ingestion --domain consumer
python -m backend.scripts.test_retrieval consumer "how do I file a complaint"
uvicorn backend.main:app --reload --port 8000
# in a second terminal:
cd frontend && npm install && npm run dev
```

## Roadmap

- [x] Architecture design and agent responsibilities finalized
- [x] LangGraph pipeline, FastAPI backend, PostgreSQL persistence
- [x] Ingestion pipeline (loader → section-aware chunker → embedder)
- [x] Next.js chat frontend with structured response cards
- [ ] Consumer domain knowledge base populated and retrieval-tested
- [ ] Labour + Cyber domains added
- [ ] Hindi + Marathi verified end-to-end
- [ ] Remaining five languages added
- [ ] Evaluation set (100+ known questions) run against the system
- [ ] Property, Family, Criminal domains

## Limitations & ethical notes

- This is legal **information**, never legal advice — enforced both by a
  standing disclaimer on every response and by wording rules in the
  Response Agent's prompt (never "you should," always "the law provides").
- Not a substitute for a lawyer. Every response points toward free legal
  aid (District Legal Services Authority) or a registered advocate.
- Knowledge base accuracy depends entirely on what's ingested and how
  current it is — laws get amended; see the BNS/BNSS/BSA note in
  `knowledge_base_raw/README.md` for a real example of exactly this kind
  of change.
- Not deployed publicly. This is a local, portfolio-and-learning project;
  it has not undergone the legal, security, or scale review that a public
  legal-information service serving real citizens would require.

## License

MIT — see `LICENSE`.
