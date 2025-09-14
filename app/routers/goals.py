from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app import models as m
from app.schemas import (
    GoalCreate, GoalUpdate, GoalOut,
    TaskCreate, TaskUpdate, TaskOut,
    WbsPlanRequest, WbsPlanResult, WbsTask
)
from app.services.wbs import generate_wbs, save_wbs_as_tasks

router = APIRouter(prefix="/v1", tags=["v1"])

def get_or_create_demo_user(db: Session) -> m.User:
    user = db.execute(select(m.User).where(m.User.email == "demo@example.com")).scalar_one_or_none()
    if user:
        return user
    user = m.User(name="Demo", email="demo@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/goals", response_model=GoalOut)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)):
    user = get_or_create_demo_user(db)
    goal = m.Goal(
        user_id=user.id, title=payload.title, why=payload.why,
        kgi=payload.kgi, deadline=payload.deadline, area=payload.area,
    )
    db.add(goal); db.commit(); db.refresh(goal)
    return goal

@router.get("/goals", response_model=List[GoalOut])
def list_goals(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    user = get_or_create_demo_user(db)
    stmt = select(m.Goal).where(m.Goal.user_id == user.id).order_by(m.Goal.id.desc())
    if q:
        stmt = stmt.where(m.Goal.title.contains(q))
    return db.execute(stmt.limit(limit).offset(offset)).scalars().all()

@router.get("/goals/{goal_id}", response_model=GoalOut)
def get_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.get(m.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="goal not found")
    return goal

@router.patch("/goals/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: int, payload: GoalUpdate, db: Session = Depends(get_db)):
    goal = db.get(m.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="goal not found")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(goal, k, v)
    db.add(goal); db.commit(); db.refresh(goal)
    return goal

@router.delete("/goals/{goal_id}", status_code=204)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.get(m.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="goal not found")
    db.delete(goal); db.commit()
    return None

# Tasks
@router.post("/goals/{goal_id}/tasks", response_model=TaskOut)
def create_task(goal_id: int, payload: TaskCreate, db: Session = Depends(get_db)):
    goal = db.get(m.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="goal not found")
    task = m.Task(
        goal_id=goal_id, title=payload.title, status=payload.status,
        impact=payload.impact, effort_min=payload.effort_min, due=payload.due,
        parent_task_id=payload.parent_task_id,
    )
    db.add(task); db.commit(); db.refresh(task)
    return task

@router.get("/goals/{goal_id}/tasks", response_model=List[TaskOut])
def list_tasks(goal_id: int, db: Session = Depends(get_db), status: Optional[str] = Query(default=None, pattern="^(pending|doing|done)$")):
    goal = db.get(m.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="goal not found")
    stmt = select(m.Task).where(m.Task.goal_id == goal_id)
    if status:
        stmt = stmt.where(m.Task.status == status)
    return db.execute(stmt.order_by(m.Task.id.desc())).scalars().all()

@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(m.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task

@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(m.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(task, k, v)
    db.add(task); db.commit(); db.refresh(task)
    return task

@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(m.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    db.delete(task); db.commit()
    return None

# WBS: generate plan
@router.post("/goals/{goal_id}/plan", response_model=WbsPlanResult)
def generate_goal_plan(goal_id: int, payload: WbsPlanRequest, db: Session = Depends(get_db)):
    goal = db.get(m.Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="goal not found")
    items: List[WbsTask] = generate_wbs(db, goal, payload)
    created = 0
    saved = False
    if not payload.dry_run:
        created = save_wbs_as_tasks(db, goal, items)
        saved = True
    return WbsPlanResult(goal_id=goal.id, created_count=created, items=items, saved=saved)
