from __future__ import annotations
from datetime import datetime, timedelta, date as date_type
import json
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models as m
from app.services.plan import get_or_create_demo_user
from app.services.coach import summarize_reflections

JST_OFFSET = 9

def jst_today() -> date_type:
    now_utc = datetime.utcnow()
    jst = now_utc + timedelta(hours=JST_OFFSET)
    return jst.date()

def generate_weekly_payload(db: Session, days: int = 7) -> Dict[str, Any]:
    user = get_or_create_demo_user(db)
    today = jst_today()
    start = today - timedelta(days=days-1)
    stmt = select(m.Reflection).where(m.Reflection.user_id == user.id).where(m.Reflection.date >= start).order_by(m.Reflection.date.desc(), m.Reflection.id.desc())
    recs = db.execute(stmt).scalars().all()
    items = [{"date": r.date.isoformat(), "text": r.text or "", "mood": r.mood or 3} for r in recs]
    res = summarize_reflections(items, days=days)
    payload = {"range": {"days": days, "start": start.isoformat(), "end": today.isoformat()}, "count": len(items), "summary": res["summary"], "improvements": res["improvements"], "generated_at": today.isoformat()}
    return payload

def save_weekly_suggestion(db: Session, payload: Dict[str, Any]) -> m.Suggestion:
    user = get_or_create_demo_user(db)
    today = jst_today()
    sug = m.Suggestion(user_id=user.id, date=today, type="weekly", content_json=json.dumps(payload, ensure_ascii=False))
    db.add(sug); db.commit(); db.refresh(sug)
    return sug

def upsert_this_week(db: Session) -> m.Suggestion:
    user = get_or_create_demo_user(db)
    today = jst_today()
    dow = today.weekday()  # Mon=0
    sun_shift = (dow + 1) % 7
    week_start = today - timedelta(days=sun_shift)
    week_end = week_start + timedelta(days=6)
    stmt = select(m.Suggestion).where(m.Suggestion.user_id == user.id).where(m.Suggestion.type == "weekly").where(m.Suggestion.date >= week_start).where(m.Suggestion.date <= week_end).order_by(m.Suggestion.id.desc())
    existing = db.execute(stmt).scalars().first()
    payload = generate_weekly_payload(db, days=7)
    if existing:
        existing.date = today
        existing.content_json = json.dumps(payload, ensure_ascii=False)
        db.add(existing); db.commit(); db.refresh(existing)
        return existing
    else:
        return save_weekly_suggestion(db, payload)
