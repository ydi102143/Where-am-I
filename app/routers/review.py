from __future__ import annotations
import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app import models as m
from app.services.plan import get_or_create_demo_user
from app.services.weekly_review import upsert_this_week

router = APIRouter(prefix="/v1", tags=["v1"])

@router.get("/review/weekly")
def get_latest_weekly_review(db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    stmt = select(m.Suggestion).where(m.Suggestion.user_id == user.id).where(m.Suggestion.type == "weekly").order_by(m.Suggestion.id.desc())
    sug = db.execute(stmt).scalars().first()
    if not sug:
        return {"exists": False, "summary": None, "improvements": [], "date": None}
    data = json.loads(sug.content_json or "{}")
    return {
        "exists": True,
        "summary": data.get("summary"),
        "improvements": data.get("improvements", []),
        "date": str(sug.date),
        "range": data.get("range"),
        "count": data.get("count", 0),
    }

@router.post("/review/weekly/run")
def run_weekly_review_now(db: Session = Depends(get_db)):
    sug = upsert_this_week(db)
    data = json.loads(sug.content_json or "{}")
    return {"created": True, "date": str(sug.date), "summary": data.get("summary"), "improvements": data.get("improvements", []), "range": data.get("range"), "count": data.get("count", 0)}
