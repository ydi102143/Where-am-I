from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.schemas import PlanItem
from app.services.plan import pick_today_tasks, _coach_line, get_or_create_demo_user
from app.services.calendar import free_minutes_between
from app import models as m

router = APIRouter(prefix="/v1", tags=["v1"])

@router.get("/plan/today", response_model=List[PlanItem])
def plan_today(
    minutes_available: int = Query(90, ge=15, le=600),
    now_iso: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    now = datetime.fromisoformat(now_iso) if now_iso else datetime.now()
    user = get_or_create_demo_user(db)
    picked = pick_today_tasks(db, user, minutes_available=minutes_available, today=now.date())
    items: List[PlanItem] = []
    for t, score in picked:
        items.append(PlanItem(
            task_id=t.id, goal_id=t.goal_id, title=t.title, status=t.status,
            impact=t.impact, effort_min=t.effort_min, due=t.due,
            score=round(score, 3), coach_line=_coach_line(t.title, t.effort_min or 30),
        ))
    return items

@router.get("/plan/available_minutes")
def plan_available_minutes(
    date_str: str | None = Query(default=None, description="YYYY-MM-DD"),
    work_start: str = Query(default="07:00"),
    work_end: str = Query(default="23:00"),
    db: Session = Depends(get_db),
):
    user = get_or_create_demo_user(db)
    row = db.execute(
        select(m.Integration).where(
            m.Integration.user_id == user.id,
            m.Integration.kind == "gcal_ics",
            m.Integration.key == "default",
        )
    ).scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="ICS not configured")
    target = datetime.now().date()
    if date_str:
        target = datetime.fromisoformat(date_str).date()
    minutes = free_minutes_between(row.value, target, work_start, work_end)
    return {"date": str(target), "work_start": work_start, "work_end": work_end, "available_minutes": minutes}
