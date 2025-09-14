from __future__ import annotations
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app import models as m
from app.services.plan import get_or_create_demo_user
from app.services.coach import summarize_reflections

router = APIRouter(prefix="/v1", tags=["v1"])

@router.get("/reflect/analyze")
def analyze_recent_reflection(days: int = Query(7, ge=3, le=30), db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    today = datetime.now().date()
    start = today - timedelta(days=days-1)
    stmt = select(m.Reflection).where(m.Reflection.user_id == user.id).where(m.Reflection.date >= start).order_by(m.Reflection.date.desc(), m.Reflection.id.desc())
    recs = db.execute(stmt).scalars().all()
    items = [{"date": r.date.isoformat(), "text": r.text or "", "mood": r.mood or 3} for r in recs]
    res = summarize_reflections(items, days=days)
    return {"days": days, "count": len(items), "summary": res["summary"], "improvements": res["improvements"]}
