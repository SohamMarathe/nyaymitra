from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from backend.db.database import get_db
from backend.db import models
from typing import Literal

router = APIRouter()


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    rating: Literal["up", "down"]
    comment: str | None = None


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, db: DBSession = Depends(get_db)):
    

    feedback = models.Feedback(
        session_id=req.session_id,
        message_id=req.message_id,
        rating=req.rating,
        comment=req.comment,
    )
    db.add(feedback)
    db.commit()
    return {"status": "recorded"}
