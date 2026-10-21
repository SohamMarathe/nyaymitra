"""
Entry point. Run with:
    uvicorn backend.main:app --reload --port 8000

Then open http://localhost:8000/docs for interactive API docs (FastAPI
generates this automatically — genuinely useful for testing agents one
query at a time before the frontend is even running).
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db.database import init_db
from backend.api.routes import query, session, feedback

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="NyayaMitra API",
    description="Agentic legal information platform for Indian citizens.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, tags=["query"])
app.include_router(session.router, tags=["session"])
app.include_router(feedback.router, tags=["feedback"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.APP_ENV}
