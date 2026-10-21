"""
POST /query — the one endpoint that matters most. Loads any persisted state
for the session, runs the graph, saves the turn, and persists the small
slice of state that needs to survive to the next turn.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from backend.db.database import get_db
from backend.db import models
from backend.graph.state import new_state, PERSISTED_FIELDS
from backend.graph.workflow import graph
from backend.utils.language_detector import detect_language
from backend.utils.response_formatter import split_response_sections

logger = logging.getLogger("nyayamitra.api")
router = APIRouter()


class QueryRequest(BaseModel):
    session_id: str | None = None
    message: str
    language: str | None = None  # explicit UI selection, takes priority over detection


class QueryResponse(BaseModel):
    session_id: str
    message_id: str
    response_text: str
    sections: dict
    confidence: str | None = None
    awaiting_reply: bool = False
    response_mode: str = "structured"


@router.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest, db: DBSession = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(400, "message cannot be empty")

    # ── Load or create session ──────────────────────────────────
    if req.session_id:
        db_session = db.get(models.Session, req.session_id)
        if not db_session:
            raise HTTPException(404, "session not found")
    else:
        db_session = models.Session(agent_state_json={})
        db.add(db_session)
        db.flush()  # assigns db_session.id without committing yet

    persisted = db_session.agent_state_json or {}

    # ── Build this turn's state, merging in whatever persisted from before ──
    state = new_state(session_id=db_session.id, query=req.message)
    for field in PERSISTED_FIELDS:
        if field in persisted:
            state[field] = persisted[field]

    state["detected_language"] = detect_language(req.message, ui_selected=req.language)

    # Recent history, for agents that benefit from seeing the last couple of turns.
    recent = (
        db.query(models.Message)
        .filter(models.Message.session_id == db_session.id)
        .order_by(models.Message.created_at.desc())
        .limit(6)
        .all()
    )
    state["messages"] = [
        {"role": m.role, "content": m.content, "language": m.language} for m in reversed(recent)
    ]

    # ── Run the graph ────────────────────────────────────────────
    try:
        result = graph.invoke(state)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Graph execution failed")
        raise HTTPException(500, f"Something went wrong processing your question: {exc}") from exc

    response_text = result.get("final_response") or "I wasn't able to generate a response — please try rephrasing."
    print("\n========== FINAL RESPONSE ==========")
    print(response_text)

    print("\n========== GRAPH RESULT ==========")
    print(result)

    # ── Save the turn ────────────────────────────────────────────
    user_msg = models.Message(
        session_id=db_session.id, role="user", content=req.message,
        language=state["detected_language"],
    )
    assistant_msg = models.Message(
        session_id=db_session.id, role="assistant", content=response_text,
        language=state["detected_language"], confidence_level=result.get("confidence_level"),
    )
    db.add_all([user_msg, assistant_msg])

    # ── Persist the slice of state that needs to survive to next turn ──
    db_session.agent_state_json = {field: result.get(field) for field in PERSISTED_FIELDS}
    db.add(db_session)
    db.commit()

    print(result.keys())
    print(result.get("response_mode"))

    return QueryResponse(
        session_id=db_session.id,
        message_id=assistant_msg.id,
        response_text=response_text,
        sections=split_response_sections(response_text),
        confidence=result.get("confidence_level"),
        awaiting_reply=bool(result.get("awaiting_user_reply")),
        response_mode=result.get("response_mode", "structured"),
    )
