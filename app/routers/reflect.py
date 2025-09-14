from __future__ import annotations
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app import models as m
from app.schemas import ReflectionCreate, ReflectionOut, ReflectionSummary
from app.services.plan import get_or_create_demo_user

router = APIRouter(prefix="/v1", tags=["v1"])

@router.post("/reflect", response_model=ReflectionOut)
def create_reflection(payload: ReflectionCreate, db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    d = payload.date or datetime.now().date()
    ref = m.Reflection(user_id=user.id, date=d, text=payload.text or "", mood=payload.mood or 3)
    db.add(ref); db.commit(); db.refresh(ref)
    return ref

@router.get("/reflect/recent", response_model=ReflectionSummary)
def recent_reflection_summary(days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    today = datetime.now().date()
    start = today - timedelta(days=days-1)
    stmt = select(m.Reflection).where(m.Reflection.user_id == user.id).where(m.Reflection.date >= start).order_by(m.Reflection.date.desc(), m.Reflection.id.desc())
    items = db.execute(stmt).scalars().all()
    if not items:
        return ReflectionSummary(days=days, count=0, avg_mood=None, latest_text=None, latest_date=None)
    avg_mood = sum(it.mood for it in items) / len(items)
    latest = items[0]
    return ReflectionSummary(days=days, count=len(items), avg_mood=round(avg_mood,2), latest_text=(latest.text[:240] if latest.text else None), latest_date=latest.date)
