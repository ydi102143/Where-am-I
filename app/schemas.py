from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ORMModel(BaseModel):
    model_config = {"from_attributes": True}

# Goal
class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    why: str = ""
    kgi: str = ""
    deadline: Optional[date] = None
    area: str = "general"

class GoalUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    why: Optional[str] = None
    kgi: Optional[str] = None
    deadline: Optional[date] = None
    area: Optional[str] = None

class GoalOut(ORMModel):
    id: int
    user_id: int
    title: str
    why: str
    kgi: str
    deadline: Optional[date] | None
    area: str
    created_at: datetime

# Task
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    status: str = Field(default="pending", pattern="^(pending|doing|done)$")
    impact: int = Field(default=1, ge=1, le=5)
    effort_min: int = Field(default=30, ge=1, le=600)
    due: Optional[date] = None
    parent_task_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    status: Optional[str] = Field(default=None, pattern="^(pending|doing|done)$")
    impact: Optional[int] = Field(default=None, ge=1, le=5)
    effort_min: Optional[int] = Field(default=None, ge=1, le=600)
    due: Optional[date] = None
    parent_task_id: Optional[int] = None

class TaskOut(ORMModel):
    id: int
    goal_id: int
    title: str
    status: str
    impact: int
    effort_min: int
    due: Optional[date] | None
    parent_task_id: Optional[int] | None

# Plan item (today)
class PlanItem(BaseModel):
    task_id: int
    goal_id: int
    title: str
    status: str
    impact: int
    effort_min: int
    due: Optional[date] = None
    score: float
    coach_line: str

# Reflection
class ReflectionCreate(BaseModel):
    date: Optional[date] = None
    text: str = Field(default="", max_length=4000)
    mood: int = Field(default=3, ge=1, le=5)

class ReflectionOut(ORMModel):
    id: int
    user_id: int
    date: date
    text: str
    mood: int
    created_at: datetime

class ReflectionSummary(BaseModel):
    days: int
    count: int
    avg_mood: float | None
    latest_text: str | None
    latest_date: Optional[date] = None

# WBS
class WbsTask(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    effort_min: int = Field(ge=5, le=600)
    impact: int = Field(ge=1, le=5)
    due: Optional[date] = None
    prereq_ids: List[int] = []

class WbsPlanRequest(BaseModel):
    minutes_per_day: int = Field(default=90, ge=15, le=600)
    max_tasks: int = Field(default=12, ge=3, le=50)
    spread_until_deadline: bool = True
    dry_run: bool = False

class WbsPlanResult(BaseModel):
    goal_id: int
    created_count: int
    items: List[WbsTask]
    saved: bool

# Integration (ICS)
class IntegrationSet(BaseModel):
    kind: str = Field(pattern="^(gcal_ics)$")
    value: str = Field(min_length=8)

class IntegrationOut(ORMModel):
    id: int
    user_id: int
    kind: str
    key: str
    value: str
