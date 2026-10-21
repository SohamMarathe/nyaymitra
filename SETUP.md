# Setup — Do These In Order

Do not skip ahead. Each step assumes the previous one works. If something
fails, fix it before moving to the next step — debugging three new things
at once is much harder than debugging one.

## 0. Prerequisites

- **Python 3.11 or 3.12** — https://www.python.org/downloads/ (on Windows,
  tick "Add Python to PATH" during install, or the `python3` command won't
  be found later)
- **Node.js 18+** — https://nodejs.org (only needed once you get to the
  frontend, step 7 — you can install this later, not right now)
- **Docker Desktop** — https://www.docker.com/products/docker-desktop
  (for PostgreSQL) — **or skip it entirely**, see step 3.5 below

Check what you already have installed:
```bash
python3 --version
node --version
docker --version
```
If a command isn't found, install that one thing before moving on.

## 1. Get your free Gemini API key

1. Go to https://aistudio.google.com/apikey
2. Sign in, click "Create API key"
3. Copy it — you won't need to enable billing. **Do not enable billing on
   the associated Google Cloud project if you want to stay on the free
   tier** — enabling billing switches a project off the free tier
   entirely, even if you don't spend anything.
4. Free-tier limits change occasionally without much notice — if you hit
   429 (rate limit) errors during testing, wait a minute and retry; the
   code already retries automatically with backoff.

## 2. Python environment

```bash
cd nyayamitra
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and paste your Gemini API key into `GEMINI_API_KEY`. Leave
everything else as default for now.

**Test the key works before doing anything else:**

```bash
python -m backend.scripts.test_gemini_connection
```

You should see two green checkmarks in a few seconds. If this fails, fix
it now — everything downstream depends on this one thing working.

## 3.5. Want to skip Docker entirely? (optional, simpler)

The project defaults to PostgreSQL via Docker because it's a more common
resume keyword. But if Docker feels like a hassle on your machine, you can
skip it completely — open `.env` and change one line:

```
DATABASE_URL=sqlite:///./nyayamitra.db
```

Nothing else needs to change. SQLite is a single file, needs no service to
start, and the code already works with either — this project's database
layer doesn't use anything Postgres-specific. If you do this, skip step 4
below entirely. You can always switch back to Postgres later if you want
that on your resume before pushing to GitHub.

## 4. Start PostgreSQL

```bash
docker compose up -d
```

Verify it's running: `docker ps` should show `nyayamitra-postgres` as
healthy. The database tables themselves are created automatically the
first time you start the backend (step 6) — no manual migration needed.

## 5. Build the Consumer knowledge base (start with ONE domain)

1. Read `knowledge_base_raw/README.md` and `knowledge_base_raw/consumer/README.md`
2. Download the Consumer Protection Act 2019 PDF (and the other listed
   documents) into `knowledge_base_raw/consumer/acts/`, following the
   filename convention in the README exactly
3. Write 2-3 procedure `.txt` files and a handful of judgment/FAQ `.txt`
   files as described there
4. Run ingestion:

```bash
python -m backend.knowledge_base.ingestion.run_ingestion --domain consumer
```

You should see log lines like `Domain 'consumer': 40 total chunks from 6
documents` and `Wrote consumer.index (40 vectors, dim=768)`.

5. **Test retrieval before doing anything else:**

```bash
python -m backend.scripts.test_retrieval consumer "how do I file a complaint about a defective product"
```

Read the results. If the top 2-3 chunks are actually about filing consumer
complaints, you're good. If they're irrelevant, your chunking or source
documents need work — fix this now, not after you've built the agents on
top of it. This single step catches the most common and most silent
failure mode in RAG projects.

## 6. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000/docs — you'll see interactive API documentation.
Try `POST /query` directly from that page with a body like:

```json
{ "message": "how do I file a consumer complaint", "session_id": null, "language": null }
```

If you get a well-formed response with `sections` and a `confidence`
field, the entire agent pipeline is working end to end — before you've
written a single line of frontend code. This is deliberate: debug the
backend through `/docs` first, so when something looks wrong later you
know immediately whether the bug is in the agents or in the frontend.

## 7. Start the frontend

In a **new terminal** (keep uvicorn running in the first one):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Send a message. It should hit your running
backend and render a structured response card.

## 8. Expand from here

Once steps 1-7 work with the Consumer domain in English, follow the
phased roadmap in the main `README.md`: add Labour and Cyber, add Hindi
and Marathi, then the remaining languages, then the quality/eval pass.
Re-run `test_retrieval.py` for every new domain before trusting it inside
the full pipeline — this habit is worth keeping through every phase, not
just Phase 0.

## Common issues

| Symptom | Likely cause |
|---|---|
| `GEMINI_API_KEY is not set` | `.env` wasn't created from `.env.example`, or key wasn't pasted in |
| `No index found for domain 'consumer'` | Ingestion wasn't run yet, or ran but found 0 documents — check `knowledge_base_raw/consumer/` actually has files in it |
| 429 errors from Gemini | Free-tier rate limit — the code retries automatically; if it persists, you're sending requests faster than the tier allows, slow down testing |
| `psycopg.OperationalError` / can't connect to DB | Docker container isn't running — `docker compose up -d`, then `docker ps` to confirm |
| Frontend shows "Couldn't reach NyayaMitra's backend" | uvicorn isn't running, or is running on a different port than `NEXT_PUBLIC_API_URL` expects (default `http://localhost:8000`) |
