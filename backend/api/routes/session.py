from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from backend.db.database import get_db
from backend.db import models

router = APIRouter()


class SessionResponse(BaseModel):
    session_id: str


class MessageOut(BaseModel):
    role: str
    content: str
    language: str
    confidence_level: str | None = None


@router.post("/session", response_model=SessionResponse)
def create_session(db: DBSession = Depends(get_db)):
    db_session = models.Session(agent_state_json={})
    db.add(db_session)
    db.commit()
    return SessionResponse(session_id=db_session.id)


@router.get("/session/{session_id}/history", response_model=list[MessageOut])
def get_history(session_id: str, db: DBSession = Depends(get_db)):
    db_session = db.get(models.Session, session_id)
    if not db_session:
        raise HTTPException(404, "session not found")
    messages = (
        db.query(models.Message)
        .filter(models.Message.session_id == session_id)
        .order_by(models.Message.created_at.asc())
        .all()
    )
    return [
        MessageOut(role=m.role, content=m.content, language=m.language, confidence_level=m.confidence_level)
        for m in messages
    ]
