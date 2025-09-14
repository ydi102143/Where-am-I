from __future__ import annotations
from datetime import datetime, date
from math import log
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models as m
from app.services.coach import coach_line_for_task

def _proximity(due: date | None, today: date) -> float:
    if due is None:
        return 0.0
    days_left = (due - today).days
    if days_left < 0: return 2.0
    if days_left == 0: return 1.8
    if days_left <= 3: return 1.5
    if days_left <= 7: return 1.0
    if days_left <= 14: return 0.6
    return 0.3

def _score(impact: int, effort_min: int, due: date | None, today: date) -> float:
    w_deadline = 1.0; w_impact = 1.2; w_effort = 0.6
    return (w_deadline * _proximity(due, today) + w_impact * max(1, impact) - w_effort * log(1 + max(1, effort_min)))

def _coach_line(title: str, effort_min: int) -> str:
    return coach_line_for_task(title, effort_min)

def pick_today_tasks(db: Session, user: m.User, minutes_available: int = 90, today: date | None = None) -> List[Tuple[m.Task, float]]:
    if today is None:
        today = datetime.now().date()
    stmt = select(m.Task).join(m.Goal, m.Task.goal_id == m.Goal.id).where(m.Goal.user_id == user.id).where(m.Task.status != "done")
    tasks = db.execute(stmt).scalars().all()
    scored: List[Tuple[m.Task, float]] = []
    for t in tasks:
        s = _score(t.impact or 1, t.effort_min or 30, t.due, today)
        scored.append((t, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    picked: List[Tuple[m.Task, float]] = []
    remain = max(1, minutes_available)
    for t, s in scored:
        e = t.effort_min if (t.effort_min and t.effort_min > 0) else 30
        if e <= remain or not picked:
            picked.append((t, s)); remain -= e
        if len(picked) >= 3:
            break
    return picked

def get_or_create_demo_user(db: Session) -> m.User:
    user = db.execute(select(m.User).where(m.User.email == "demo@example.com")).scalar_one_or_none()
    if user: return user
    user = m.User(name="Demo", email="demo@example.com"); db.add(user); db.commit(); db.refresh(user); return user
